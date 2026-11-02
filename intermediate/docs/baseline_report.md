# TalentRoute: Intermediate evidence report

## Decision and scope
An educational consulting team serving universities prioritises alerts and human reviews using information available at day 28. The assumed alternative is an early-score/inactivity queue, not a documented institutional workflow. Missed cases lose an opportunity for review; false warnings burden learners and staff.

The proposal's employee recommender/uplift became student classification plus engagement outlier detection: OULAD supports learner outcomes, not employee transfer or treatment benefits. Same-budget baselines, uncertainty and component go/no-go checks remain. Commitments and acceptance criteria: project_definition.md.

## Data and evaluation boundary
OULAD (Kuzilek, Hlosta & Zdrahal, 2015; doi:10.24432/C5KK69; CC BY 4.0) contains 32593 enrolments. Of 27515 initially eligible, 1959 earlier repeat-student records are purged. Train: 10412 (2013B/J); validation: 5934 (2014B); final cohort: 9210 (2014J). Purging ensures disjoint identities but changes the population and can disadvantage analysis of repeat learners.

A separate frozen candidate was already evaluated on 2014J. It is no longer unseen. Everything added here is development-only exploratory analysis; it neither selects a replacement nor reopens that test. Any changed final model needs independent evidence for confirmatory claims. Preserve the original frozen evaluation separately.

VLE ends at day 28; non-banked/non-exam submissions end at day 21 under an assumed seven-day score delay. Imputation uses training data only. IDs, demographics and future outcomes are excluded from predictors. Success combines Pass/Distinction; Fail and Withdrawn remain distinct. Among development records, 6 Withdrawn cases lack withdrawal dates, leaving day-28 eligibility uncertain; 3 have submissions but no score. No-submission flags are not missing-score flags.

## Connected methods
Classification estimates Success/Fail/Withdrawn probabilities; Isolation Forest supplies an engagement-rarity percentile. A weighted ranking feeds one staff-time policy. Five classifiers are comparisons within one family; classification and outlier detection are the two families.

Baselines: logistic classification, inactivity detection, and early-score/inactivity decision rule. First-pass comparisons include constrained tree, forest, histogram boosting and module-logistic specialists with training-only eligibility/global fallback. Settings: logistic C=1; boosting 140 iterations, learning rate .07, leaf/L2 candidates (7,2), (15,2), (15,10); detector 150 trees, max_samples=512; seed 7101. Historical validation search used adverse PR-AUC and blend weights 0/.1/.2/.35/.5. Exact configurations: revision.py.

## Metrics and results
Primary ML metric: average precision, reported as PR-AUC, for ranking adverse outcomes. Fail/Withdrawn AP, macro-F1, log loss and Brier assess distinct outcomes and probability quality. Detector AP/precision/coverage are outcome-relevance proxies, not accuracy against verified anomaly labels. Primary decision metric: adverse coverage at fixed effort; precision, missed cases and workload expose trade-offs.

Validation prevalence is 48.43%, the population no-skill AP reference. With 1700 contacts and 2874 adverse cases, perfect ranking could cover at most 59.15%, counting either action equally. This is a targeting ceiling, not achievable prevention.

Classification, outputs/revision/model_comparison.csv:
```csv
model,adverse_pr_auc,fail_pr_auc,withdrawn_pr_auc,macro_f1,log_loss,adverse_brier,adverse_coverage
logistic,0.7280,0.4870,0.2829,0.4001,0.9145,0.2076,0.4283
tree,0.7099,0.4650,0.2560,0.3965,0.9300,0.2114,0.4489
forest,0.7478,0.5022,0.2861,0.4115,0.9054,0.2025,0.4555
hgb_15_10,0.7472,0.4891,0.3072,0.4552,0.9021,0.2023,0.4579
module_logistic_hybrid,0.7369,0.4871,0.2807,0.4224,0.9122,0.2045,0.4475
```

Same-budget decisions, outputs/validation_decision_metrics.csv:
```csv
policy,adverse_coverage,fail_coverage,withdrawn_coverage,flag_precision,human_n,alert_n,staff_minutes
business_rule,0.4137,0.4336,0.3801,0.6994,514,1186,17792.0000
classifier_only,0.4579,0.4491,0.4728,0.7741,514,1186,17792.0000
anomaly_rule,0.3876,0.4241,0.3258,0.6553,514,1186,17792.0000
anomaly_only,0.3553,0.4042,0.2725,0.6006,514,1186,17792.0000
coupled_selected,0.4624,0.4679,0.4532,0.7818,514,1186,17792.0000
```

Detector proxies, outputs/validation_anomaly_proxy_metrics.csv:
```csv
detector,proxy_adverse_pr_auc,adverse_coverage,flag_precision,missed_adverse_n
isolation_forest,0.5899,0.3553,0.6006,1853
inactivity_rule,0.6300,0.3876,0.6553,1760
```

Classifier versus rule reaches 127 additional adverse cases: +4.42 percentage points (paired 95% interval 2.57–6.33). It clears the original development comparison, but selection makes this exploratory evidence, not independent confirmation. Source: diagnostics/classifier_minus_rule.json.

Isolation Forest loses to inactivity (AP 0.590 versus 0.630): unusual behaviour need not imply adverse outcomes. Blending covers 46.24% versus classifier 45.79%; difference interval [-0.0055, 0.0160] crosses zero. Added benefit is unconfirmed. Across seeds, gains range 0.07–0.45 percentage points (validation_seed_stability.csv); do not retune from this diagnostic.

Budget assumptions: 300 minutes/100 learners, 30/review, 2/alert; up to 20% of time reserved for alerts, capped at 20% of learners. Both actions count equally. This remains constrained ranking with a fixed action mix, not learned treatment allocation or measured benefit.

## EDA: observations that affect interpretation
CCC is absent from training but contributes 22.8% of validation: test unseen-course robustness rather than assume course-specific learning transfers. FFF's no-submission rate shifts from 14.7% to 70.2%; GGG's validation rate is 99.4%. Missingness can reflect assessment schedules, not disengagement. Overall 47.0% lack early scores. Keep missingness explicit and audit course/period slices.

![Development outcomes](../outputs/eda_01_outcomes.png)
![Submission availability by course and period](../outputs/eda_07_observability.png)
![Unequal-window engagement totals](../outputs/eda_05_change.png)

Ten saved figures and overview CSVs cover both families and the decision. Engagement windows are days 0–14 and 15–28 (15 versus 14 days): totals are not equal-duration trends.

## Three commitments: executed evidence and consequence
1. Layer escape: equal-quota round-robin covers 41.89% versus classifier 45.79%. Extra layers do not automatically help; retain the single ranking as reference. Sources: revision/same_quota_layers.csv; layer_quota_sensitivity.csv tests 24 orders/three tie seeds.
2. Warning profiles: under historical four-layer selection, 496 flagged learners succeeded; observed-score medians are 62 (Success), 48 (Fail), 40 (Withdrawn), with observed counts 277/262/208. Source: revision/warning_outcome_profiles.csv. Treat warnings as review prompts; these static profiles establish neither resilience mechanisms nor intervention effects.
3. Course specialists: hybrid AP 0.737 versus logistic 0.728, boosting 0.747. Specialisation is not automatically better; retain global fallback for unsupported courses. Sources: revision/model_comparison.csv, specialist_eligibility.csv, model_segments.csv.

A critical segment audit: classifier selects zero of GGG's 315 adverse cases; blend reaches 21.3%. Female/male adverse coverage is 34.0%/53.9%. These descriptive validation gaps require course-aware review before deployment; they neither prove discrimination nor justify retuning on the final test. Source: validation_challenge_segments.csv. Aggregate improvement alone is insufficient.

## Debugging, ablation and final path
Learning curves, single-feature probes, grouped permutation and shuffled-training-label controls are development diagnostics, not proof against leakage. HGB learning-curve AP moves 0.731→0.745; period-classifier ROC-AUC 0.791 signals covariate differences, not proven concept drift. Sources: outputs/investigations/ and diagnostics/; reproduce with just investigations.

Ablation removes/swaps classifier, detector and rule at equal effort. Executed sensitivity varies budget, action costs, availability delay/cutoff and seeds (validation_sensitivity.csv, validation_data_assumptions.csv). The three commitments stay fixed; final writing must explain their decision consequences, not promise universal improvement.

Keep classifier-only as a provisional analytical reference, not a deployable recommendation. A stakeholder pilot additionally needs an agreed practical gain, segment review, real workload checks and intervention evidence. No prevented failures, ROI, weekly integration or employee benefit is established. Reproduce: just install; just pipeline. Evidence provenance: outputs/development_evidence.json. Historical platform checks apply only to their recorded snapshots.
