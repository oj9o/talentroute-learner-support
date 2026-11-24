"""Retrospective analyses of the assessment-free final system.

The same predeclared policy is used throughout. Previously examined 2014B is
not an independent test. No 2014J features, predictions or outcomes are loaded.
"""

from dataclasses import replace
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score
from .data import ROOT, split_frames
from .availability_audit import SAFE_NUM, predict
from .models import classifier, ml_metrics
from .decision import Policy, allocate, observed_metrics
from .evaluation import frame_actions, coverage_interval, ROUTES
from .analyses import (
    review_route_analysis,
    reconciliation_analysis,
    conditional_value_analysis,
    workload_stress,
)

MODEL = "assessment_free"
SWEEPS = {
    "minutes_per_100": [150, 300, 600, 900],
    "review_minutes": [15, 30, 45, 60],
    "reserve_fraction": [0, 0.1, 0.2, 0.3],
    "risk_threshold": [0, 0.25, 0.5, 0.75],
    "alert_budget_fraction": [0, 0.1, 0.2, 0.4],
}


def load_frame(protocol, seed=7101):
    """Load 2014B cases and score them with the saved assessment-free model."""
    frame = pd.read_csv(ROOT / f"data/processed/predictions_{protocol}_{seed}.csv")
    if set(frame.code_presentation) != {"2014B"}:
        raise ValueError("Final retrospective analyses accept 2014B only")
    bundle = joblib.load(ROOT / f"outputs/assessment_free_{protocol}.joblib")
    frame[MODEL], probabilities = predict(bundle["model"], frame, bundle["features"])
    return frame, bundle, probabilities


def inactivity_actions(frame, policy=Policy(), seed=7101):
    # Shared eligibility permits a fair ranking comparison at a risk cutoff.
    """Rank inactivity alone while matching the final classifier eligibility mask."""
    return allocate(
        frame.inactive_days.to_numpy() / 29,
        frame.rarity,
        frame.inactive_days,
        frame.code_module,
        policy,
        "classifier",
        seed,
        eligibility_mask=frame[MODEL].to_numpy() >= policy.risk_threshold,
    )[0]


def specialists(frame, train, protocol, global_model):
    """Training-size rule fixed in advance; assessment-free features in both arms."""
    features = SAFE_NUM + ["code_module"]
    global_risk, _ = predict(global_model, frame, features)
    hybrid = global_risk.copy()
    eligibility, rows = [], []
    for module in sorted(frame.code_module.unique()):
        local = train.loc[train.code_module.eq(module)]
        counts = local.target.value_counts().reindex(
            ["Success", "Fail", "Withdrawn"], fill_value=0
        )
        eligible = len(local) >= 300 and counts.min() >= 30
        eligibility.append(
            {
                "protocol": protocol,
                "module": module,
                "training_n": len(local),
                "smallest_class_n": counts.min(),
                "specialist_fitted": eligible,
            }
        )
        if eligible:
            fitted = classifier("logistic", 7101, SAFE_NUM).fit(
                local[features], local.target
            )
            mask = frame.code_module.eq(module).to_numpy()
            hybrid[mask], _ = predict(fitted, frame.loc[mask], features)
    for name, risk in [("global_selected", global_risk), ("module_logistic", hybrid)]:
        actions = allocate(risk, frame.rarity, frame.inactive_days, frame.code_module)[
            0
        ]
        for module in ["ALL"] + sorted(frame.code_module.unique()):
            mask = (
                np.ones(len(frame), bool)
                if module == "ALL"
                else frame.code_module.eq(module).to_numpy()
            )
            rows.append(
                {
                    "protocol": protocol,
                    "variant": name,
                    "module": module,
                    "average_precision": average_precision_score(
                        frame.target[mask].ne("Success"), risk[mask]
                    ),
                    **observed_metrics(frame.target[mask], actions[mask]),
                }
            )
    return rows, eligibility


def record_model_metrics(frame, bundle, probabilities, protocol, results):
    """Summarize ranking quality and conditional learner-bootstrap uncertainty."""
    metrics = ml_metrics(frame.target, probabilities, bundle["model"].classes_)
    ids, index = np.unique(frame.id_student, return_inverse=True)
    rng = np.random.default_rng(7101)
    ap = []
    for _ in range(200):
        sampled = rng.integers(0, len(ids), len(ids))
        weights = np.bincount(sampled, minlength=len(ids))[index]
        ap.append(
            average_precision_score(
                frame.target.ne("Success"), frame[MODEL], sample_weight=weights
            )
        )
    ap_low, ap_high = np.quantile(ap, [0.025, 0.975])
    results["model_metrics"].append(
        {
            "protocol": protocol,
            **metrics,
            "average_precision_low": ap_low,
            "average_precision_high": ap_high,
            "isolation_forest_outcome_ap": average_precision_score(
                frame.target.ne("Success"), frame.rarity
            ),
            "inactivity_outcome_ap": average_precision_score(
                frame.target.ne("Success"), frame.inactive_days
            ),
        }
    )


def record_route_comparisons(frame, reference, baseline, protocol, results):
    """Compare all routes at the same capacity, then audit each learner segment."""
    for route in [*ROUTES, "inactivity_baseline"]:
        actions = (
            baseline
            if route == "inactivity_baseline"
            else frame_actions(frame, route, model=MODEL)[0]
        )
        lo, hi = coverage_interval(frame, actions)
        dl, dh = coverage_interval(frame, actions, reference)
        bl, bh = coverage_interval(frame, actions, baseline)
        results["comparison"].append(
            {
                "protocol": protocol,
                "route": route,
                **observed_metrics(frame.target, actions),
                "coverage_low": lo,
                "coverage_high": hi,
                "difference_low": dl,
                "difference_high": dh,
                "vs_inactivity_low": bl,
                "vs_inactivity_high": bh,
            }
        )
        for dimension in ["code_module", "gender", "prior_enrolment", "unseen_module"]:
            for value, group in frame.groupby(dimension, dropna=False):
                selected = actions[group.index]
                counts = observed_metrics(group.target, selected)
                allowed = len(group) >= 50 and counts["adverse_n"] >= 10
                ci = coverage_interval(group, selected) if allowed else (np.nan, np.nan)
                results["segments"].append(
                    {
                        "protocol": protocol,
                        "route": route,
                        "dimension": dimension,
                        "segment": str(value),
                        **counts,
                        "coverage_low": ci[0],
                        "coverage_high": ci[1],
                        "interpretation_allowed": allowed,
                    }
                )


def record_warning_and_gender_profiles(frame, reference, protocol, results):
    """Describe within-course gender gaps and observed outcomes among flagged cases."""
    for (module, gender), group in frame.groupby(["code_module", "gender"]):
        counts = observed_metrics(group.target, reference[group.index])
        allowed = len(group) >= 50 and counts["adverse_n"] >= 10
        ci = (
            coverage_interval(group, reference[group.index])
            if allowed
            else (np.nan, np.nan)
        )
        results["course_gender"].append(
            {
                "protocol": protocol,
                "module": module,
                "gender": gender,
                **counts,
                "coverage_low": ci[0],
                "coverage_high": ci[1],
                "interpretation_allowed": allowed,
            }
        )
    for outcome, group in frame.loc[reference > 0].groupby("target"):
        results["warning_profiles"].append(
            {
                "protocol": protocol,
                "outcome": outcome,
                "n": len(group),
                "inactivity_median": group.inactive_days.median(),
                "score_observed_n": group.score_mean.notna().sum(),
                "assessment_use": "descriptive_only_not_a_predictor",
            }
        )


def record_sensitivity(frame, protocol, results):
    """Vary one planning assumption at a time; keep comparator eligibility matched."""
    for parameter, values in SWEEPS.items():
        for value in values:
            policy = replace(Policy(), **{parameter: value})
            for route in ["classifier", "anomaly", "inactivity_baseline"]:
                actions = (
                    inactivity_actions(frame, policy)
                    if route == "inactivity_baseline"
                    else frame_actions(frame, route, policy, model=MODEL)[0]
                )
                results["sensitivity"].append(
                    {
                        "protocol": protocol,
                        "parameter": parameter,
                        "value": value,
                        "route": route,
                        "eligibility": "shared_assessment_free_cutoff",
                        **observed_metrics(frame.target, actions, policy),
                    }
                )


def record_calibration(frame, reference, protocol, results):
    """Compare scores with observed rates; this does not fit a calibration correction."""
    groups = {"all": np.ones(len(frame), bool), "contacted": reference > 0}
    groups.update(
        {
            "course_" + str(m): frame.code_module.eq(m).to_numpy()
            for m in frame.code_module.unique()
        }
    )
    for name, mask in groups.items():
        y = frame.target.ne("Success").to_numpy()[mask]
        risk = frame[MODEL].to_numpy()[mask]
        results["calibration"].append(
            {
                "protocol": protocol,
                "group": name,
                "n": int(mask.sum()),
                "mean_predicted": risk.mean(),
                "observed_rate": y.mean(),
                "brier": np.mean((risk - y) ** 2),
            }
        )


def record_seed_stability(frame, train, bundle, choices, protocol, results):
    """Refit the already-selected candidate; seeds do not create new test cohorts."""
    chosen = choices.loc[
        choices.protocol.eq(protocol) & choices.variant.eq(MODEL), "selected_model"
    ].iloc[0]
    for seed in [7101, 7102, 7103]:
        seeded, _, _ = load_frame(protocol, seed)
        fitted = classifier(chosen, seed, SAFE_NUM).fit(
            train[bundle["features"]], train.target
        )
        seeded[MODEL], _ = predict(fitted, seeded, bundle["features"])
        for route in ["classifier", "anomaly"]:
            actions = frame_actions(seeded, route, seed=seed, model=MODEL)[0]
            results["stability"].append(
                {
                    "protocol": protocol,
                    "seed": seed,
                    "route": route,
                    **observed_metrics(seeded.target, actions),
                    "scope": "fixed_model_seed_check_not_independent_validation",
                }
            )


def record_deeper_analyses(frame, train, bundle, reference, protocol, results):
    """Run the committed analyses and the explicitly assumed action-value scenarios."""
    transitions, crossovers, uncertainty = review_route_analysis(frame, protocol, MODEL)
    special, eligibility = specialists(frame, train, protocol, bundle["model"])
    extras = dict(
        action_transitions=transitions,
        action_break_even=crossovers,
        action_value_uncertainty=uncertainty,
        specialists=special,
        specialist_eligibility=eligibility,
        reconciliation=reconciliation_analysis(frame, protocol, MODEL),
        action_value_scenarios=conditional_value_analysis(frame, protocol, MODEL),
        workload_stress=[
            {"protocol": protocol, **r}
            for r in workload_stress(frame, reference, MODEL)
        ],
    )
    for name, rows in extras.items():
        results[name].extend(rows)


def run():
    """Load frozen predictions, execute each analysis once, and write final CSVs."""
    data = pd.read_csv(ROOT / "data/processed/development.csv")
    if set(data.code_presentation) != {"2013B", "2014B"}:
        raise ValueError("Only recorded development periods are allowed")
    results = {
        name: []
        for name in [
            "comparison",
            "segments",
            "course_gender",
            "sensitivity",
            "calibration",
            "stability",
            "reconciliation",
            "specialists",
            "specialist_eligibility",
            "action_transitions",
            "action_break_even",
            "action_value_uncertainty",
            "action_value_scenarios",
            "workload_stress",
            "warning_profiles",
            "model_metrics",
        ]
    }
    choices = pd.read_csv(ROOT / "outputs/availability_audit.csv")
    for protocol in ["identity_disjoint", "operational"]:
        train, _ = split_frames(data, protocol)
        frame, bundle, probabilities = load_frame(protocol)
        reference = frame_actions(frame, model=MODEL)[0]
        baseline = inactivity_actions(frame)
        record_model_metrics(frame, bundle, probabilities, protocol, results)
        record_route_comparisons(frame, reference, baseline, protocol, results)
        record_warning_and_gender_profiles(frame, reference, protocol, results)
        record_sensitivity(frame, protocol, results)
        record_calibration(frame, reference, protocol, results)
        record_seed_stability(frame, train, bundle, choices, protocol, results)
        record_deeper_analyses(frame, train, bundle, reference, protocol, results)
    for name, rows in results.items():
        output = pd.DataFrame(rows)
        output["routing_model"] = MODEL
        output["evaluation_scope"] = "previously_examined_2014B_retrospective"
        output.to_csv(ROOT / f"outputs/final_{name}.csv", index=False)
    print(
        "Final assessment-free comparisons, five sweeps, segments and three deeper analyses complete."
    )


if __name__ == "__main__":
    run()
