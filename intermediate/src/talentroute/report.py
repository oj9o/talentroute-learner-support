"""Generate the concise Intermediate report from current development artifacts."""
import json
import pandas as pd
from .data import ROOT

def report():
    out=ROOT/'outputs'
    def read(name):return pd.read_csv(out/name)
    def block(frame):return '```csv\n'+frame.to_csv(index=False,float_format='%.4f').strip()+'\n```\n'
    audit=json.loads((out/'data_audit.json').read_text());ci=json.loads((out/'validation_paired_interval.json').read_text())
    models=read('revision/model_comparison.csv');policy=read('validation_decision_metrics.csv');detector=read('validation_anomaly_proxy_metrics.csv')
    p=policy.set_index('policy');curve=read('investigations/learning_curve.csv');shift=read('investigations/period_shift.csv');single=read('investigations/single_feature.csv')
    learning=curve.groupby(['model','fraction','split'],as_index=False).adverse_ap.mean()
    top=single.iloc[0];h=learning[(learning.model=='hgb_15_10')&(learning.split=='validation')].set_index('fraction')
    text=f'''# TalentRoute: Intermediate evidence report

## Problem and decision
An educational consulting team serving universities must decide which learners receive an alert, human review or no action within limited staff time. TalentRoute uses information available at day 28 to prioritise that queue. OULAD is the evaluated learner population; corporate employee transfer and causal intervention benefit are not established.

The original recommender/uplift framing changed to classification plus engagement outlier detection because the available data support observed learner outcomes and engagement, not verified treatment benefits. The baseline, uncertainty analysis, same-budget comparisons and added-component go/no-go principle are retained. Scope and the three final commitments are in project_definition.md.

## Data and evaluation history
OULAD (Kuzilek, Hlosta & Zdrahal, 2015; doi:10.24432/C5KK69; CC BY 4.0) supplies real outcomes. Pass/Distinction map to Success; Fail and Withdrawn remain separate. From {audit['raw_enrolments']} raw enrolments, {audit['eligible_enrolments']} meet initial eligibility; {audit['purged_earlier_repeat_enrolments']} earlier records of later-partition students are purged. Training: {audit['split_counts']['train']} (2013B/J); validation: {audit['split_counts']['validation']} (2014B); final cohort: {audit['split_counts']['test']} (2014J). See outputs/data_audit.json.

This report and its pipeline evaluate development data. A separate frozen final candidate was already evaluated on 2014J before this update: it is no longer an unseen test. New diagnostics use training/validation only and cannot justify retuning against that observed test. Original Intermediate archives preserve the earlier chronology. Any later model change needs independent evidence for a confirmatory claim.

VLE aggregates stop at day 28. Non-banked, non-exam assessment submissions stop at day 21 under an assumed seven-day grading delay. Training-fitted imputation keeps missingness explicit. IDs, protected demographics and future outcomes are excluded from predictors. Eligibility, cutoff and identity-disjointness are tested. The data dictionary defines each variable and its availability assumption.

## What is actually implemented
Two technique families feed one policy: classification estimates three outcome probabilities; Isolation Forest maps unusual engagement to a training-reference percentile. Their weighted score ranks cases before staff-time allocation. Multiple classifiers are comparisons within one family, not extra technique families.

Executed classifier comparisons include logistic regression, a constrained Decision Tree, Random Forest, histogram gradient boosting and module-specific logistic models with global fallback. Logistic is the supervised baseline; inactivity is the detector baseline; early scores plus inactivity form the model-free decision baseline. Module eligibility is decided using training rows only.

Original settings: logistic C=1; boosting 140 iterations, learning rate 0.07, leaf/L2 candidates (7,2), (15,2), (15,10); Isolation Forest 150 trees and max_samples=512. Seed 7101. Tree/forest/specialist configurations are reproducible in revision.py. Historical selection maximized validation adverse PR-AUC; the blend search examined 0, 0.1, 0.2, 0.35 and 0.5. Later comparisons are exploratory.

## Metrics and results
Primary ML metric is adverse PR-AUC, measuring how well risk ranks later Fail/Withdrawn cases. Outcome-specific PR-AUC, macro-F1, log loss and Brier score describe discrimination and probability quality. Detector PR-AUC, flag precision and coverage measure relevance to recorded outcomes, not accuracy against nonexistent anomaly labels. Primary decision metric is adverse coverage at a fixed effort budget; precision and missed cases expose contact burden and omissions.

Classification comparison, outputs/revision/model_comparison.csv:
{block(models[['model','adverse_pr_auc','fail_pr_auc','withdrawn_pr_auc','macro_f1','log_loss','adverse_brier','adverse_coverage']])}
Same-budget decisions, outputs/validation_decision_metrics.csv:
{block(policy[policy.policy.isin(['business_rule','classifier_only','anomaly_rule','anomaly_only','coupled_selected'])][['policy','adverse_coverage','fail_coverage','withdrawn_coverage','flag_precision','human_n','alert_n','staff_minutes']])}
Detector comparison, outputs/validation_anomaly_proxy_metrics.csv:
{block(detector)}
The configured scenario allows 300 staff minutes per 100 learners, 30 per review and two per alert. Up to 20% of time is reserved for alerts, capped at 20% of learners. Reviews go to highest-ranked cases; alerts go to subsequent cases. These are configurable workload assumptions, not measured intervention costs. Either contact counts equally toward coverage.

The coupled candidate covers {p.loc['coupled_selected','adverse_coverage']:.2%}, versus {p.loc['classifier_only','adverse_coverage']:.2%} for classifier-only. Its paired student-cluster interval is [{ci['ci95'][0]:.4f}, {ci['ci95'][1]:.4f}] (validation_paired_interval.json). Because it crosses zero and follows validation selection, incremental benefit is unconfirmed. Keep the simpler classifier as the provisional operating reference. A working second component need not be a proven deployment improvement.

## EDA and Week 10 investigations
Ten figures cover outcomes, missingness, assessments, engagement, modules, detector disagreement and the budget frontier. Overview CSVs contain feature types, summary statistics, missing counts and sample development records without IDs. Missing scores are not zero; course differences are not individual ability.

![Development outcome balance](../outputs/eda_01_outcomes.png)
![Early assessment availability](../outputs/eda_07_observability.png)
![Engagement patterns](../outputs/eda_05_change.png)

The offline decision room offers three guided predict–investigate–decide cases using these saved model, detector and budget comparisons. Stakeholder prompts are illustrative, not real communications. The diagnostic investigations follow question → expected pattern → observed evidence → interpretation limit. Learning curves compare logistic/HGB at three training fractions over three seeds. HGB keeps early stopping disabled throughout this diagnostic to hold the iteration budget fixed. Its mean validation AP moves from {h.loc[.2,'adverse_ap']:.4f} to {h.loc[1.,'adverse_ap']:.4f}; this does not guarantee future data gains. Individual-feature probes rank {top.feature} highest at AP {top.adverse_ap:.4f}; predictive strength alone cannot establish leakage. A student-grouped period classifier gives mean ROC-AUC {shift.domain_roc_auc.mean():.4f}, suggesting detectable covariate differences, not proven concept drift. Source CSVs and fingerprints: outputs/investigations/; reproduce with just investigations.

Existing train/validation diagnostics, ten shuffled-training-label controls and grouped permutation checks remain in outputs/diagnostics/. They generate hypotheses, not proof of clean labels or absence of leakage. No outcome is relabeled because a model disagrees with it. The new studies are explicitly exploratory after the separate final evaluation.

## Deeper work and final commitments
1. Layer escape at equal total quota: test whether complementary warnings reach missed adverse cases. Completed development sweeps compare all 24 orders and three tie seeds; retain negative findings rather than crediting a larger union with a larger contact budget.
2. Warning-positive Success/Fail/Withdrawn profiles: compare descriptive trajectories/observed-score summaries, without claiming resilience causes or treatment effects.
3. Global versus module-specialist models: compare pooled predictions with training-only eligibility and flexible global models; course heterogeneity does not itself justify specialist deployment.

Ablation removes/swaps classifier, detector and rule under identical constraints. Sensitivity varies budget, review/alert effort, score availability and cutoff; seed checks assess stability. Outputs/revision/ and validation_sensitivity.csv record executed development analyses. These high-level commitments remain fixed; further refinement must respect the already-observed final-test boundary.

## Practical recommendation and limitations
Use an interpretable review queue with an explicit capacity setting; audit learners lacking early assessments and module slices with minimum sample guards. Human review is required. Risk estimates are not guarantees. Detection of unusual engagement is not a verified diagnosis of learner need.

This is a reproducible day-28 prototype, not a weekly live integration. OULAD has no randomized support interventions or measured staff costs. No prevented failures, retained value, ROI or employee benefit is estimated. One development validation period, course shift and uncertain score availability constrain generalization. The report is an Intermediate development account; separate final results must not be presented as newly untouched confirmation.

Run just install and just pipeline; use just app with a chosen budget. Current runtime/platform/test results are in outputs/current_pipeline_verification.json. Historical platform evidence verifies its named snapshot only. Week 10 inspiration: Saravanan Thirumuruganathan, Debugging ML Models. All learner outcomes are real; diagnostic expectations are interpretations rather than hidden synthetic answer keys.
'''
    (ROOT/'docs/baseline_report.md').write_text(text)
    (ROOT/'docs/development_findings.md').write_text('# Development evidence index\n\nThe canonical concise interpretation is in baseline_report.md.\n\n- Classification: outputs/revision/model_comparison.csv.\n- Same-budget policies: outputs/validation_decision_metrics.csv.\n- Added-component uncertainty: outputs/validation_paired_interval.json.\n- Detector proxy comparison: outputs/validation_anomaly_proxy_metrics.csv.\n- Layer quota, profiles and specialists: outputs/revision/.\n- Budget/timing sensitivity: outputs/validation_sensitivity.csv and outputs/validation_data_assumptions.csv.\n- Week 10 learning curves, single-feature probes and period differences: outputs/investigations/.\n\nThe new diagnostics are exploratory after a separate final evaluation, and do not select a replacement model.\n')
    print('Generated concise Intermediate report')
