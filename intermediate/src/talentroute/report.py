"""Generate development interpretations from saved evidence; never fit or score a model."""
import json
import pandas as pd
from .data import ROOT


def report():
    out=ROOT/'outputs'
    def read(name): return pd.read_csv(out/name)
    def block(frame): return '```csv\n'+frame.to_csv(index=False,float_format='%.4f').strip()+'\n```\n'
    audit=json.loads((out/'data_audit.json').read_text())
    ci=json.loads((out/'validation_paired_interval.json').read_text())
    rule_ci=json.loads((out/'diagnostics/classifier_minus_rule.json').read_text())
    models=read('revision/model_comparison.csv'); policy=read('validation_decision_metrics.csv')
    detector=read('validation_anomaly_proxy_metrics.csv').set_index('detector')
    coverage=read('development_coverage.csv').set_index(['split','code_module'])
    segments=read('validation_challenge_segments.csv').set_index(['segment','group','policy'])
    layers=read('revision/same_quota_layers.csv').set_index('policy')
    profiles=read('revision/warning_outcome_profiles.csv')
    seeds=read('validation_seed_stability.csv').pivot(index='seed',columns='weight',values='adverse_coverage')
    gains=100*(seeds[.2]-seeds[0.])
    # Only development records enter these audits; the final cohort is not scored.
    dev=pd.read_csv(ROOT/'data/processed/enrolments.csv')
    dev=dev[dev.split.isin(['train','validation'])].copy()
    val=dev[dev.split=='validation']; n_adverse=int(val.target.ne('Success').sum())
    p=policy.set_index('policy'); flagged=int(p.loc['classifier_only','human_n']+p.loc['classifier_only','alert_n'])
    ggg=segments.loc[('code_module','GGG','classifier_only')]
    ggg_mix=segments.loc[('code_module','GGG','coupled_selected')]
    female=segments.loc[('gender','F','classifier_only')]; male=segments.loc[('gender','M','classifier_only')]
    missing_date=int((dev.target.eq('Withdrawn')&dev.date_unregistration.isna()).sum())
    unscored=int((dev.submitted_count.gt(0)&dev.score_mean.isna()).sum())
    curve=read('investigations/learning_curve.csv')
    learning=curve.groupby(['model','fraction','split'],as_index=False).adverse_ap.mean()
    h=learning[(learning.model=='hgb_15_10')&(learning.split=='validation')].set_index('fraction')
    shift=read('investigations/period_shift.csv')
    flagged_profiles=profiles[profiles.flagged.eq(True)&profiles.feature.eq('score_mean')].set_index('outcome')
    m=models.set_index('model')
    tradeoffs=read('validation_challenge_segments.csv')
    tradeoffs=tradeoffs[tradeoffs.policy.isin(['classifier_only','coupled_selected'])]
    wide=tradeoffs.pivot(index=['segment','group'],columns='policy',values=['adverse_coverage','flagged_n'])
    delta=pd.DataFrame({'classifier_coverage':wide['adverse_coverage']['classifier_only'],
        'blend_coverage':wide['adverse_coverage']['coupled_selected'],
        'coverage_difference':wide['adverse_coverage']['coupled_selected']-wide['adverse_coverage']['classifier_only'],
        'classifier_flagged_n':wide['flagged_n']['classifier_only'],
        'blend_flagged_n':wide['flagged_n']['coupled_selected']})
    delta.to_csv(out/'development_segment_tradeoffs.csv')
    # Machine-readable provenance and checks allow reviewers to reproduce prose numbers.
    evidence={'scope':'exploratory development interpretation; no fitting, selection or test scoring',
        'test_rows_used':0,'final_2014J_already_observed':True,'new_model_selection':False,
        'segment_interpretation':'Descriptive shared-budget coverage shifts; no causal or fairness guarantee',
        'validation_adverse_n':n_adverse,'validation_prevalence':n_adverse/len(val),
        'perfect_ranking_coverage_ceiling_at_current_contact_count':min(flagged,n_adverse)/n_adverse,
        'missing_withdrawal_date_adverse_development_n':missing_date,
        'submission_present_but_score_missing_development_n':unscored,
        'classifier_minus_rule':rule_ci,'blend_minus_classifier':ci,
        'sources':['development_coverage.csv','validation_challenge_segments.csv',
            'revision/same_quota_layers.csv','revision/warning_outcome_profiles.csv',
            'revision/model_comparison.csv','validation_seed_stability.csv'],
        'commitment_status':{'layer_escape':'executed at equal quota; round-robin underperforms',
            'warning_profiles':'executed descriptive profiles, not causal resilience or trajectories',
            'module_specialists':'executed with train-only eligibility and global fallback'}}
    (out/'development_evidence.json').write_text(json.dumps(evidence,indent=2))
    text=f'''# TalentRoute: Intermediate evidence report

## Decision and scope
An educational consulting team serving universities prioritises alerts and human reviews using information available at day 28. The assumed alternative is an early-score/inactivity queue, not a documented institutional workflow. Missed cases lose an opportunity for review; false warnings burden learners and staff.

The proposal's employee recommender/uplift became student classification plus engagement outlier detection: OULAD supports learner outcomes, not employee transfer or treatment benefits. Same-budget baselines, uncertainty and component go/no-go checks remain. Commitments and acceptance criteria: project_definition.md.

## Data and evaluation boundary
OULAD (Kuzilek, Hlosta & Zdrahal, 2015; doi:10.24432/C5KK69; CC BY 4.0) contains {audit['raw_enrolments']} enrolments. Of {audit['eligible_enrolments']} initially eligible, {audit['purged_earlier_repeat_enrolments']} earlier repeat-student records are purged. Train: {audit['split_counts']['train']} (2013B/J); validation: {audit['split_counts']['validation']} (2014B); final cohort: {audit['split_counts']['test']} (2014J). Purging ensures disjoint identities but changes the population and can disadvantage analysis of repeat learners.

A separate frozen candidate was already evaluated on 2014J. It is no longer unseen. Everything added here is development-only exploratory analysis; it neither selects a replacement nor reopens that test. Any changed final model needs independent evidence for confirmatory claims. Preserve the original frozen evaluation separately.

VLE ends at day 28; non-banked/non-exam submissions end at day 21 under an assumed seven-day score delay. Imputation uses training data only. IDs, demographics and future outcomes are excluded from predictors. Success combines Pass/Distinction; Fail and Withdrawn remain distinct. Among development records, {missing_date} Withdrawn cases lack withdrawal dates, leaving day-28 eligibility uncertain; {unscored} have submissions but no score. No-submission flags are not missing-score flags.

## Connected methods
Classification estimates Success/Fail/Withdrawn probabilities; Isolation Forest supplies an engagement-rarity percentile. A weighted ranking feeds one staff-time policy. Five classifiers are comparisons within one family; classification and outlier detection are the two families.

Baselines: logistic classification, inactivity detection, and early-score/inactivity decision rule. First-pass comparisons include constrained tree, forest, histogram boosting and module-logistic specialists with training-only eligibility/global fallback. Settings: logistic C=1; boosting 140 iterations, learning rate .07, leaf/L2 candidates (7,2), (15,2), (15,10); detector 150 trees, max_samples=512; seed 7101. Historical validation search used adverse PR-AUC and blend weights 0/.1/.2/.35/.5. Exact configurations: revision.py.

## Metrics and results
Primary ML metric: average precision, reported as PR-AUC, for ranking adverse outcomes. Fail/Withdrawn AP, macro-F1, log loss and Brier assess distinct outcomes and probability quality. Detector AP/precision/coverage are outcome-relevance proxies, not accuracy against verified anomaly labels. Primary decision metric: adverse coverage at fixed effort; precision, missed cases and workload expose trade-offs.

Validation prevalence is {n_adverse/len(val):.2%}, the population no-skill AP reference. With {flagged} contacts and {n_adverse} adverse cases, perfect ranking could cover at most {min(flagged,n_adverse)/n_adverse:.2%}, counting either action equally. This is a targeting ceiling, not achievable prevention.

Classification, outputs/revision/model_comparison.csv:
{block(models[['model','adverse_pr_auc','fail_pr_auc','withdrawn_pr_auc','macro_f1','log_loss','adverse_brier','adverse_coverage']])}
Same-budget decisions, outputs/validation_decision_metrics.csv:
{block(policy[policy.policy.isin(['business_rule','classifier_only','anomaly_rule','anomaly_only','coupled_selected'])][['policy','adverse_coverage','fail_coverage','withdrawn_coverage','flag_precision','human_n','alert_n','staff_minutes']])}
Detector proxies, outputs/validation_anomaly_proxy_metrics.csv:
{block(detector.reset_index()[['detector','proxy_adverse_pr_auc','adverse_coverage','flag_precision','missed_adverse_n']])}
Classifier versus rule reaches {rule_ci['extra_adverse_cases_flagged']} additional adverse cases: +{100*rule_ci['coverage_difference']:.2f} percentage points (paired 95% interval {100*rule_ci['ci95'][0]:.2f}–{100*rule_ci['ci95'][1]:.2f}). It clears the original development comparison, but selection makes this exploratory evidence, not independent confirmation. Source: diagnostics/classifier_minus_rule.json.

Isolation Forest loses to inactivity (AP {detector.loc['isolation_forest','proxy_adverse_pr_auc']:.3f} versus {detector.loc['inactivity_rule','proxy_adverse_pr_auc']:.3f}): unusual behaviour need not imply adverse outcomes. Blending covers {p.loc['coupled_selected','adverse_coverage']:.2%} versus classifier {p.loc['classifier_only','adverse_coverage']:.2%}; difference interval [{ci['ci95'][0]:.4f}, {ci['ci95'][1]:.4f}] crosses zero. Added benefit is unconfirmed. Across seeds, gains range {gains.min():.2f}–{gains.max():.2f} percentage points (validation_seed_stability.csv); do not retune from this diagnostic.

Budget assumptions: 300 minutes/100 learners, 30/review, 2/alert; up to 20% of time reserved for alerts, capped at 20% of learners. Both actions count equally. This remains constrained ranking with a fixed action mix, not learned treatment allocation or measured benefit.

## EDA: observations that affect interpretation
CCC is absent from training but contributes {val.code_module.eq('CCC').mean():.1%} of validation: test unseen-course robustness rather than assume course-specific learning transfers. FFF's no-submission rate shifts from {coverage.loc[('train','FFF'),'no_assessment_rate']:.1%} to {coverage.loc[('validation','FFF'),'no_assessment_rate']:.1%}; GGG's validation rate is {coverage.loc[('validation','GGG'),'no_assessment_rate']:.1%}. Missingness can reflect assessment schedules, not disengagement. Overall {dev.score_mean.isna().mean():.1%} lack early scores. Keep missingness explicit and audit course/period slices.

![Development outcomes](../outputs/eda_01_outcomes.png)
![Submission availability by course and period](../outputs/eda_07_observability.png)
![Unequal-window engagement totals](../outputs/eda_05_change.png)

Ten saved figures and overview CSVs cover both families and the decision. Engagement windows are days 0–14 and 15–28 (15 versus 14 days): totals are not equal-duration trends.

## Three commitments: executed evidence and consequence
1. Layer escape: equal-quota round-robin covers {layers.loc['four_layer_round_robin','adverse_coverage']:.2%} versus classifier {layers.loc['classifier_only','adverse_coverage']:.2%}. Extra layers do not automatically help; retain the single ranking as reference. Sources: revision/same_quota_layers.csv; layer_quota_sensitivity.csv tests 24 orders/three tie seeds.
2. Warning profiles: under historical four-layer selection, {int(flagged_profiles.loc['Success','n'])} flagged learners succeeded; observed-score medians are {flagged_profiles.loc['Success','median']:.0f} (Success), {flagged_profiles.loc['Fail','median']:.0f} (Fail), {flagged_profiles.loc['Withdrawn','median']:.0f} (Withdrawn), with observed counts {int(flagged_profiles.loc['Success','observed_n'])}/{int(flagged_profiles.loc['Fail','observed_n'])}/{int(flagged_profiles.loc['Withdrawn','observed_n'])}. Source: revision/warning_outcome_profiles.csv. Treat warnings as review prompts; these static profiles establish neither resilience mechanisms nor intervention effects.
3. Course specialists: hybrid AP {m.loc['module_logistic_hybrid','adverse_pr_auc']:.3f} versus logistic {m.loc['logistic','adverse_pr_auc']:.3f}, boosting {m.loc['hgb_15_10','adverse_pr_auc']:.3f}. Specialisation is not automatically better; retain global fallback for unsupported courses. Sources: revision/model_comparison.csv, specialist_eligibility.csv, model_segments.csv.

A critical segment audit: classifier selects zero of GGG's {int(ggg.adverse_n)} adverse cases; blend reaches {ggg_mix.adverse_coverage:.1%}. Female/male adverse coverage is {female.adverse_coverage:.1%}/{male.adverse_coverage:.1%}. These descriptive validation gaps require course-aware review before deployment; they neither prove discrimination nor justify retuning on the final test. Source: validation_challenge_segments.csv. Aggregate improvement alone is insufficient.

## Debugging, ablation and final path
Learning curves, single-feature probes, grouped permutation and shuffled-training-label controls are development diagnostics, not proof against leakage. HGB learning-curve AP moves {h.loc[.2,'adverse_ap']:.3f}→{h.loc[1.,'adverse_ap']:.3f}; period-classifier ROC-AUC {shift.domain_roc_auc.mean():.3f} signals covariate differences, not proven concept drift. Sources: outputs/investigations/ and diagnostics/; reproduce with just investigations.

Ablation removes/swaps classifier, detector and rule at equal effort. Executed sensitivity varies budget, action costs, availability delay/cutoff and seeds (validation_sensitivity.csv, validation_data_assumptions.csv). The three commitments stay fixed; final writing must explain their decision consequences, not promise universal improvement.

Keep classifier-only as a provisional analytical reference, not a deployable recommendation. A stakeholder pilot additionally needs an agreed practical gain, segment review, real workload checks and intervention evidence. No prevented failures, ROI, weekly integration or employee benefit is established. Reproduce: just install; just pipeline. Evidence provenance: outputs/development_evidence.json. Historical platform checks apply only to their recorded snapshots.
'''
    (ROOT/'docs/baseline_report.md').write_text(text)
    (ROOT/'docs/development_findings.md').write_text('# Development evidence\n\nCanonical interpretations and source paths: baseline_report.md. Machine-readable checks: outputs/development_evidence.json. All additions are exploratory development analysis; 2014J was previously observed and is not rescored.\n')
    print('Generated development evidence and report; no model fitting or final scoring')
