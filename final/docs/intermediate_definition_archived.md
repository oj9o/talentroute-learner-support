# TalentRoute: early learner-support triage

## Business problem and scope
An educational consulting team serving universities prioritises eligible learners for review, alert or no action at day 28. The assumed alternative is an early-score/inactivity queue, not an observed university workflow. Missed cases lose support opportunities; false warnings consume staff time. Better targeting must expose subgroup omissions.

The employee recommender/uplift proposal became student classification plus engagement outlier detection. OULAD describes university learners, which our consulting context includes directly; it does not establish employee transfer or intervention benefits. This resolves the population/recommender mismatch and circular score-derived benefit evaluation. Credible baselines, uncertainty, equal-budget comparisons and a component go/no-go rule are retained.

## Data and connected techniques
Use real public OULAD, 2013–2014, CC BY 4.0. One row is a student/module/presentation enrolment. Students must be registered and not known to have withdrawn by day 28. Pass/Distinction become Success; Fail and Withdrawn remain distinct. VLE features stop at day 28; non-banked/non-exam submissions stop at day 21 under a configurable seven-day score-availability assumption. Submission time is not grading time. Unknown scores remain missing until training-fitted imputation. IDs, demographics and future outcomes are excluded from predictors; aggregate demographic audits use minimum-sample guards.

Classification estimates three outcome probabilities. Logistic is the baseline; tree/forest/boosting and training-eligible module specialists test complexity, with global fallback. Isolation Forest models unusual engagement without anomaly labels; inactivity is its baseline. A risk/rarity blend is tested in ablation under the same budget; classifier-only remains the provisional reference because detector benefit is unconfirmed. Pattern Mining is not added. These are two connected technique families, not five families. Diagram: system_diagram.md.

## Decision assumptions
Reference budget: 300 staff minutes/100 eligible learners, 30/review, 2/alert. Reserve the smaller of 20% of minutes or enough for alerts to 20% of learners. Highest ranks receive reviews from the remaining budget; later ranks receive alerts, limited to 20% of learners and remaining minutes. Integer rounding can shift the minute share slightly. The 20% learner cap applies to alerts, not all contacts. Coverage counts each selected learner once. These are configurable workload assumptions, not measured costs or optimal treatment allocation.

## Evaluation and success
Train: 2013B/J; validation: 2014B; final cohort: 2014J. Earlier enrolments of later-partition students are purged to prevent identity overlap, sacrificing observations and potentially changing the repeat-learner population. Preprocessing/detector references fit training only.

Primary ML metric: adverse average precision (reported as PR-AUC), suited to ranking a limited contact queue. Compare against prevalence; also report Fail/Withdrawn AP, macro-F1, log loss and Brier. Detector AP/precision/coverage measure outcome relevance, not verified anomaly accuracy. Adverse means later Fail or Withdrawn; ranking scores are never reused as outcomes. Primary decision metric: adverse coverage at fixed effort, alongside precision, missed cases, outcome-specific coverage and workload.

Original analytical success requires a paired student-cluster coverage-difference interval above zero versus the model-free rule. The detector additionally needs improvement over classifier-only and at most two percentage-point precision loss (assumed margin). It does not clear this gate: it loses to inactivity and the blend interval crosses zero. Validation selection makes these exploratory criteria, not deployment approval. Practical pilot thresholds require stakeholder agreement before a new independent assessment; no post-hoc threshold is presented as a passed gate.

## Three final commitments
Scope change: equal-quota reconciliation, warning profiles and course segments replace the proposal's uncertainty/frontier framing. Intervals and seeds remain checks; budget/action sensitivity replaces recommendation-strength/uplift scenarios, unsupported by OULAD.
1. Cross-model reconciliation: measure escaped adverse cases under one total quota, including who gains/loses by course; do not credit a larger warning union with a larger budget.
2. Challenge-set evaluation: compare warning-positive Success/Fail/Withdrawn profiles under the reference policy, retaining observed-score denominators; no resilience mechanism or treatment-effect claim.
3. Segment-specific analysis: evaluate module specialists versus global logistic and flexible models, including per-course metrics, training-only eligibility and fallback.

Ablation compares classifier, detector and rule at equal effort. Sensitivity varies budget, costs, weights and availability; seeds check stability. Negative findings do not justify complexity.

## Boundaries and final-test history
A separate frozen Final candidate already used 2014J before this revision. It is no longer unseen. All new analyses remain development-only and cannot select a replacement using that observed test. Preserve the original frozen record; a changed model needs genuinely independent evidence for confirmation. High-level techniques and the three commitments stay fixed.

Python 3.14 is CPU-only. Missingness, course shift, old data and one validation period limit generalisation. No live integration, intervention benefit or production approval is established.
