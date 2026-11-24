"""Remove unknown score-release dependence and isolate selection to earlier data.

This is a retrospective audit, not a fresh independent test. The assessment-free
variant is designated on availability grounds before inspecting its performance.
"""

import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold
from .data import ROOT, split_frames
from .models import classifier, NUM, ENG, ml_metrics
from .decision import allocate, observed_metrics
from .evaluation import coverage_interval

SAFE_NUM = ENG + ["studied_credits", "num_of_prev_attempts"]
ASSESSMENT_COLUMNS = {
    "score_mean",
    "score_min",
    "submitted_count",
    "late_rate",
    "no_early_assessment",
}


def predict(model, frame, features):
    """Score only the explicitly permitted features using an already-fitted model."""
    probabilities = model.predict_proba(frame[features])
    return 1 - probabilities[:, list(model.classes_).index("Success")], probabilities


def actions_for(frame, risk):
    """Apply the fixed classifier-only policy; do not use outcome labels."""
    return allocate(
        risk,
        np.zeros(len(frame)),
        frame.inactive_days,
        frame.code_module,
        route="classifier",
    )[0]


def select_on_training(train, numeric, spec):
    """Never accepts evaluation rows or labels. Refit preprocessing within folds."""
    if set(train.code_presentation) != {"2013B"}:
        raise ValueError("Selection accepts 2013B training records only")
    features = list(numeric) + ["code_module"]
    folds = StratifiedGroupKFold(
        n_splits=spec["folds"], shuffle=True, random_state=spec["seed"]
    )
    partitions = list(folds.split(train, train.target, groups=train.id_student))
    records = []
    for name in spec["candidates"]:
        for fold, (fit_idx, check_idx) in enumerate(partitions):
            fit, check = train.iloc[fit_idx], train.iloc[check_idx]
            if set(fit.id_student) & set(check.id_student):
                raise ValueError("Learner overlap inside training selection")
            model = classifier(name, spec["seed"], numeric).fit(
                fit[features], fit.target
            )
            risk, probabilities = predict(model, check, features)
            records.append(
                {
                    "model": name,
                    "fold": fold,
                    **ml_metrics(check.target, probabilities, model.classes_),
                    **observed_metrics(check.target, actions_for(check, risk)),
                }
            )
    results = pd.DataFrame(records)
    means = results.groupby("model")[["coverage", "adverse_average_precision"]].mean()
    chosen = max(
        spec["candidates"],
        key=lambda name: (
            means.loc[name, "coverage"],
            means.loc[name, "adverse_average_precision"],
            -spec["candidates"].index(name),
        ),
    )
    return chosen, results


def run():
    """Select within 2013B, fit on allowed training rows, then audit exposed 2014B."""
    spec = json.loads((ROOT / "configs/availability_audit.json").read_text())
    frame = pd.read_csv(ROOT / "data/processed/development.csv")
    if set(frame.code_presentation) != {"2013B", "2014B"}:
        raise ValueError("Audit only accepts development periods")
    rows, selection_rows = [], []
    for protocol in ["identity_disjoint", "operational"]:
        train, evaluation = split_frames(frame, protocol)
        for variant, numeric in [
            ("assessment_free", SAFE_NUM),
            ("assessment_assumption", NUM + ENG),
        ]:
            chosen, folds = select_on_training(train, numeric, spec)
            folds["protocol"], folds["variant"] = protocol, variant
            selection_rows.append(folds)
            features = list(numeric) + ["code_module"]
            model = classifier(chosen, spec["seed"], numeric).fit(
                train[features], train.target
            )
            # Selection is complete before evaluation predictions or metrics are calculated.
            risk, probabilities = predict(model, evaluation, features)
            actions = actions_for(evaluation, risk)
            # Outcome-free inactivity comparator, same action capacity and no score inputs.
            baseline_risk = evaluation.inactive_days.to_numpy() / 29
            baseline = actions_for(evaluation, baseline_risk)
            low, high = coverage_interval(evaluation, actions, baseline)
            rows.append(
                {
                    "protocol": protocol,
                    "variant": variant,
                    "selected_model": chosen,
                    "selection_population": "2013B_only",
                    **ml_metrics(evaluation.target, probabilities, model.classes_),
                    **observed_metrics(evaluation.target, actions),
                    "inactivity_coverage": observed_metrics(
                        evaluation.target, baseline
                    )["coverage"],
                    "difference_low": low,
                    "difference_high": high,
                    "scope": "retrospective_2014B_not_independent",
                }
            )
            if variant == "assessment_free":
                joblib.dump(
                    {
                        "model": model,
                        "features": features,
                        "scope": "assessment_free_retrospective_audit",
                    },
                    ROOT / f"outputs/assessment_free_{protocol}.joblib",
                )
    pd.DataFrame(rows).to_csv(ROOT / "outputs/availability_audit.csv", index=False)
    pd.concat(selection_rows).to_csv(
        ROOT / "outputs/availability_selection.csv", index=False
    )
    print(
        "Availability audit complete; selection used earlier training only. No independent-test claim."
    )


if __name__ == "__main__":
    run()
