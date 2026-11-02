# TalentRoute: early learner-support triage

## Problem, decision and scope change
At day 28, an educational consulting team supporting a university or learning provider must prioritise eligible enrolments for an alert, human review or no action within limited staff time. The assumed alternative is a simple early-score/inactivity queue, not an observed university workflow. Missing an adverse case leaves it without a warning; false warnings consume time and burden successful learners.

The proposal’s employee-training recommender and score-derived uplift are replaced by student risk classification plus engagement outlier detection. OULAD records students, not employees or randomized interventions. This change aligns the question with the data and addresses the instructor’s population, recommender and circular-evaluation concerns. The consulting context includes university learners directly; employee transfer would require new data and validation. Model-free comparison, uncertainty, same-budget policies and an added-component go/no-go principle are retained.

## Data and connected system
Use real public OULAD enrolments, 2013–2014. Eligible students registered by day 28 and had not withdrawn by then. Success combines Pass/Distinction; Fail and Withdrawn remain separate outcomes. VLE features use days 0–28. Assessment features use non-banked, non-exam submissions by day 21: seven-day grading availability is an assumption, not an observed timestamp. Missing scores are imputed using training statistics with missing indicators. IDs and protected demographics are excluded from predictors; demographics support aggregate audits.

Train: 2013B/J; validation: 2014B; final evaluation cohort: 2014J. Purge earlier enrolments of later-partition students for identity-disjoint splits, sacrificing development observations. Counts are reported. The original candidate was selected on validation. A separate frozen final candidate was subsequently evaluated on 2014J before this updated Intermediate was prepared; that cohort is no longer an unseen test. New diagnostics use development rows only. Course shift, missing assessments, repeated-student exclusion and one validation period restrict generalization.

Workflow: OULAD → eligibility/features → classifier and detector → budgeted queue → held-out outcome evaluation. See system_diagram.md. Logistic is the supervised baseline; histogram boosting is the original candidate family. Isolation Forest learns unusual engagement without anomaly labels, with module context; inactivity is its simple baseline. Classifier-only, detector-only and coupled policies share the same decision rule. The model-free decision baseline combines early scores and inactivity.

## Decision assumptions
Configuration specifies 300 staff minutes per 100 learners, 30 minutes per review and two per alert. These approximate a longer review and brief contact, not measured costs. Reserve up to 20% of time for alerts, capped at 20% of learners; reviews go to highest-ranked cases and alerts to subsequent cases. Report actual and unused minutes. Coverage counts either action equally: this is targeting under an assumed mix, not learned treatment allocation or estimated prevention.

## Evaluation and acceptance
Primary ML metric: adverse average precision (reported as PR-AUC), measuring how well a limited review queue prioritises adverse cases; compare with outcome prevalence. Also report separate Fail/Withdrawn PR-AUC, macro-F1, log loss and Brier score. Primary decision metric: adverse coverage at fixed effort; flag precision measures contact relevance. Report outcome-specific coverage, missed cases and workload. Detector PR-AUC/coverage/precision use adverse outcomes as relevance proxies, not verified anomaly labels.

A validation-selected blend is an exploratory candidate, not an operational endorsement. Current provisional reference is classifier-only because added-detector improvement is unconfirmed. Validation intervals reflect selection and are exploratory.

The separate final implementation recorded a candidate, costs, budget, tie rule, metrics and acceptance criteria before scoring 2014J. This Intermediate presents development evidence and does not reset that history. Proposed analytical success: a paired student-cluster 95% coverage-difference lower bound above zero against the model-free reference. Adding the detector also requires improvement over classifier-only and no greater than two percentage-point precision loss. This margin is an analyst assumption with no measured intervention-effect interpretation. These describe the original development criteria; the separate final record documents its exact specification. A zero-crossing interval is inconclusive. For a stakeholder pilot, also propose at least 100 additional adverse cases reached at the current validation cohort size and fixed effort; this is an analyst-proposed practical threshold, not retrospectively confirmed acceptance. Deployment additionally needs stakeholder agreement, a segment audit and intervention evidence.

## Final commitments and constraints
Three deeper analyses, adopted after original validation:
1. Cross-model reconciliation through layer escape under one total quota: do complementary signals reach missed adverse cases?
2. Challenge-set evaluation of warning-positive Success/Fail/Withdrawn profiles: descriptive contrasts, not resilience mechanisms.
3. Segment-specific analysis of module-specialist versus global logistic and flexible ensembles: does course-specific complexity help?

Ablate rule/logistic/classifier/detector/combined policies under identical constraints. Vary budget, action costs, blend weights, score availability and cutoff; repeat detector seeds. Frontier/uncertainty remain sensitivity checks. Historical warning-profile diagnostics are labelled separately from the recommended policy. Weekly survival and corporate/causal validation are outside scope. These high-level techniques and analyses are final commitments.

CPU-only execution needs no credentials/GPU. Privacy, interpretable human review, missing information and course shift constrain use. Aggregate releases exclude student IDs and row-level predictions. This Intermediate supplies a working development system and plan, not a deployment approval. Any future model change would require new independent evidence for a confirmatory claim.

## Week 10 investigation extension
Classification comparisons include logistic regression, decision tree, forest, boosting and module-specific logistic. Logistic anchors a simple baseline; trees/boosting test nonlinear patterns, forest tests averaging, and module specialists test course heterogeneity. Isolation Forest supplies the second technique family and feeds the coupled ranking. Week 10 diagnostic experiments explain model behavior; they do not count as extra technique families, change the three commitments or select a new final model.
