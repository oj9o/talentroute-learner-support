"""Generate the final narrative and figures from assessment-free outputs."""

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from .data import ROOT
from .report import table


def read(name, primary=True):
    """Read generated final evidence, selecting the primary population by default."""
    frame = pd.read_csv(ROOT / f"outputs/final_{name}.csv")
    return frame.loc[frame.protocol.eq("identity_disjoint")] if primary else frame


def figures():
    """Plot existing final CSVs; do not refit models or select favorable results."""
    folder = ROOT / "outputs/figures"
    folder.mkdir(exist_ok=True)
    plt.rcParams.update(
        {"font.size": 10, "axes.spines.top": False, "axes.spines.right": False}
    )

    def save(fig, name):
        fig.tight_layout()
        fig.savefig(folder / f"final_{name}.png", dpi=160, bbox_inches="tight")
        plt.close(fig)

    routes = (
        read("comparison")
        .set_index("route")
        .loc[["inactivity_baseline", "classifier", "anomaly"]]
    )
    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.barh(
        [
            "Inactivity baseline",
            "Assessment-free classifier",
            "Classifier + anomaly reserve",
        ],
        routes.coverage * 100,
        color=["#86948e", "#125c56", "#a97545"],
    )
    ax.errorbar(
        routes.coverage * 100,
        range(3),
        xerr=np.array(
            [
                routes.coverage - routes.coverage_low,
                routes.coverage_high - routes.coverage,
            ]
        )
        * 100,
        fmt="none",
        color="#243732",
        capsize=3,
    )
    ax.set(
        xlim=(0, 50),
        xlabel="Adverse cases contacted (%)",
        title="Retrospective targeting at the same staffing budget",
    )
    save(fig, "comparison")
    sensitivity = read("sensitivity")
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    for ax, parameter, label in zip(
        axes,
        ["minutes_per_100", "review_minutes"],
        ["Minutes per 100 cases", "Minutes per review"],
    ):
        for route, color in [
            ("classifier", "#125c56"),
            ("inactivity_baseline", "#86948e"),
            ("anomaly", "#a97545"),
        ]:
            rows = sensitivity[
                sensitivity.parameter.eq(parameter) & sensitivity.route.eq(route)
            ].sort_values("value")
            ax.plot(
                rows.value,
                rows.coverage * 100,
                "o-",
                label=route.replace("_", " "),
                color=color,
            )
        ax.set(xlabel=label, ylabel="Adverse coverage (%)")
    axes[0].legend(frameon=False, fontsize=8)
    save(fig, "sensitivity")
    rows = read("segments")
    rows = rows[rows.route.eq("classifier") & rows.dimension.eq("code_module")]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].barh(rows.segment, rows.review_n, label="Review", color="#125c56")
    axes[0].barh(
        rows.segment, rows.alert_n, left=rows.review_n, label="Alert", color="#a97545"
    )
    axes[0].set(xlabel="Course cases contacted", title="Actual queue composition")
    axes[0].legend(frameon=False)
    axes[1].barh(
        rows.segment,
        rows.staff_minutes / rows.staff_minutes.sum() * 100,
        color="#125c56",
        label="Staff time",
    )
    axes[1].plot(
        rows.n / rows.n.sum() * 100,
        rows.segment,
        "o",
        color="#a97545",
        label="Case share",
    )
    axes[1].set(xlabel="Share (%)", title="Time allocation versus cohort size")
    axes[1].legend(frameon=False)
    save(fig, "queue_composition")
    rows = read("course_gender")
    rows = rows[rows.interpretation_allowed]
    fig, ax = plt.subplots(figsize=(8, 4))
    modules = sorted(rows.module.unique())
    for gender, offset, color in [("F", -0.1, "#125c56"), ("M", 0.1, "#a97545")]:
        group = rows[rows.gender.eq(gender)].set_index("module").reindex(modules)
        ax.errorbar(
            group.coverage * 100,
            np.arange(len(modules)) + offset,
            xerr=np.array(
                [
                    group.coverage - group.coverage_low,
                    group.coverage_high - group.coverage,
                ]
            )
            * 100,
            fmt="o",
            color=color,
            capsize=3,
            label=gender,
        )
    ax.set(
        yticks=range(len(modules)),
        yticklabels=modules,
        xlabel="Adverse coverage (%)",
        title="Within-course gender audit; conditional intervals",
    )
    ax.legend(frameon=False)
    save(fig, "gender_by_course")


def run():
    """Generate the final narrative from the saved assessment-free analysis outputs."""
    figures()
    routes = read("comparison").set_index("route")
    main, baseline, anomaly = (
        routes.loc[name] for name in ["classifier", "inactivity_baseline", "anomaly"]
    )
    operational = (
        read("comparison", False)
        .query("protocol == 'operational' and route == 'classifier'")
        .iloc[0]
    )
    metrics = read("model_metrics").iloc[0]
    segments = read("segments").query("route == 'classifier'")
    courses = segments.query("dimension == 'code_module'").set_index("segment")
    genders = segments.query("dimension == 'gender'").set_index("segment")
    ggg = courses.loc["GGG"]
    calibration = read("calibration").set_index("group").loc["contacted"]
    stress = (
        read("workload_stress")
        .query("review_minutes == 45 and alert_minutes == 2")
        .iloc[0]
    )
    reconciled = read("reconciliation").query("module == 'ALL'")
    special = read("specialists").query("module == 'ALL'")
    changes = read("action_transitions").set_index("route").loc["anomaly"]
    availability = pd.read_csv(ROOT / "outputs/availability_audit.csv")
    folds = pd.read_csv(ROOT / "outputs/availability_selection.csv")
    foldmeans = (
        folds.query("protocol == 'identity_disjoint' and variant == 'assessment_free'")
        .groupby("model")[["coverage", "adverse_average_precision"]]
        .mean()
        .reset_index()
    )
    sensitivity = read("sensitivity").pivot(
        index=["parameter", "value"], columns="route", values="adverse_contact_n"
    )
    sensitivity["classifier_minus_inactivity"] = (
        sensitivity["classifier"] - sensitivity["inactivity_baseline"]
    )
    sensitivity["anomaly_minus_classifier"] = (
        sensitivity["anomaly"] - sensitivity["classifier"]
    )
    sensitivity = sensitivity.reset_index()
    selected = availability.query(
        "protocol == 'identity_disjoint' and variant == 'assessment_free'"
    ).iloc[0]
    enabled = availability.query(
        "protocol == 'identity_disjoint' and variant == 'assessment_assumption'"
    ).iloc[0]
    nested = pd.read_csv(ROOT / "outputs/nested_results.csv")
    nested_model = nested.query("method == 'nested_selected_classifier'")
    nested_anomaly = nested.query("method == 'nested_anomaly_reserve'")
    nested_anomaly_extra = int(nested_anomaly.adverse_contact_n.sum() - nested_model.adverse_contact_n.sum())
    nested_rule = nested.query("method == 'inactivity'")
    nested_coverage = (
        nested_model.adverse_contact_n.sum() / nested_model.adverse_n.sum()
    )
    nested_baseline = nested_rule.adverse_contact_n.sum() / nested_rule.adverse_n.sum()
    nested_extra = int(
        nested_model.adverse_contact_n.sum() - nested_rule.adverse_contact_n.sum()
    )
    nested_table = nested[
        [
            "outer_fold",
            "method",
            "selected_model",
            "evaluation_cases",
            "adverse_contact_n",
            "coverage",
            "staff_minutes",
        ]
    ]
    correction = pd.read_csv(ROOT / "outputs/probability_audit.csv")
    correction_table = correction[["fold", "method", "temperature", "adverse_brier", "log_loss", "adverse_contact_n"]]
    correction_means = correction.groupby("method")[["adverse_brier", "log_loss"]].mean()
    correction_counts = correction.groupby("method").adverse_contact_n.sum()
    report = f"""# TalentRoute: assessment-free learner-support decisions

Mouza Aldarmaki · MAAI7101 · Final project

## Executive summary

TalentRoute helps a learner-support coordinator decide which course cases to review or alert when staff time is limited. It ranks cases using early platform activity and enrolment information. Assessment scores are excluded because their release timing is unverified; submission-derived fields are also excluded as a conservative simplification, not because they are proven unavailable. A submission-only alternative was not tested.

In a previously examined cohort, the queue reaches {int(main.adverse_contact_n):,} of {int(main.adverse_n):,} course cases with later failure or withdrawal ({main.coverage:.1%}), versus {int(baseline.adverse_contact_n):,} ({baseline.coverage:.1%}) when ranking by inactivity alone at the same workload. The difference is too uncertain to establish superiority. An additional unusual-engagement detector does not establish enough extra targeting value to recommend reserving review places for it.

The practical output is an adjustable queue with a separate feasibility checker. Staffing assumptions and course composition materially change who gets attention. The recommendation is a research tool for inspecting these trade-offs, not a validated institutional policy. Historical targeting does not establish prevented failures or intervention benefits, and no untouched final test remains.

## 1. Who decides what, and why?

An educational consulting team may support universities as well as other learning providers. Its coordinator receives a list of enrolled learners at day 28 and has a finite amount of staff time. A human review means a staff member investigates a course case; an alert is a lower-effort contact. The coordinator sets available minutes, assumed effort, eligible risk scores and the share reserved for alerts. TalentRoute ranks cases and proposes mutually exclusive review, alert or no-action assignments. A person checks feasibility and decides whether outreach is appropriate.

The business question is: **How should limited review and alert capacity be directed toward learners with later observed Fail or Withdrawn outcomes, and where does that allocation fail?** This makes the university population directly relevant to the consulting scenario. There is no assertion that university learners behave like corporate employees. Applying the system elsewhere would require local data, workflow agreement and validation.

Four questions structure the evidence: Does classification outperform a simple comparator? Does an anomaly review reserve add targeting value? How do staffing assumptions and course or learner segments change the queue? Which attractive alternatives fail or remain uncertain? A valuable result can be a rejected method or a capacity constraint, rather than a higher headline score.

The intermediate design retains classification, outlier detection and three deeper investigations. Revisions address score availability, incompatible score blending and concentrated errors. Appendix B links each commitment and feedback item to evidence and the resulting decision. The archived definition already disclosed prior test use; this is not an exemption from final evaluation requirements.

## 2. Proposed system

```mermaid
flowchart LR
    A[Day-28 engagement and enrolment inputs] --> B[Assessment-free classifier]
    A --> C[Training-fitted Isolation Forest]
    B --> D[Risk-ranked review and alert queue]
    C --> E[Optional reserve inside existing review capacity]
    E --> D
    F[Staff time and action costs] --> D
    D --> G[Separate feasibility checker]
    G --> H[Coordinator inspects and decides]
```

The default uses no anomaly reserve; the connected reserve is an evaluated alternative. Later observed outcomes are used only to evaluate the frozen assignments, never by the allocator or checker.

## 3. Evaluation setup and results

OULAD is a public distance-learning dataset with registration, platform activity, assessments and observed outcomes. Each row in the modeling table is a course enrolment, not necessarily a unique person. Pass and Distinction map to Success; Fail and Withdrawn remain separate classifier classes. Their combined adverse indicator is used only for the declared targeting metric. The separate action/outcome counts prevent that combination from hiding different mechanisms. No outcome labels are simulated.

Features are restricted to information recorded by day 28: engagement counts in early and later windows, their change, inactivity, study credits, previous attempts and course. Log counts reduce extreme activity scale; inactivity represents the absence of recent recorded engagement. These are plausible warning signals, not measures of motivation or proof of causation. All numeric imputation and model-specific preprocessing fit training records only. IDs, gender, final outcomes and post-cutoff activity are not predictors. Gender is used only for audit. There is no clustering or dimensionality reduction added merely to display another technique.

OULAD does not establish exact assessment score-release dates. Restricting submission dates alone cannot prove a grade was visible. The final system conservatively removes **all five assessment-derived inputs**. The score-release issue directly concerns scores; removing submission counts, lateness and the no-early-assessment indicator is a broader simplification to avoid dependence on assessment schedules and recording assumptions. A submission-only variant was not tested, and these fields are not asserted to be inherently unavailable. Earlier 2014B diagnostics prompted this design decision; training-only candidate selection does not erase that exposure. Assessment fields retained in historical diagnostic tables are not accessed by its predictor. Mutation tests change assessments and outcomes while checking that final predictions stay identical.

Training uses 2013B; evaluation uses 2014B. Calendar interval checks account for uncertain start days and assumed result-release delays. Training on earlier completed courses is more defensible than using a possibly unfinished later presentation, but final-result publication remains an assumption. The identity-disjoint design removes overlapping evaluation identities from training. The operational companion retains mature prior enrolments and reports returning learners separately. Both evaluate the same cases; neither selects training rows using 2014J membership.

The final classifier and preprocessing are selected within three learner-grouped training folds, comparing six bounded candidates: logistic regularization levels, a constrained tree and two boosting capacities. The ranking rule is mean fold coverage, then average precision, then fixed candidate order. The selected candidate is logistic regression with C=1. Its mean fold coverage ties C=10, but its unrounded AP is slightly higher (0.730185675 versus 0.730183657); fixed candidate order did not decide this result. The chosen family is fitted on all allowed training rows before evaluation. The candidate grid reflects earlier project learning, so this separation repairs direct selection on evaluation labels but does not create a fresh experiment.

Both 2014B and 2014J were previously examined. Repeated splits, new seeds and a new freeze cannot restore independence. No fresh cohort is available. This revision does not score 2014J again and does not claim the independent final-evaluation requirement is fully satisfied. Its results are retrospective development evidence; an external future cohort remains necessary for confirmation. A supplementary nested 2013B diagnostic evaluates the selection procedure at equal capacity: {nested_coverage:.1%} coverage versus {nested_baseline:.1%} for inactivity. Appendix A explains its distinct population and limits.

### Models, metrics and comparators

The primary ML metric is adverse-outcome average precision (AP), appropriate for assessing ranking against the observed adverse prevalence. The final model has AP {metrics.adverse_average_precision:.3f}, with conditional learner-bootstrap interval [{metrics.average_precision_low:.3f}, {metrics.average_precision_high:.3f}]. Brier score and class-specific metrics are also exported. The primary decision metric is the fraction of actual adverse cases contacted at a common workload. Contact precision, separate Fail/Withdrawn counts, review/alert counts and staff minutes qualify that measure. Coverage treats both contacts equally; it does not itself answer which intervention is worth its cost.

The default scenario allocates 300 staff minutes per 100 enrolments, assumes 30 minutes per review and two per alert, reserves an initial alert budget share of 20%, and caps alerts at 20% of cases. Whole-action rounding and the remaining time determine capacity. These are explicit constructed assumptions, not observed university practice. For this cohort the queue has {int(main.review_n):,} reviews and {int(main.alert_n):,} alerts, consuming {int(main.staff_minutes):,} minutes. Its contact precision is {main.contact_precision:.1%}. Reviews reach {int(main.review_fail_n + main.review_withdrawn_n)} adverse cases versus {int(baseline.review_fail_n + baseline.review_withdrawn_n)} for inactivity, while {int(main.review_success_n)} versus {int(baseline.review_success_n)} reviewed cases later succeed. These counts distinguish action tiers without claiming support was unnecessary.

Isolation Forest fits engagement features on training data only. Its training-reference anomaly percentile ranks a separately reserved portion of the existing review capacity. It is never added to the outcome probability: equal numeric ranges do not imply comparable meanings. Removing the reserve gives the default classifier-only queue. Inactivity, course round-robin and seeded-random reserves test whether the detector earns its complexity. A full inactivity-ranked queue is the transparent no-model comparator; it is distinct from reserving only some reviews for inactivity. It replaces the intermediate score-plus-inactivity rule to match the assessment-free input restriction.

All route comparisons use the same capacity. Cutoff sweeps apply the classifier eligibility mask to the inactivity comparator too, so they compare ordering among the same eligible cases. Thresholds are model-score eligibility rules, not calibrated guarantees. No threshold or cost is selected for a favorable retrospective result.

### ML-level comparison

{table(read("model_metrics"), ["adverse_average_precision", "average_precision_low", "average_precision_high", "inactivity_outcome_ap", "isolation_forest_outcome_ap"])}

### Training-only candidate comparison

{table(foldmeans)}

### Final-system results and uncertainty

{table(read("comparison"), ["route", "adverse_contact_n", "coverage", "contact_precision", "staff_minutes", "difference_low", "difference_high"])}

The difference interval columns compare each route with classifier-only. The separate inactivity comparison is reported in the executive summary and exported CSV. Intervals resample learners with all their enrolments together, holding predictions and assignments fixed. They describe conditional sampling uncertainty; they exclude refitting, earlier search and workflow uncertainty. They are not prospective confidence claims or treatment-effect intervals.

The operational companion contacts {int(operational.adverse_contact_n):,} adverse cases ({operational.coverage:.1%}). This training-population sensitivity check retains the same evaluation cases; it is not an independent test or evidence that all segments are stable. Three seed checks refit the fixed selected candidate and vary tie-breaking and detector seeds; their spread is reported separately. Logistic fitting is deterministic here, so unchanged classifier coverage is expected; detector variation is the meaningful stochastic check. Seeds are not independent test populations.

![Final route comparison](../outputs/figures/final_comparison.png)

## 4. Ablation

The intermediate success gate required a paired coverage-difference interval entirely above zero versus the model-free rule. The detector additionally required improvement over classifier-only with at most a two-percentage-point precision loss. Neither improvement gate is cleared here: both intervals cross zero. The detector satisfies the precision margin but not the improvement requirement. The current inactivity comparator, training population and assessment-free inputs differ from the intermediate setup; this is a disclosed revision, not a claim that the original experiment passed.

The anomaly reserve contacts {int(anomaly.adverse_contact_n):,} adverse cases, only {int(anomaly.adverse_contact_n - main.adverse_contact_n)} more than classifier-only. Its paired coverage-difference interval is [{anomaly.difference_low * 100:.2f}, {anomaly.difference_high * 100:.2f}] percentage points. It changes {int(changes.changed_action_n)} actions, gains {int(changes.new_adverse_contact_n)} adverse contacts and loses {int(changes.lost_adverse_contact_n)}. This distinguishes changed action type from newly reached people. Detector outcome AP is {metrics.isolation_forest_outcome_ap:.3f}, below inactivity's {metrics.inactivity_outcome_ap:.3f}; outcome AP is only a relevance diagnostic because true anomaly labels do not exist. The default remains zero detector reserve.

## 5. Sensitivity, stability and concentrated failures

Five sweeps vary budget, review effort, reserve share, score cutoff and alert share, one at a time. Results and workload counts are generated for both populations using the final assessment-free predictions. The budget and effort curves show how staffing choices change the observed coverage; they do not show saved students. More resources can increase contact reach, while a higher cutoff may leave capacity unused.

{table(sensitivity, ["parameter", "value", "classifier_minus_inactivity", "anomaly_minus_classifier"])}

The classifier point advantage remains positive across the tested budget and effort settings, but these sweep differences have no uncertainty intervals and the default interval crosses zero. At cutoff 0.75 the common eligibility gate leaves all queues contacting the same 966 adverse cases; this is not evidence of ranking robustness. Alert shares 0.2 and 0.4 coincide because the alert-count cap binds. Anomaly differences remain between minus two and plus two cases across these sweeps; no tested setting establishes a reason to activate the reserve.

![Budget and effort sensitivity](../outputs/figures/final_sensitivity.png)

Course GGG receives {ggg.staff_minutes / main.staff_minutes:.1%} of staff minutes while representing {ggg.n / main.n:.1%} of cases. It reaches {int(ggg.adverse_contact_n)} of {int(ggg.adverse_n)} adverse cases ({ggg.coverage:.1%}). This describes concentration in the current queue. Earlier course results used a different model and population and are not a matched before/after comparison. Course calibration and queue composition make this visible. A coordinator should review course-specific workload and score reliability before using the global queue.

Overall female adverse coverage is {genders.loc["F", "coverage"]:.1%}, versus {genders.loc["M", "coverage"]:.1%} for males. Contact precision is {genders.loc["F", "contact_precision"]:.1%} for women and {genders.loc["M", "contact_precision"]:.1%} for men. Women account for {int(genders.loc["F", "review_success_n"])} of {int(main.review_success_n)} later-successful reviewed cases. Within-course coverage gaps are smaller in CCC (30.5% versus 31.4%) and GGG (82.6% versus 84.6%). These patterns do not establish fairness or causally explain the aggregate gap through course mix. Within-course comparisons retain denominators and conditional intervals; groups below 50 cases or ten adverse outcomes are marked unsuitable for interpretation. No protected-attribute quota is silently introduced.

![Queue composition and resource concentration](../outputs/figures/final_queue_composition.png)

![Within-course gender comparisons](../outputs/figures/final_gender_by_course.png)

Among contacted cases, mean predicted adverse risk is {calibration.mean_predicted:.1%}, while the observed adverse rate is {calibration.observed_rate:.1%}. The overstatement means displayed scores should support ranking, not be read as verified individual probabilities. Calibration would need training-only fitting followed by genuinely new evaluation; fitting a correction on this exposed evaluation cohort would not repair confirmation.

{table(read("calibration").query("group.str.startswith('course_')", engine="python"), ["group", "n", "mean_predicted", "observed_rate", "brier"])}

The workload stress test freezes membership before changing effort. Raising reviews from 30 to 45 minutes creates a {int(stress.shortfall_minutes):,}-minute shortfall. An explicit alerts-first contingency defers {int(stress.deferred_n)} original contacts and retains {stress.retained_coverage:.1%} adverse coverage. Replanning under the same stressed budget gives {stress.replanned_coverage:.1%}. Both are feasible; neither is asserted to maximize real intervention benefit. This exposes failure and an actionable fallback instead of hiding overspend through automatic reallocation.

## 6. Three promised deeper investigations

**Equal-quota reconciliation.** Interleave classifier, anomaly and inactivity rankings at the same total quota, removing duplicate cases. The Swiss Cheese idea motivates looking for complementary misses, not assuming independent layers. The output below tests that idea directly. More layers do not guarantee better coverage, and the global risk queue remains the default.

{table(reconciled, ["policy", "adverse_contact_n", "coverage", "staff_minutes"])}

**Warning-positive profiles.** Compare later Success, Fail and Withdrawn among final flagged cases, reporting inactivity and the count with observed assessment scores. Scores here are descriptive only. A flagged learner who succeeds is neither proof of resilience nor proof of wasted support: no intervention history establishes either explanation. The analysis helps identify what staff would need to investigate rather than assigning a fabricated reason.

{table(read("warning_profiles"), ["outcome", "n", "inactivity_median", "score_observed_n"])}

**Course specialization and learner segments.** Fit a local logistic model only where training has at least 300 cases and 30 examples per class; otherwise retain the selected global model. All models use assessment-free features. Eligibility is determined from training, never from evaluation success. The exploratory comparison below is reported without promoting the best-looking result after inspection. Returning-learner, unseen-course and within-course demographic audits accompany it.

{table(special, ["variant", "average_precision", "coverage", "adverse_contact_n"])}

These analyses sharpen the recommendation: keep the simple global queue as a transparent demonstration, review concentration explicitly, and require new evidence before adopting specialists or the detector reserve. They do not imply that the original two-family design was successful merely because both algorithms run.

## 7. Insights and recommendations

**Staffing dominates the practical decision.** Increasing available time changes reach more than adding an anomaly reserve. Agree actual effort and available staff time before model refinements. If effort rises, compare a replanned queue with the explicit contingency; neither is optimal without real action values.

**Model complexity has not established better outcomes.** Keep inactivity as a standing comparator. Treat classification as a provisional ranking and retain zero anomaly reserve. Specialists are exploratory rather than a selected deployment alternative.

**A feasible queue still needs scrutiny.** Review GGG's concentrated workload and score reliability with course staff before outreach. Do not present uncalibrated scores as verified personal probabilities. A flag initiates investigation, not a diagnosis; coordinate multiple course cases belonging to one learner.

The decision rules have explicit limits:

| Decision | Why this choice | When to reconsider |
|---|---|---|
| Assessment-free inputs | Avoid uncertain score availability | Verify input timestamps before adding assessment fields |
| No anomaly reserve | Added targeting value is not established | Require new evidence before reserving scarce review places |
| Review, alert or no action | Apply the declared ranking and staffing caps | Recheck costs and capacity when staffing changes |
| No action for an eligible case | Capacity can run out | Do not interpret it as evidence the learner is safe |
| Human approval before outreach | Feasibility does not establish intervention value | Review course concentration and repeated-learner contacts |

Coverage cannot identify the best intervention. As an additional analysis, conditional preference scenarios weight reviews and alerts separately, distinguish Fail and Withdrawn, penalize contacts to later Success cases, and subtract assumed effort. Weights are external scenario preferences applied to observed outcome counts, not to the score used for selection. This avoids the earlier circular evaluation. Break-even calculations show which assumed review value would favor a reserve, and paired fixed-action intervals show uncertainty. None estimates causal benefit, monetary ROI or the true cost of a false flag.

The action-value analysis is an additional decision-relevant deep dive. The table reports reserve-versus-risk-only preference differences under the declared default weights; intervals remain conditional and are not intervention-effect estimates.

{table(read("action_value_uncertainty").query("withdrawn_value == 1"), ["route", "preference_difference", "difference_low", "difference_high"])}

## 8. Limitations, failed approaches and risks

In the matched training-only audit, assessment-enabled prediction reaches {int(enabled.adverse_contact_n):,} adverse cases versus {int(selected.adverse_contact_n):,} assessment-free. The latter sacrifices targeting performance to remove that input dependence; it is not an accuracy improvement. Direct development-cohort model choice was replaced by training-only grouped selection, while acknowledging earlier exposure. Adding anomaly ranks did not establish incremental value; numerical probability/percentile blending was rejected. Reconciliation and specialists remain exploratory. One workbench and report generator reproduce current evidence; historical experiments are labeled separately.

The app lets a user change capacity, effort, eligibility and route, then inspect actions and workload. A separate checker tests an edited plan without outcomes. Saved-setting comparison shows entering, leaving and changed-action cases. Individual input edits rescore a fitted model; they do not manufacture a future outcome or simulate the causal effect of changing behavior. Exports omit student IDs, protected attributes and outcomes. Multiple course cases for one learner still require coordination before real outreach.

## 9. Connection to the original problem, next steps and reproduction

The coordinator receives a feasible, inspectable allocation and evidence of where it concentrates attention. This answers who could be contacted under declared constraints; it does not establish which support action prevents failure. Real workflow agreement and new outcomes are prerequisites for operational adoption.

Use Python 3.14 with `uv` and `just`: `just install`, `just pipeline`, then `just app`. The CPU pipeline verifies pinned public data, fits models, generates all comparisons and this report, and runs meaningful tests for time eligibility, training-only selection, mutation invariance, budget arithmetic, deterministic allocation and app/output consistency. Runtime is measured in `outputs/runtime.csv`. Linux reproduction checks portability; no LLM or credentials are required to run the project.

Main final-system evidence uses `outputs/final_*.csv`, labeled assessment-free and retrospective. `availability_selection.csv` records the training-fold selection; `availability_audit.csv` records the matched feature-removal comparison. Unprefixed model, route and sensitivity files are historical. The separate `nested_*.csv` diagnostic appears in Appendix A and slides 8/14.

Use the assessment-free workbench to inspect constrained decisions, with no default anomaly reserve. New outcomes and measured workflow evidence are required before deployment. Appendix B distinguishes completed experiments from established benefits; negative results remain part of the deliverable.

Data source: Kuzilek, Hlosta and Zdrahal, Open University Learning Analytics Dataset, UCI, DOI 10.24432/C5KK69, CC BY 4.0. Course concepts applied include classifier comparisons, leakage checks, error slicing, domain-grounded features, and the Beyond Predictions explain/check/compare pattern.
"""
    report += f"""

## Appendix A. Retrospective nested selection diagnostic

**Why.** Conditional intervals on fixed predictions omit refitting and selection. This diagnostic repeats candidate selection inside outer training folds to examine the procedure on excluded learners. It does not repair previous data exposure. Designed after the 2014B results were known, its protocol was written before execution and all folds are reported regardless of outcome.

**Method.** Use all 4,118 eligible 2013B course cases from 4,116 learners, including cases removed by the main identity-disjoint training protocol. One outer partition uses three stratified learner-grouped folds (seed 247101). All cases come from BBB, DDD and FFF in the same cohort. This checks neither temporal shift nor new courses such as GGG. Within each outer training fold, three learner-grouped folds compare the same six candidates by coverage, then average precision, then fixed order. Preprocessing refits inside each fold. Fit the chosen candidate on that outer training partition and evaluate once on its excluded learners. Use the same assessment-free inputs, action costs and capacity for classifier and inactivity queues. Every learner belongs to one outer evaluation fold. Neither 2014B nor 2014J is scored. A supplementary extension refits Isolation Forest inside each outer training fold and evaluates the existing 20% review reserve at matched action counts. Only feature columns enter outer prediction and allocation; labels are used afterwards for scoring. The reserve and candidate grid are not selected from these results.

{table(nested_table)}

**Result.** Across 2,025 adverse cases, pooled outer-fold coverage is {nested_coverage:.1%} versus {nested_baseline:.1%}, reaching {nested_extra} additional cases at identical contact capacity and within budget. Logistic C=1 wins fold 1; C=10 wins folds 2 and 3. All three comparisons favor the selected classifier, but the preferred penalty varies. The fixed anomaly reserve reaches {nested_anomaly_extra} additional adverse cases in total versus classifier-only, an exploratory difference that does not establish incremental benefit or change the default route.

**What this adds.** The result describes the selection procedure within the earlier 2013B population. Its larger advantage cannot establish why the later-cohort advantage is smaller, because population, training size and evaluation design differ. It is not a new independent test, a temporal estimate, or evaluation of one fixed final fitted model. Overlapping training folds do not justify an independent-fold significance claim. It neither supersedes the main 2014B comparison nor passes its original improvement gate. No final model, policy or recommendation changed. Reproduce with `just nested-audit`; source: `outputs/nested_results.csv` and `outputs/nested_inner_selection.csv`.

## Appendix B. Commitments, feedback and evidence

The reference is the [archived intermediate definition](intermediate_definition_archived.md), extracted unchanged from the locally retained November intermediate release. Its identity has not been verified against the renamed ZIP shown in the LMS submission screenshot. The archive states: "A separate frozen Final candidate already used 2014J before this revision. It is no longer unseen." It also requires preserving the original record and independent evidence before confirming a changed model. This documents the development boundary; it does not establish an instructor waiver or make the revised model independently tested.

**Reading this map.** "Executed" means the experiment or check exists, not that it passed its improvement gate. Output paths below are relative to the repository. Final comparisons and figures are regenerated by `just final-analysis`; training selection by `just availability-audit`; nested diagnostics by `just nested-audit`; `just pipeline` assembles the evidence. Archived text is a reference, not a generated experimental result.

| Promise or feedback | Evidence | What was implemented or tried | Finding, alternative and reason |
|---|---|---|---|
| University learners must fit the business problem | Report section 1; archived definition | A consulting coordinator prioritizes university course cases | Corporate employee transfer is not claimed; the dataset matches the stated learner population |
| Classification plus outlier detection | `src/talentroute/models.py`; `outputs/final_model_metrics.csv`; `outputs/final_comparison.csv` | Logistic, tree and boosting comparisons; connected Isolation Forest review reserve | Both families implemented; incremental reserve benefit unestablished, so default reserve is zero |
| Do not combine incomparable scores | `src/talentroute/decision.py`; `outputs/final_action_transitions.csv` | Replace probability/percentile addition with a separate reserve within existing capacity | Anomaly rank is not an outcome probability; retain separate meanings and compare changed actions |
| Real labels and justified features | `src/talentroute/data.py`; `tests/test_availability.py`; report section 3 | Real Success/Fail/Withdrawn outcomes; activity and recency features | No simulated anomaly or intervention labels; missing grades are not invented outcomes |
| Score availability and leakage | `outputs/availability_audit.csv`; `outputs/calendar_bounds.csv`; `outputs/label_availability.csv` | Matched assessment-enabled/free audit; calendar checks; mutation tests | Remove assessment inputs despite lower targeting; submission-only alternative untested; final-label release remains assumed |
| Compare models without evaluation-driven selection | `outputs/availability_selection.csv`; `outputs/model_settings.csv` | Learner-grouped selection within earlier training data | Logistic selected by the declared rule; earlier development exposure is not erased |
| Preserve credible baselines and equal effort | `outputs/final_comparison.csv`; `tests/test_decision.py` | Inactivity versus classifier and reserve alternatives at identical capacity | Classifier superiority not established by the interval; keep inactivity as comparator |
| Separate ML quality, decisions and value | `outputs/final_model_metrics.csv`; `outputs/final_action_value_scenarios.csv`; `outputs/final_action_break_even.csv`; `outputs/final_action_value_uncertainty.csv` | AP, coverage, action-specific outcomes, false flags and conditional value scenarios | Scenario weights are assumptions; actual prevented failures and intervention value remain unmeasured |
| Equal-quota reconciliation / Swiss Cheese | `outputs/final_reconciliation.csv` | Interleave classifier, anomaly and inactivity within one quota | Fewer adverse contacts than risk ranking; keep global risk queue, not a larger warning union |
| Warning-positive profiles | `outputs/final_warning_profiles.csv` | Compare later-successful flagged cases with Fail and Withdrawn; show observed-score denominators | Profiles guide investigation; neither resilience nor wasted intervention is demonstrated |
| Course specialists and segments | `outputs/final_specialists.csv`; `outputs/final_specialist_eligibility.csv`; `outputs/final_segments.csv` | Training-eligible specialists with global fallback | Small exploratory improvement does not justify selecting specialists after inspection |
| Show queue composition and concentrated failures | `outputs/final_segments.csv`; `outputs/final_course_gender.csv`; `outputs/figures/final_queue_composition.png` | Review/alert counts, workload shares and within-course gender audits | Inspect GGG concentration and denominators; no fairness guarantee or causal demographic explanation |
| Audit repeated-learner selection | `outputs/final_comparison.csv`; `outputs/final_segments.csv`; `outputs/populations.csv` | Identity-disjoint and operational training populations evaluated on the same cases | Training-population sensitivity, not a second independent test; coordinate repeat contacts |
| Keep sensitivity and uncertainty | `outputs/final_sensitivity.csv`; `outputs/final_stability.csv`; `outputs/nested_results.csv` | Staffing and eligibility sweeps, seeds, supplementary nested selection | Conditional uncertainty and retrospective stability; nested results do not replace temporal evidence |
| Make failed plans and alternatives visible | `outputs/final_workload_stress.csv`; `src/talentroute/plan.py`; `tests/test_plan.py` | Freeze queue, raise effort, test contingency and replan | Original plan can exceed capacity; explicit feasible alternatives are not claimed optimal |
| Explain scores honestly | `outputs/final_calibration.csv`; report section 5 | Compare model scores with observed outcome frequencies | Use scores for ranking, not verified personal probabilities; training-only temperature experiment not adopted (Appendix C); later-cohort calibration remains unresolved |
| Clear code and a working, explainable artifact | `src/talentroute/`; `tests/`; `Justfile`; `docs/presentation_script.md` | Separate data, models, decisions, analyses and checker; one workbench | Readability is inspectable, not proven by file count; demonstration explains actions without code slides |
| Preserve the test history | `docs/development_protocol.md`; archived definition; report section 3 | Keep revised evaluation retrospective and exclude previously examined final cohort | Historical candidate differs from current model. Initial exposure and availability are not fully verified; no claim that archived results confirm this revision |

### What the experiments changed

Assessment removal trades observed targeting for defensible input availability. The anomaly blend was rejected on meaning, and its separate reserve failed to establish additional targeting value. Equal-quota reconciliation was weaker than the risk queue. Specialists and nested selection were informative but did not justify changing the recommended default or declaring confirmation. The workload stress test produced a concrete failure and feasible alternatives. These outcomes preserve the promised investigations while explaining why implementation does not imply adoption.

The separate KU Leuven exploration concerns a different activity-only model and grade endpoint. It is not used to select this model or to resolve its test requirement; its numerical results are not incorporated into this report's reproducible pipeline. A historical result, a retrospective revision and a separate transfer study must not be pooled or described as interchangeable validation.

## Appendix C. Probability correction tested, not adopted

**Problem and design.** Lecture 13 distinguishes probability correction from threshold changes. Test one temperature-scaling correction, retaining three-class outcomes and assessment-free features. Use only 2013B. Within each learner-grouped outer training fold, reserve one third of learners for calibration; select among the existing six candidates and fit on the remaining two thirds only. Fit temperature by multiclass log loss on calibration learners, with fixed bounds [0.25, 4]. Score raw and corrected versions of the exact same base model on outer-assessment learners. No learner crosses these three roles, and no outer label enters fitting or allocation. This is a development-only diagnostic within 2013B, designed after earlier findings, not independent confirmation. See `docs/probability_audit_protocol.md`.

{table(correction_table)}

**Result and decision.** Mean outer-fold multiclass log loss changes from {correction_means.loc['raw', 'log_loss']:.6f} to {correction_means.loc['temperature', 'log_loss']:.6f} (lower is better), while adverse Brier error changes from {correction_means.loc['raw', 'adverse_brier']:.6f} to {correction_means.loc['temperature', 'adverse_brier']:.6f}. The corrected queue contacts {correction_counts['temperature']:.0f} adverse cases versus {correction_counts['raw']:.0f} without correction at matched capacity. Both probability-metric changes are tiny and point in opposite directions; they do not establish a useful correction. Adverse Brier error is slightly higher in all three folds and two fewer adverse cases are contacted. No superiority or harm claim follows from these small differences. The design and reporting metrics were written before execution, but no numerical adoption threshold was prespecified; retaining the default is a post hoc conservative interpretation, not a passed statistical gate. Do not replace the application model or claim its probabilities are repaired. Do not compare these raw scores directly with Appendix A as a correction effect: model-fitting samples differ because calibration learners are withheld here. The identical raw total of 876 in the two diagnostics is coincidental; their fold counts differ. This raw arm is not the deployed default model.

A global temperature fitted within 2013B does not test or resolve course-specific calibration under later-cohort shift. It also does not make anomaly percentiles comparable with outcome probabilities.

Temperature scaling preserves the most likely class but can change the ranking of combined Fail-plus-Withdrawn risk. No new threshold or correction method is chosen from these results. The method was implemented and rejected for the current default; no 2014B or 2014J scoring occurred. Reproduce with `just probability-audit`; all fold results are in `outputs/probability_audit.csv`. This is an additional reliability experiment, preserving the intermediate techniques and investigations.

"""
    (ROOT / "docs/final_report.md").write_text(report)
    print("Final report generated from assessment-free outputs.")
