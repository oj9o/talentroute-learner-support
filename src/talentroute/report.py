"""Generate concise intermediate evidence directly from produced files."""
import json
import platform
from .data import ROOT, config
import pandas as pd

def report():
    out=ROOT/'outputs';audit=json.loads((out/'data_audit.json').read_text(encoding='utf-8'));sel=json.loads((out/'development_selection.json').read_text(encoding='utf-8'));metrics=pd.read_csv(out/'validation_decision_metrics.csv');ml=pd.read_csv(out/'validation_model_search.csv');ci=json.loads((out/'validation_paired_interval.json').read_text(encoding='utf-8'))
    linux_record=ROOT/'evidence/platform-validation-2026-10-31/linux_verification.json'
    linux_ok=linux_record.exists() and json.loads(linux_record.read_text(encoding='utf-8')).get('pipeline_exit_code')==0
    linux_status='A historical Ubuntu VM run is saved under evidence/platform-validation-2026-10-31; it does not verify later code changes or container execution.' if linux_ok else 'Linux execution remains unverified.'
    anomaly=pd.read_csv(out/'validation_anomaly_proxy_metrics.csv').set_index('detector')
    detector_sentence=f"Proxy adverse PR-AUC: inactivity {anomaly.loc['inactivity_rule','proxy_adverse_pr_auc']:.4f}, Isolation Forest {anomaly.loc['isolation_forest','proxy_adverse_pr_auc']:.4f}."
    blend_sentence=('The interval includes zero: improvement is inconclusive.' if ci['ci95'][0]<=0<=ci['ci95'][1] else 'The interval excludes zero; its sign and outcome tradeoffs must still be interpreted as exploratory.')
    platform_note=('Historical platform comparisons are retained in evidence/platform-validation-2026-10-31/platform_comparison.csv; they concern an earlier code snapshot, not the current regeneration.' if (ROOT/'evidence/platform-validation-2026-10-31/platform_comparison.csv').exists() else 'No historical cross-platform comparison is supplied in this package.')
    def csvblock(frame): return '```csv\n'+frame.to_csv(index=False,float_format='%.4f').strip()+'\n```'
    text=f'''# Intermediate baseline and first-pass report

## Decision and changed framing
TalentRoute supports early learner-support triage under a finite staff-time budget. The observed population is distance-learning students. Corporate employee claims and score-derived causal uplift have been removed. Classification and outlier detection feed the same action policy. See project_definition.md for the current scope; later revisions are explicitly labeled.

## Data and partitions
Source: OULAD, Kuzilek, Hlosta & Zdrahal (2015), UCI doi:10.24432/C5KK69, CC BY 4.0. Download URL/checksum is recorded in data/raw/manifest.json. Decision time is day {audit['cutoff_day']}. Seven-day score availability is an assumption requiring sensitivity analysis, not observed marking time. No protected demographics are model inputs.

Data audit (outputs/data_audit.json): {audit['raw_enrolments']} raw enrolments, {audit['eligible_enrolments']} eligible before group purging, {audit['purged_earlier_repeat_enrolments']} earlier repeated-student enrolments removed. Retained partitions: training {audit['split_counts']['train']}, validation {audit['split_counts']['validation']}, reserved test {audit['split_counts']['test']}. Training uses 2013, validation 2014B and reserved final test 2014J. No final test performance was computed. Outcome counts and assessment availability are in development_target_counts.csv and development_coverage.csv.

## Models and tuning
Logistic regression is the supervised baseline. Histogram boosting candidates use a small search specified in the original development code. Model selection maximizes validation adverse-outcome PR-AUC. Selected model: {sel['selected_model']}. Isolation Forest uses engagement features plus module context, fitted on training data; its score is mapped through the training score distribution. The rule baseline combines poor early scores and inactivity.

Settings: logistic C=1, max_iter=1500; boosting max_iter=140, learning_rate=0.07, leaf/L2 candidates (7,2), (15,2), (15,10); Isolation Forest 150 trees, max_samples=512. Seed: {config()['seed']}. Numeric preprocessing uses training medians with missing indicators and scaling; module uses one-hot encoding. Revision tree/forest/hybrid settings are recorded in src/talentroute/revision.py.

Validation model metrics (outputs/validation_model_search.csv):
{csvblock(ml[['model','adverse_pr_auc','fail_pr_auc','withdrawn_pr_auc','macro_f1','adverse_brier']])}

## Decision results and ablation
All policies use the same eligible validation cohort, actions, effort budget and alert cap. Coverage measures later adverse outcomes flagged, not intervention effectiveness. Human and alert effort are explicit scenario assumptions in configs/policy.json. The validation-search candidate has anomaly weight {sel['selected_weight']}; it remains an experimental comparison, not the recommended operating policy. The provisional operating reference uses weight zero (classifier-only) pending final specification; candidate evidence and uncertainty are reported below. The action mix is a declared workload rule: reviews go to the highest-ranked cases and alerts to the next cases. It does not learn treatment choice; either action counts equally toward coverage.

Validation decisions (outputs/validation_decision_metrics.csv):
{csvblock(metrics[['policy','adverse_coverage','fail_coverage','withdrawn_coverage','flag_precision','human_n','alert_n','staff_minutes']])}

Paired fixed-action student-cluster bootstrap 95% interval for selected coupled minus classifier-only coverage: [{ci['ci95'][0]:.4f}, {ci['ci95'][1]:.4f}] (outputs/validation_paired_interval.json). These validation-selected intervals are exploratory and not independent confirmation. The final added-component gate has not been evaluated on the reserved test.

## Does the second component earn its complexity?
{csvblock(pd.read_csv(out/'validation_anomaly_proxy_metrics.csv')[['detector','proxy_adverse_pr_auc','adverse_coverage','flag_precision']])}
These are outcome-relevance proxies, not verified anomaly labels. {detector_sentence} {blend_sentence} Separate Fail/Withdrawn changes are reported in development_findings.md. Keep the simpler classifier as provisional operational reference; report the second component and negative evidence rather than forcing deployment.

## EDA and interpretation
Nine development EDA/model figures cover outcomes, missingness, engagement, scores, modules and detector disagreement; one frontier covers the decision. eda_feature_types.csv, eda_numeric_summary.csv, eda_missing_counts.csv and eda_sample_records.csv supply overview tables and five illustrative records without IDs. Missing scores are not zero; module differences are not individual ability.

![Development outcome balance](../outputs/eda_01_outcomes.png)
![Observable assessment coverage](../outputs/eda_07_observability.png)
![Engagement patterns](../outputs/eda_05_change.png)

## Sensitivity and deeper analyses
Executed development analyses write validation_sensitivity.csv, validation_uncertainty_analysis.csv, validation_challenge_segments.csv and validation_seed_stability.csv. The frontier plot shows coverage under changing staff budgets. These support sensitivity/ablation; the three committed deeper analyses are layer escape, warning-positive outcome profiles and general-versus-specialist models, as defined in project_definition.md. Numerical findings and operational recommendations are recorded in development_findings.md. Their hypotheses need independent final-test confirmation.

## Portability and limitations
Tables and figures in this generated report come from {platform.system()} / Python {platform.python_version()}. {platform_note} Neither platform is claimed bit-identical to the other. Comparisons within this report use one platform consistently.

OULAD contains no randomized interventions or measured staff effort. We cannot claim prevented failures, retained students, ROI or transfer to employees. Anomaly relevance uses outcome proxies, not verified anomaly labels. Seven-day marking availability, day-28 cutoff, module shift and missing early assessment coverage require scrutiny. Bootstrap intervals do not capture all temporal drift. Seed stability covers the outlier layer only. Mac execution is tested separately. {linux_status}

Final plan: freeze candidate/settings, execute reserved test once, retain negative evidence and verify clean Mac/Linux operation. Three analytical commitments and sensitivity designs are in project_definition.md. This Intermediate is not the final report.
'''
    # Integrate current revision evidence into the canonical generated report.
    rev = out/'revision'
    if (rev/'forest_minus_hgb_intervals.csv').exists():
        comparison = pd.read_csv(rev/'model_comparison.csv')
        intervals = pd.read_csv(rev/'forest_minus_hgb_intervals.csv')
        layers = pd.read_csv(rev/'layer_quota_sensitivity.csv')
        text += "\n## Exploratory revision after instructor feedback\n"
        text += "These candidates and checks were added after viewing original validation results; they are exploratory, not confirmatory. Original model/policy files remain the historical reference. Final-test metrics remain unused.\n\n"
        text += csvblock(comparison[['model','adverse_pr_auc','fail_pr_auc','withdrawn_pr_auc','adverse_coverage']])
        text += "\nPaired student-cluster bootstrap, forest minus historical hgb, conditional on the fitted models and validation selection:\n"
        text += csvblock(intervals[['metric','ci95_lower','ci95_upper','valid_repeats']])
        text += "\nThree unadjusted exploratory intervals do not establish confirmatory superiority or equivalence. PR-AUC remains the selection metric; historical hgb is retained pending final specification. Specialists are also compared with flexible global models.\n"
        summary = layers.groupby('classifier_first_share').adverse_coverage.agg(['min','max']).reset_index()
        text += "\nSame-total-quota layer diagnostics across all 24 orders and three tie seeds:\n"+csvblock(summary)
        text += "\nQuota conclusions apply only to tested designs. outputs/revision/ contains ties, overlap, outcome-specific escape and historical profiles; selection-related profiles do not identify resilience mechanisms.\n"
        text += "\nAction allocation remains a scenario, not measured benefit: action_break_even.csv uses observed adverse cases for evaluation after ranking without labels, varying alert caps with near-full budget expenditure and a reference operating mix. Comparing caps changes an operational constraint. Hypothetical effectiveness multipliers do not establish causal intervention effects or optimal allocation.\n"
        text += "\nUncertainty/frontier are sensitivity analyses; project_definition.md contains the single current list of three deeper analyses. Current-run verification is reported in outputs/current_pipeline_verification.json; historical VM evidence is separate under evidence/; the reserved final test is unused.\n"
    profiles=pd.read_csv(rev/'warning_outcome_profiles.csv')
    flagged=profiles[profiles.flagged.astype(str).str.lower()=='true']
    inactivity=flagged[flagged.feature=='inactive_days'].set_index('outcome')
    scores=flagged[flagged.feature=='score_mean'].set_index('outcome')
    text+='\n## Three analytical findings and limits\n'
    reference=float(metrics.set_index('policy').loc['classifier_only','adverse_coverage'])
    mixed=layers.loc[layers.classifier_first_share<1,'adverse_coverage']
    text+=f"Layer quotas: tested mixed-design pooled coverage ranged {mixed.min():.4f}–{mixed.max():.4f}, versus classifier-only {reference:.4f}. These are exploratory quota-specific results, not a conclusion about layered detection generally.\n"
    profile_rows=[]
    for outcome in ['Success','Fail','Withdrawn']:
        if outcome in inactivity.index and outcome in scores.index:
            profile_rows.append(f"{outcome}: median inactivity {inactivity.loc[outcome,'median']:g} days, median score {scores.loc[outcome,'median']:g} from {int(scores.loc[outcome,'observed_n'])} observed scores")
        else:profile_rows.append(f"{outcome}: profile unavailable or suppressed by minimum-n guard")
    text+='Within the historical four-signal flagged set: '+'; '.join(profile_rows)+'. Selection uses these features; these are descriptive profiles, not resilience causes or treatment effects.\n'
    by_model=comparison.set_index('model').adverse_pr_auc
    text+=f"Pooled PR-AUC: global logistic {by_model['logistic']:.4f}, specialist hybrid {by_model['module_logistic_hybrid']:.4f}, forest {by_model['forest']:.4f}, historical boosting {by_model['hgb_15_10']:.4f}. Training eligibility and pooled probability comparability constrain interpretation.\n"
    diag=out/'diagnostics'
    check=json.loads((diag/'classifier_minus_rule.json').read_text(encoding='utf-8'))
    null=pd.read_csv(diag/'shuffled_training_labels.csv')
    ladder=pd.read_csv(diag/'train_validation_metrics.csv')
    ties=pd.read_csv(rev/'tie_sensitivity.csv');ties=ties[ties.score=='business_rule']
    tie_min,tie_max=ties.adverse_coverage.min(),ties.adverse_coverage.max()
    rule_coverage=float(metrics.set_index('policy').loc['business_rule','adverse_coverage'])
    text+='\n## Model diagnostics\n'
    text+=f"Classifier-only reaches {check['extra_adverse_cases_flagged']} additional adverse cases of {check['adverse_cases']} versus the rule at the same workload; coverage difference {check['coverage_difference']:.4f}, exploratory paired interval [{check['ci95'][0]:.4f}, {check['ci95'][1]:.4f}]. Historical rule ties remain unchanged; seeded tie checks gave {tie_min:.4f}–{tie_max:.4f} coverage versus historical {rule_coverage:.4f}.\n"
    text+=csvblock(ladder[['model','split','adverse_pr_auc','log_loss']])+'\n'
    text+=f"Ten shuffled-training-label controls produced validation ROC-AUC {null.adverse_roc_auc.min():.3f}–{null.adverse_roc_auc.max():.3f} (random-ranking reference 0.5). Randomly fitted scores can rank validation cases inversely, so a value below 0.5 alone is not evidence of leakage. This limited negative control cannot certify absence of leakage. Grouped permutation diagnostics and a code/config/data fingerprint are in outputs/diagnostics/. Correlated feature groups move together; predictive reliance is not causality. No expert ceiling, production performance or manually verified label-error rate is available. Performance remains limited: many later adverse outcomes are missed and missing assessments restrict early information.\n"
    missed=pd.read_csv(out/'missed_case_profile.csv')
    missing=missed[missed.segment=='no_early_assessment']
    text+='\n## What the observed errors imply\n'
    text+=csvblock(missing[['group','n','adverse_n','flagged_adverse_n','missed_adverse_n','coverage']])+'\n'
    text+='Group 1 lacks an observable early assessment; group 0 has one. Compare counts and coverage together: differences are descriptive, not proof that missing scores cause an error. Missingness motivates checking the engagement-only pathway, not assigning a zero score. Module slices in missed_case_profile.csv locate uneven targeting; interpret only rows passing the minimum-n guard. These slices do not establish discrimination or a correct intervention.\n'
    text+='The historical classifier improves targeting over the rule at identical effort, yet many adverse cases remain missed. Added detector complexity has no confirmed benefit in the paired interval. The detector/risk scatter illustrates disagreement; disagreement alone does not establish useful complementarity. Specialist comparisons test course heterogeneity without establishing specialist deployment superiority.\n'
    text+='\n## Final execution plan (not completed test results)\n'
    text+='1. Before opening 2014J, record a dated final specification: predictor availability, one candidate, action mix/costs, tie rule, primary metrics and acceptance criteria. Retain the current model-free and classifier-only references.\n'
    text+='2. Complete the three commitments on the frozen design: layer escape at equal quota, warning-positive outcome profiles with observed-score denominators, and global-versus-specialist comparison with training-only eligibility. Retain budget/cost/cutoff sensitivities as separate scenario analyses. Report negative findings and outcome tradeoffs.\n'
    text+='3. Only after freezing, evaluate reserved 2014J once using the same metrics and student-cluster intervals. Do not tune or repair the acceptance rule using that test. Report cohort shift and errors, verify an extracted release in the grading environment, and explain each conclusion using saved evidence.\n'
    (ROOT/'docs/baseline_report.md').write_text(text, encoding='utf-8')
    sensitivity=pd.read_csv(out/'validation_sensitivity.csv');u=pd.read_csv(out/'validation_uncertainty_analysis.csv');segments=pd.read_csv(out/'validation_challenge_segments.csv')
    findings='# Development findings — not final-test claims\n\n'
    for name in ['business_rule','classifier_only','coupled_selected','coupled_fixed_020']:
        r=metrics[metrics.policy==name].iloc[0];findings+=f"- {name}: adverse coverage {r.adverse_coverage:.4f}; flag precision {r.flag_precision:.4f}. Source: validation_decision_metrics.csv.\n"
    f=sensitivity[(sensitivity.assumption=='staff_minutes_per_100')&(sensitivity.policy=='coupled_selected')]
    findings+='\n## Frontier\n'+csvblock(f[['value','adverse_coverage','flag_precision','staff_minutes']])+'\nRecommendation: increasing capacity increases the number flagged; select an operating point only if added workload and marginal relevance are acceptable. This is not an estimate of prevented outcomes.\n'
    findings+='\n## Uncertainty\n'+csvblock(u[['policy','adverse_coverage','flag_precision']])+'\nRecommendation: retain uncertainty prioritization only if it earns a validation benefit and survives final confirmation; entropy is not calibrated epistemic uncertainty.\n'
    c=segments[(segments.segment=='no_early_assessment')&(segments.policy=='coupled_selected')]
    findings+='\n## Challenge set\n'+csvblock(c[['group','n','adverse_coverage','fail_coverage','withdrawn_coverage','flag_precision']])+'\nRecommendation: audit the no-assessment pathway before deploying an assessment-led policy. Differences are descriptive and do not establish discrimination or causality.\n'
    findings+='\n## Added-layer recommendation\n'+('The selected outlier weight is zero: recommend the simpler classifier-only operating policy for now. Keep the outlier analysis and negative ablation result visible; do not add complexity to satisfy a preferred story.' if sel['selected_weight']==0 else 'The validation search retained a nonzero outlier contribution, but the paired interval must exclude zero before asserting evidence of improvement. Prefer the simpler policy operationally while this remains unconfirmed. Check the separate Fail/Withdrawn tradeoff, not just the pooled coverage.')+'\n'
    trade=metrics.set_index('policy')
    delta=trade.loc['coupled_selected',['fail_coverage','withdrawn_coverage']]-trade.loc['classifier_only',['fail_coverage','withdrawn_coverage']]
    findings+='\nOutcome-specific coverage changes from adding the selected anomaly blend: '+str(delta.to_dict())+'. Source: validation_decision_metrics.csv. An aggregate improvement can conceal deterioration for one outcome; stakeholder priorities must be declared before final testing.\n'
    if (out/'validation_data_assumptions.csv').exists():
        assumptions=pd.read_csv(out/'validation_data_assumptions.csv')
        findings+='\n## Availability assumptions\n'+csvblock(assumptions[['cutoff_day','score_delay_days_assumed','model','n','no_assessment_rate','adverse_coverage']])+'\nCompare policies within each scenario: changing the cutoff changes both information and eligibility. No raw cross-scenario gain is treated as causal or pure model improvement.\n'
    anomaly=pd.read_csv(out/'validation_anomaly_proxy_metrics.csv')
    findings+='\n## Strong detector baseline\n'+csvblock(anomaly[['detector','proxy_adverse_pr_auc','adverse_coverage','flag_precision']])+'\nIn this run: '+detector_sentence+' Do not deploy the complex detector merely because it is more sophisticated. Investigate score direction and module/observability shift before a final candidate is frozen. Outcome relevance is not verified anomaly ground truth.\n'
    if (out/'validation_layer_overlap.csv').exists():
        overlap=pd.read_csv(out/'validation_layer_overlap.csv')
        findings+='\n## Swiss Cheese escape diagnostic\n'+csvblock(overlap[['outcome','n','both_flag','classifier_only_flag','anomaly_only_flag','escape_both']])+'\nEach layer has its own warning quota. The diagnostic union exceeds the original policy quota, so it must not be reported as a feasible policy improvement. The coupled policy comparison remains the valid same-budget result.\n'
    (ROOT/'docs/development_findings.md').write_text(findings, encoding='utf-8')
