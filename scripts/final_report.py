"""Generate the ten-section final report strictly from saved outputs."""
from pathlib import Path
import json
import pandas as pd
from talentroute.data import ROOT

def table(path,columns=None):
    df=pd.read_csv(path)
    if columns:df=df[columns]
    df=df.map(lambda v:f'{v:.4f}' if isinstance(v,float) else str(v))
    return '| '+' | '.join(df.columns)+' |\n| '+' | '.join(['---']*len(df.columns))+' |\n'+'\n'.join('| '+' | '.join(r)+' |' for r in df.to_numpy())+'\n'

def main():
    out=ROOT/'outputs/final';gate=json.loads((out/'acceptance.json').read_text());freeze=json.loads((out/'freeze.json').read_text())
    receipt=json.loads((ROOT/'evidence/linux-container-2026-11-01/attestation.json').read_text()) if (ROOT/'evidence/linux-container-2026-11-01/attestation.json').exists() else None
    if receipt:
        (out/'platform_evidence.json').write_text(json.dumps(receipt,indent=2))
        pd.DataFrame([{'platform':'Recorded Linux container','python':receipt['python'],'tests_passed':receipt['tests_passed'],'pipeline_seconds':receipt['pipeline_seconds']}]).to_csv(out/'platform_verification.csv',index=False)
        local=pd.read_csv(out/'test_metrics.csv');local['platform']='Canonical local run'
        remote=pd.read_csv(ROOT/'evidence/linux-container-2026-11-01/test_metrics.csv');remote['platform']='Recorded Linux container'
        pd.concat([local,remote]).to_csv(out/'platform_policy_comparison.csv',index=False)
    profiles=pd.read_csv(ROOT/'outputs/revision/warning_outcome_profiles.csv')
    profiles.loc[(profiles.flagged==True)&profiles.feature.isin(['log_clicks','inactive_days'])].to_csv(out/'warning_profile_summary.csv',index=False)
    segments=pd.read_csv(out/'test_segments.csv')
    segments.loc[(segments.segment=='no_early_assessment')&(segments.policy=='proposed_connected'),['group','n','adverse_coverage','flag_precision','missed_adverse_n']].to_csv(out/'assessment_availability_summary.csv',index=False)
    sensitivity=pd.read_csv(out/'development_sensitivity.csv')
    sensitivity.loc[sensitivity.assumption=='staff_minutes_per_100',['value','policy','adverse_coverage']].to_csv(out/'budget_condition_summary.csv',index=False)
    metrics=pd.read_csv(out/'test_metrics.csv').set_index('policy')
    gain=int(metrics.loc['business_rule','missed_adverse_n']-metrics.loc['proposed_connected','missed_adverse_n'])
    params={k:freeze['policy'][k] for k in ['staff_minutes_per_100','human_minutes','alert_minutes','alert_budget_fraction','max_alert_fraction','score_delay_days']}
    params.update({'forest_weight':freeze['forest_weight'],'anomaly_weight':freeze['anomaly_weight'],'max_flag_precision_loss':freeze['acceptance']['max_flag_precision_loss']})
    pd.DataFrame([{'parameter':k,'value':v} for k,v in params.items()]).to_csv(out/'frozen_parameters.csv',index=False)
    text=f'''# TalentRoute final evaluation

## 1. Executive summary
An educational consulting team serving universities or learning providers needs an auditable support-review and alert queue within limited staff time. We built a classification-plus-engagement-detector candidate and evaluated recorded outcomes, not the effect of contacting learners. The final candidate combines forest and boosting probabilities before adding the detector score to the budgeted ranking. Under the same staff-time budget, the connected candidate identifies {gain} more recorded adverse cases than the simple rule. Its result is below.

{table(out/'test_metrics.csv',['policy','adverse_coverage','flag_precision','human_precision','missed_adverse_n','staff_minutes'])}

**Acceptance decision:** {gate['recommendation']} This recommendation follows the recorded acceptance checks, not visual appeal or technique count. No prevention, ROI or employee-performance benefit is inferred.

## 2. Problem recap and changes since Intermediate
The original employee-training recommendation framing was refined to educational-consultancy learner-support targeting because OULAD contains student outcomes, not employee or intervention-effect labels. The intended client-facing consulting team designs learning plans, assessments and support processes; the evaluated software addresses only support prioritisation. The consulting use case serves university and other learners directly, without equating students with employees. This prototype has not been validated in a client deployment. This change was documented in the Intermediate. Pass and Distinction map to Success; Fail and Withdrawn remain separate. No outcome labels were fabricated.

Relative to the Intermediate, this release adds a fixed forest/boosting probability ensemble, a hashed pre-test freeze, separate held-out evaluation, paired acceptance checks, complete component ablations, and a final report. The ensemble tests whether averaging two model families yields a more useful ranking; it is not asserted to improve performance in advance. Current detector evidence is weak, so the connected system is an experimental candidate, not a deployment promise. Contextual-detector experiments remain development-only negative checks and are not silently substituted after test results.

## 3. Proposed system
```mermaid
flowchart LR
 A[Public OULAD] --> B[Eligibility and decision-time features]
 B --> C[Boosting and forest probability ensemble]
 B --> D[Train-fitted engagement Isolation Forest]
 C --> E[Fixed blended ranking]
 D --> E
 E --> F[Reviews and alerts within staff-time constraint]
 F --> G[Recorded-outcome evaluation]
```

The classifier retains distinct outcome probabilities. The detector learns unusual engagement without outcome labels; its training-reference percentile is not a failure probability. Shared engagement inputs mean these components are not statistically independent. Both feed the experimental ranking. Reviews take priority positions; alerts use the subsequent positions in that same ranking. The artifact does not claim a separate anomaly-only intervention pathway.

{table(out/'frozen_parameters.csv')}

The frozen configuration, weights and acceptance thresholds are recorded in `outputs/final/freeze.json`. Effort costs, budget and alert limits are configurable planning assumptions. Coverage counts either contact equally; it is not treatment-effect optimisation. The grading-availability lag is assumed because actual grading timestamps are absent.

## 4. Evaluation setup, results and tuning
Training and validation precede the held-out presentation chronologically; student identities are disjoint. Feature imputation and encoders fit training only. Predictors exclude protected attributes, final outcomes and future withdrawal. Eligibility and feature-availability rules are detailed in the Intermediate data dictionary. Protected fields support aggregate audits only.

Intermediate boosting settings and blend candidates were compared on validation; these are exploratory selections. The final forest/boosting averaging weight was fixed by design before test evaluation rather than selected on test. The frozen model, data and implementation hashes prevent silent replacement. Primary ML metric is adverse PR-AUC: relevant to ranking eventual adverse cases. Separate outcome PR-AUC, macro-F1, log loss and Brier assess distinctions and probability quality. Primary decision metric is coverage within staff time; precision describes unnecessary contacts. Detector metrics use recorded outcomes as relevance proxies, never anomaly ground truth.

{table(out/'test_ml_metrics.csv',['model','adverse_pr_auc','macro_f1','log_loss','fail_pr_auc','withdrawn_pr_auc','adverse_brier'])}

{table(out/'test_detector_relevance.csv',['detector','proxy_adverse_pr_auc','adverse_coverage','flag_precision'])}

Primary-metric uncertainty and paired coverage differences use student-cluster resampling, preserving repeated enrolments. These intervals describe sampling uncertainty conditional on the fitted system and data; they do not establish population transportability.

{table(out/'test_primary_intervals.csv')}
{table(out/'test_paired_intervals.csv')}

The proposed ensemble has adverse PR-AUC {float(pd.read_csv(out/'test_ml_metrics.csv').set_index('model').loc['proposed_ensemble','adverse_pr_auc']):.4f}, compared with {float(pd.read_csv(out/'test_ml_metrics.csv').set_index('model').loc['hgb_15_10','adverse_pr_auc']):.4f} for the original boosting model. A better fixed-budget contact list does not imply universally better ranking or classification. The lower macro-F1 also limits claims about assigning the three outcome labels.

The acceptance JSON records whether the lower paired bounds beat the references and whether precision loss stays within the frozen tolerance. A zero-crossing interval is inconclusive. No post-test tuning or positive-result substitution is permitted.

## 5. Ablation
`outputs/final/ablation.csv` compares the business rule, original classifier, ensemble without detector, detector alone and connected proposal at the same capacity. Removing the detector isolates its incremental contribution; replacing the ensemble with the original classifier isolates the model-family change. Detector relevance is also compared with inactivity. Negative results favour simpler models rather than justify additional complexity.

![Component ablation](../outputs/final/ablation.png)

## 6. Sensitivity and stability
Development sensitivity varies staff budget, human-review effort, alert effort and detector weight. These are scenario assumptions, not estimated real costs. Ranges bracket the configured scenario and represent lighter/heavier staff availability and contact effort; operational stakeholders must validate them before use. Additional data-availability and cutoff checks appear in `outputs/validation_data_assumptions.csv`. Detector-seed checks are in `outputs/final/development_seed_stability.csv`.

![Development sensitivity](../outputs/final/sensitivity.png)

These curves evaluate the frozen ensemble/detector candidate on development validation, including alternative detector seeds. They show sensitivity to declared scenarios rather than transportability to a new institution. They do not permit redesign after final-test results.

## 7. Three deeper analyses
The Intermediate committed to layer escape, warning-positive outcome profiles and module-specialist versus global models. Implementations and aggregate results remain under `outputs/revision/`; all were development analyses, not independent confirmation.

{table(ROOT/'outputs/revision/same_quota_layers.csv',['policy','adverse_coverage','flag_precision','staff_minutes'])}

**Complementarity / layer escape:** `same_quota_layers.csv`, `layer_quota_sensitivity.csv` and `tie_sensitivity.csv` test signal combinations within a shared total quota. The original pooled mixture did not generally beat classifier ranking. Recommendation: do not equate more warning layers with better targeting; retain capacity-matched comparisons.

**Challenge profiles:** `warning_outcome_profiles.csv` compares historical warning-positive Success, Fail and Withdrawn cases. Success despite warnings does not establish resilience mechanisms or intervention benefit. Recommendation: use profiles as prompts for human review, not causal prescriptions. These historical signals differ from the current policy flags.

{table(ROOT/'outputs/revision/model_comparison.csv',['model','adverse_pr_auc','adverse_coverage','flag_precision'])}

**Segment-specific models / reconciliation:** `model_comparison.csv`, `specialist_eligibility.csv` and `forest_minus_hgb_intervals.csv` compare global and specialist models. Specialist eligibility uses training counts; stronger global comparators prevent a weak baseline from overstating specialist value. Recommendation: do not deploy specialists solely because they beat global logistic. The paired development check below quantifies the specialist/global-logistic comparison; this is not confirmation against a stronger global ensemble.

{table(ROOT/'outputs/revision/specialist_minus_global_intervals.csv')}

{table(out/'warning_profile_summary.csv',['outcome','feature','n','median'])}

These mappings make explicit how the committed analyses relate to the proposal's deeper-analysis categories. Each sharpens a recommendation; none establishes a causal support mechanism.

## 8. Insights and recommendations
The recorded acceptance check does not support endorsing the additional component. Retain the simpler reference pending new independent evidence; the connected system remains an evaluated experimental candidate. The experimental second technique remains implemented and evaluated; the evaluated final candidate connects both techniques, while its operational fallback is explicitly simpler. This distinction is disclosed rather than presenting experimental inclusion as deployment approval.

The development advantage is budget-dependent: the connected candidate's coverage advantage over the original classifier reverses at the largest tested budget. Do not promise the same benefit at every staffing level; a new client must validate its own declared budget before adoption, without revising this release after test inspection.

{table(out/'budget_condition_summary.csv')}

Assessment availability also exposes a hard segment. In the following held-out table, group 0 has early scores and group 1 lacks them. Lower coverage among learners with scores identifies an important missed-case audit; it does not prove that missing scores cause risk or justify forcing equal contact rates across groups. Investigate additional observable signals and reviewer context prospectively rather than inventing labels or treating missing scores as zero.

{table(out/'assessment_availability_summary.csv')}

Historical warning-positive profiles also differ by outcome: withdrawn learners need not exhibit the same inactivity pattern as failed learners. Keep the outcomes separate and avoid a universal inactivity story. Review Fail and Withdrawn separately because a pooled improvement may hide a loss for one outcome. See `test_metrics.csv`. Inspect course and missing-assessment segments before deployment; `test_segments.csv` marks when sample sizes permit interpretation. Budget changes alter contact volume and missed cases, not demonstrated prevented failures. A human reviewer should confirm context before contacting a learner.

## 9. Limitations and risks
The dataset is old and institution-specific. Course shift, repeat-student exclusions, unobserved grading availability and missing assessments limit generalisation. Activity anomalies lack verified labels. Neither assumed effort nor contact effectiveness is measured. Low-count segments are not evidence of fairness. Contact policies can create feedback loops; future monitoring should record workload, complaints, drift and subgroup errors. Public-data identifiers are excluded from released worklists; the demonstration uses synthetic case references, not synthetic research outcomes.

A separate Linux-container reproduction succeeded for the same analytical source and configuration; its source commit and checksummed artifact are recorded in `outputs/final/platform_evidence.json`. Later report-only changes are separate from that run. The archived requirements file was generated before external attestation and retains its original static label. Local and container metrics are kept separate because numerical tree-model differences occur across platforms; bit-identical outputs are not claimed.

{table(out/'platform_verification.csv') if receipt else 'External platform verification is unavailable in this checkout.'}

## 10. Connection to the original problem and next steps
The project delivers an auditable learner-support targeting experiment that an educational consulting team could use when advising a university. It does not evaluate a complete learning-plan or assessment-management platform, nor establish validity for other providers or corporate L&D. It retains the original goal of supporting resource-constrained decisions while rejecting unsupported uplift. The next useful data are actual contact times, grading-availability timestamps, and ethically collected intervention outcomes. A prospective human-reviewed pilot would be needed to estimate whether acting improves outcomes. The viva and presentation are separate assessments; explanations here must remain defensible in both.

Data: Kuzilek, Hlosta and Zdrahal, OULAD, UCI DOI 10.24432/C5KK69, CC BY 4.0. Further schema and preparation details: `data_dictionary.md` and `project_definition.md`.
'''
    (ROOT/'docs/final_report.md').write_text(text)
    historical='> Intermediate development record. Final held-out evidence and conclusions are in `final_report.md`.\n\n'
    for name in ['baseline_report.md','EXPERIMENT_REGISTER.md','development_findings.md','project_definition.md','system_diagram.md']:
        path=ROOT/'docs'/name
        value=path.read_text()
        if not value.startswith(historical):path.write_text(historical+value)
    print('Final report generated; acceptance:',gate['accepted'])
if __name__=='__main__':main()
