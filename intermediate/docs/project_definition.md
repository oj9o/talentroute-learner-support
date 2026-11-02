# TalentRoute: early learner-support triage

## Business problem and scope
An educational consulting team serving universities must decide which eligible learners receive an alert, human review or no action at day 28. The assumed current alternative is a simple early-score/inactivity queue, not a documented university workflow. Missed cases lose an opportunity for support; unnecessary warnings consume time and can burden learners. A better queue reaches more later adverse cases at the same staff effort, with subgroup omissions visible.

The employee recommender/uplift proposal became student classification plus engagement outlier detection. OULAD describes university learners, which our consulting context includes directly; it does not establish employee transfer or intervention benefits. This resolves the population/recommender mismatch and circular score-derived benefit evaluation. Credible baselines, uncertainty, equal-budget comparisons and a component go/no-go rule are retained.

## Data and connected techniques
Use real public OULAD, 2013–2014, CC BY 4.0. One row is a student/module/presentation enrolment. Students must be registered and not known to have withdrawn by day 28. Pass/Distinction become Success; Fail and Withdrawn remain distinct. VLE features stop at day 28; non-banked/non-exam submissions stop at day 21 under a configurable seven-day score-availability assumption. Submission time is not grading time. Unknown scores remain missing until training-fitted imputation. IDs, demographics and future outcomes are excluded from predictors; aggregate demographic audits use minimum-sample guards.

Classification estimates three outcome probabilities. Logistic is the baseline; tree/forest/boosting comparisons test nonlinear structure. Training-eligible module-logistic specialists test whether course differences justify complexity, with global fallback. Isolation Forest models unusual engagement without anomaly labels; inactivity is its baseline. A weighted risk/rarity score feeds the same budgeted queue. These are two connected technique families, not five families. Diagram: system_diagram.md.

## Decision assumptions
Configuration sets staff minutes per 100 learners, review/alert effort, alert time share and learner cap. The reference values are 300, 30, 2, 20% and 20%, respectively: illustrative workload assumptions, not measured costs. Highest ranks receive reviews, subsequent ranks alerts. Both contacts count equally toward coverage; report actual/unused minutes. This is constrained ranking with an assumed action mix, not optimal treatment allocation. Sensitivity and hypothetical break-even scenarios test these assumptions without claiming causal value.

## Evaluation and success
Train: 2013B/J; validation: 2014B; final cohort: 2014J. Earlier enrolments of later-partition students are purged to prevent identity overlap, sacrificing observations and potentially changing the repeat-learner population. Preprocessing/detector references fit training only.

Primary ML metric: adverse average precision (reported as PR-AUC), suited to ranking a limited contact queue. Compare against prevalence; also report Fail/Withdrawn AP, macro-F1, log loss and Brier. Detector AP/precision/coverage measure adverse-outcome relevance, not verified anomaly accuracy. Primary decision metric: adverse coverage at fixed effort, alongside precision, missed cases, outcome-specific coverage and workload.

Original analytical success requires a paired student-cluster coverage-difference interval above zero versus the model-free rule. Adding the detector additionally needs improvement over classifier-only and no greater than two percentage-point precision loss; the margin is an analyst assumption. Validation selection makes these exploratory criteria, not deployment approval. Practical pilot thresholds require stakeholder agreement before a new independent assessment; no post-hoc threshold is presented as a passed gate.

## Three final commitments
1. Cross-model reconciliation: measure escaped adverse cases under one total quota, including who gains/loses by course; do not credit a larger warning union with a larger budget.
2. Challenge-set evaluation: compare warning-positive Success/Fail/Withdrawn profiles under the reference policy, retaining observed-score denominators; no resilience mechanism or treatment-effect claim.
3. Segment-specific analysis: evaluate module specialists versus global logistic and flexible models, including per-course metrics, training-only eligibility and fallback.

Ablation removes/swaps classifier, detector and rule at equal effort. Sensitivity varies budget, action costs, blend weights, score delay/cutoff; seed checks assess stability. Negative findings can sharpen the recommendation; more models alone do not justify complexity.

## Boundaries and final-test history
A separate frozen Final candidate already used 2014J before this revision. It is no longer unseen. All new analyses remain development-only and cannot select a replacement using that observed test. Preserve the original frozen record; a changed model needs genuinely independent evidence for confirmation. High-level techniques and the three commitments stay fixed.

CPU-only Python 3.14 execution needs no GPU, credentials or LLM API. Missing dates/scores, course shift, data age and one validation period limit generalisation. Human review, privacy and explainability matter; no live weekly integration, expert label audit, prevented failures, ROI or production approval is established.
