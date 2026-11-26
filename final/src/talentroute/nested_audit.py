"""Retrospective nested selection diagnostic on 2013B, without final model changes."""

import json
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedGroupKFold
from .data import ROOT
from .availability_audit import SAFE_NUM, select_on_training, predict, actions_for
from .models import classifier, ml_metrics, ENG, numeric_transform
from .decision import observed_metrics, allocate, Policy


def training_cases(frame):
    """Exclude other periods before any split, fitting, selection or scoring."""
    return frame.loc[frame.code_presentation.eq("2013B")].copy()


def outer_partitions(train, seed=247101):
    """Keep every learner within one assessment fold; reject non-training periods."""
    if set(train.code_presentation) != {"2013B"}:
        raise ValueError("Nested audit accepts 2013B only")
    splitter = StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=seed)
    for fit_idx, check_idx in splitter.split(
        train, train.target, groups=train.id_student
    ):
        if set(train.iloc[fit_idx].id_student) & set(train.iloc[check_idx].id_student):
            raise ValueError("Learner overlap in outer folds")
        yield fit_idx, check_idx


def fit_outer_routes(fit, check_inputs, spec):
    """Choose and fit on outer training only; assessment receives feature columns only.

    The anomaly reserve uses the existing 20% review quota. It is an evaluated
    alternative, not a quota chosen from outer-fold performance.
    """
    features = SAFE_NUM + ["code_module"]
    check_inputs = check_inputs[features].copy()
    chosen, selection = select_on_training(fit, SAFE_NUM, spec)
    model = classifier(chosen, spec["seed"], SAFE_NUM).fit(fit[features], fit.target)
    risk, probabilities = predict(model, check_inputs, features)
    detector = Pipeline([
        ("preprocess", numeric_transform()),
        ("model", IsolationForest(n_estimators=150, max_samples=min(512, len(fit)),
                                  random_state=spec["seed"], n_jobs=1)),
    ]).fit(fit[ENG])
    reference = np.sort(-detector.score_samples(fit[ENG]))
    rarity = np.searchsorted(reference, -detector.score_samples(check_inputs[ENG]),
                             side="right") / len(reference)
    routes = {
        "nested_selected_classifier": actions_for(check_inputs, risk),
        "inactivity": actions_for(check_inputs, check_inputs.inactive_days.to_numpy() / 29),
        "nested_anomaly_reserve": allocate(
            risk, rarity, check_inputs.inactive_days, check_inputs.code_module,
            Policy(reserve_fraction=0.2), route="anomaly",
        )[0],
    }
    return chosen, selection, probabilities, model.classes_, routes


def run():
    """Refit selection inside each outer training fold and report every outer fold."""
    spec = json.loads((ROOT / "configs/availability_audit.json").read_text())
    protocol = {
        "scope": "retrospective 2013B nested learner-grouped diagnostic, not independent or temporal confirmation",
        "outer_folds": 3,
        "outer_seed": 247101,
        "inner_spec": spec,
        "features": SAFE_NUM + ["code_module"],
        "comparator": "inactivity_days / 29, identical fixed action policy",
        "rules": [
            "No tuning based on outer results",
            "No 2014B or 2014J scoring",
            "No fitted production model changes",
            "Report all folds and negative results",
            "All records of one learner remain in one fold",
            "Fixed 20% anomaly review reserve; detector refitted on outer training only",
            "Outer outcomes withheld from fitting, selection and action allocation",
        ],
    }
    (ROOT / "outputs/nested_protocol.json").write_text(json.dumps(protocol, indent=2))
    # Read only training rows into the audit; the existing processed file also stores development validation.
    chunks = pd.read_csv(ROOT / "data/processed/development.csv", chunksize=1000)
    train = pd.concat([training_cases(c) for c in chunks], ignore_index=True)
    assert set(train.code_presentation) == {"2013B"}
    features = protocol["features"]
    results = []
    inner = []
    for fold, (fit_idx, test_idx) in enumerate(
        outer_partitions(train, protocol["outer_seed"]), 1
    ):
        fit, test = train.iloc[fit_idx].copy(), train.iloc[test_idx].copy()
        assert not set(fit.id_student) & set(test.id_student)
        # Outcomes are retained solely for scoring after both queues are allocated.
        chosen, selection, prob, classes, routes = fit_outer_routes(
            fit, test[features], spec
        )
        selection["outer_fold"] = fold
        inner.append(selection)
        for name, actions in routes.items():
            results.append(
                {
                    "outer_fold": fold,
                    "method": name,
                    "selected_model": chosen,
                    "train_cases": len(fit),
                    "evaluation_cases": len(test),
                    "evaluation_learners": test.id_student.nunique(),
                    **observed_metrics(test.target, actions),
                    **(
                        ml_metrics(test.target, prob, classes)
                        if name == "nested_selected_classifier"
                        else {}
                    ),
                }
            )
        print("Completed fold", fold, "selected", chosen, flush=True)
    pd.DataFrame(results).to_csv(ROOT / "outputs/nested_results.csv", index=False)
    pd.concat(inner).to_csv(ROOT / "outputs/nested_inner_selection.csv", index=False)


if __name__ == "__main__":
    run()
