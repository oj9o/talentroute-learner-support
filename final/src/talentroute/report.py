"""Concise evidence report and decision-relevant figures from computed CSV files."""

from dataclasses import asdict
import os
import re
from .data import ROOT, config
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.cache/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from .decision import Policy
from .models import FEATURES

INK, REVIEW, ALERT = '#152f36', '#126c69', '#c77a35'


def read(name):
    return pd.read_csv(ROOT / f'outputs/{name}.csv')


def table(frame, columns=None, digits=3):
    """Small Markdown table without another runtime dependency."""
    frame = frame[columns] if columns else frame
    def fmt(value):
        if pd.isna(value):
            return '—'
        if isinstance(value, (float, np.floating)):
            return f'{value:.{digits}f}'
        return str(value).replace('|', '/')
    lines = ['| ' + ' | '.join(frame.columns) + ' |', '| ' + ' | '.join(['---'] * len(frame.columns)) + ' |']
    lines.extend('| ' + ' | '.join(fmt(v) for v in row) + ' |' for row in frame.itertuples(index=False, name=None))
    return '\n'.join(lines)


def eda():
    data = pd.read_csv(ROOT / 'data/processed/development.csv')
    rows = []
    for (period, module), group in data.groupby(['code_presentation', 'code_module']):
        rows.append({'presentation': period, 'module': module, 'n': len(group),
                     'students': group.id_student.nunique(), 'adverse_rate': group.target.ne('Success').mean(),
                     'assessment_missing_rate': group.score_mean.isna().mean(),
                     'no_clicks_rate': group.clicks.eq(0).mean()})
    pd.DataFrame(rows).to_csv(ROOT / 'outputs/course_observability.csv', index=False)
    pd.DataFrame({'feature': FEATURES, 'missing_n': data[FEATURES].isna().sum().values}).to_csv(ROOT / 'outputs/missingness.csv', index=False)
    parameters = {**asdict(Policy()), 'cutoff_day': config()['cutoff_day'],
                  'score_delay_days_assumed': config()['score_delay_days'],
                  'original_precision_loss_margin': .02}
    pd.DataFrame([parameters]).to_csv(ROOT / 'outputs/parameters.csv', index=False)
    folder = ROOT / 'outputs/figures'
    folder.mkdir(exist_ok=True)
    observability = pd.DataFrame(rows)
    for metric, title in [('assessment_missing_rate', 'Early-score availability differs by course and cohort'),
                          ('adverse_rate', 'Observed outcome prevalence differs by course and cohort')]:
        matrix = observability.pivot(index='module', columns='presentation', values=metric)
        ax = (matrix * 100).plot.bar(figsize=(8, 4), color=['#126c69', '#c77a35'])
        ax.set(title=title, ylabel='Cases (%)', xlabel='Course')
        ax.figure.tight_layout()
        ax.figure.savefig(folder / (metric + '.png'), dpi=160)
        plt.close(ax.figure)



def ablation_figure():
    """Show paired route differences, including uncertainty, for the selected model."""
    folder = ROOT / 'outputs/figures'
    folder.mkdir(exist_ok=True)
    scores = read('policy_comparison')
    scores = scores[scores.protocol.eq('identity_disjoint') & scores.seed.eq(7101)]
    intervals = read('policy_intervals')
    data = scores.merge(intervals, on=['protocol', 'seed', 'model', 'route'])
    reference = data.loc[data.route.eq('classifier'), 'coverage'].iloc[0]
    data = data[~data.route.eq('classifier')]
    delta = data.coverage - reference
    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.errorbar(delta * 100, data.route,
                xerr=np.array([delta-data.difference_low, data.difference_high-delta]) * 100,
                fmt='o', color='#355c9b', capsize=3)
    ax.axvline(0, color=INK, linewidth=.8)
    ax.set(xlabel='Coverage difference vs risk-only (percentage points)',
           title='Does an alternative review reserve improve targeting?')
    fig.tight_layout()
    fig.savefig(folder / 'ablation.png', dpi=160, bbox_inches='tight')
    plt.close(fig)


def budget_figure():
    (ROOT / 'outputs/figures').mkdir(exist_ok=True)
    data = read('sensitivity')
    subset = data[(data.protocol == 'identity_disjoint') & (data.parameter == 'minutes_per_100')]
    fig, ax = plt.subplots(figsize=(8, 4))
    for route, color, style in [('classifier', '#355c9b', '-'), ('rule', '#6b788a', ':'), ('anomaly', '#8056a6', '--')]:
        rows = subset[subset.route == route]
        ax.plot(rows.value, rows.coverage * 100, style, marker='o', color=color, label=route)
    ax.set(title='How coverage changes with staff time', xlabel='Staff minutes per 100 enrolment cases',
           ylabel='Observed adverse outcomes contacted (%)')
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(ROOT / 'outputs/figures/budget_curve.png', dpi=160, bbox_inches='tight')
    plt.close(fig)


def figures():
    """One action palette, meaningful comparisons, labeled counts and denominators."""
    folder = ROOT / 'outputs/figures'
    folder.mkdir(exist_ok=True)
    ablation_figure()
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.labelcolor': INK, 'text.color': INK, 'axes.titleweight': 'bold'})
    def save(fig, name):
        fig.tight_layout()
        fig.savefig(folder / f'{name}.png', dpi=160, bbox_inches='tight')
        plt.close(fig)
    budget_figure()
    composition = read('segments')
    composition = composition[(composition.protocol == 'identity_disjoint') & (composition.route == 'classifier') & (composition.dimension == 'code_module')]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh(composition.segment, composition.review_n, color=REVIEW, label='Human review')
    ax.barh(composition.segment, composition.alert_n, left=composition.review_n, color=ALERT, label='Alert')
    ax.barh(composition.segment, composition.no_action_n, left=composition.contact_n, color='#e6ebe7', label='No action')
    ax.set(title='Course composition of the selected-model queue', xlabel='Enrolment cases', ylabel='Course')
    ax.legend(frameon=False, ncol=3)
    save(fig, 'queue_composition')
    gender = read('course_gender')
    gender = gender[(gender.protocol == 'identity_disjoint') & (gender.route == 'classifier') & gender.interpretation_allowed]
    fig, ax = plt.subplots(figsize=(8, 5))
    modules = sorted(gender.module.unique())
    for sex, marker, offset in [('F', 'o', -.12), ('M', 'D', .12)]:
        rows = gender[gender.gender == sex].set_index('module').reindex(modules)
        y = np.arange(len(modules)) + offset
        errors = np.array([rows.coverage - rows.coverage_low, rows.coverage_high - rows.coverage]) * 100
        ax.errorbar(rows.coverage * 100, y, xerr=errors, fmt=marker, color=INK, label=sex, capsize=2)
        for level, row in zip(y, rows.itertuples()):
            ax.annotate(f'n={row.n:g}; adverse={row.adverse_n:g}', (102, level), va='center', fontsize=8)
    ax.set(yticks=range(len(modules)), yticklabels=modules, xlim=(0, 133),
           xticks=range(0, 101, 20), xlabel='Adverse outcome coverage (%)', ylabel='Course',
           title='Within-course gender audit: conditional bootstrap intervals')
    ax.legend(frameon=False)
    save(fig, 'gender_by_course')
    curves = read('action_break_even')
    curves = curves[(curves.protocol == 'identity_disjoint') & (curves.withdrawn_value == 1)]
    fig, ax = plt.subplots(figsize=(8, 4))
    x = np.linspace(0, 10, 101)
    for route, color in [('anomaly', '#8056a6'), ('inactivity', '#617871'), ('course', '#6b788a')]:
        row = curves[curves.route == route].iloc[0]
        ax.plot(x, row.delta_intercept + row.delta_slope * x, label=route, color=color)
    ax.axhline(0, color=INK, linewidth=.8)
    ax.set(title='Conditional value difference against risk-only routing', xlabel='Assumed review targeting weight',
           ylabel='Preference-unit difference (not causal benefit)')
    ax.legend(frameon=False)
    save(fig, 'preference_regions')


def run():
    """Build explanations from current outputs, including unfavorable findings."""
    figures()
    def primary(name):
        frame = read(name)
        frame = frame[frame.protocol.eq('identity_disjoint')]
        return frame[frame.seed.eq(7101)] if 'seed' in frame else frame
    selection = read('development_selection')
    chosen = selection.loc[selection.selected_development_candidate, 'model'].iloc[0]
    scores = primary('model_comparison').merge(primary('model_intervals'), on=['protocol','model'])
    routes = primary('policy_comparison')
    reference = routes[routes.route.eq('classifier')].iloc[0]
    anomaly = routes[routes.route.eq('anomaly')].iloc[0]
    intervals = primary('policy_intervals')
    interval = intervals[intervals.route.eq('anomaly')].iloc[0]
    baseline = primary('baselines')
    rule = baseline[baseline.baseline.eq('score_inactivity_rule')].iloc[0]
    proposed = read('proposed_system')
    headline = proposed[proposed.system.isin(['score_inactivity_rule','selected_risk_queue'])]
    chosen_result = headline[headline.protocol.eq('identity_disjoint') & headline.system.eq('selected_risk_queue')].iloc[0]
    transitions = primary('action_transitions')
    change = transitions[transitions.route.eq('anomaly')].iloc[0]
    detector = primary('detector_comparison')
    params = read('parameters').iloc[0]
    profiles = primary('warning_profiles'); profiles = profiles[profiles.route.eq('classifier')]
    profile_fail = profiles[profiles.observed_outcome.eq('Fail')].iloc[0]
    specialists = primary('specialists'); specialists = specialists[specialists.module.eq('ALL')]
    global_row = specialists[specialists.model.eq('global_logistic')].iloc[0]
    specialist_row = specialists[specialists.model.eq('module_logistic')].iloc[0]
    reconciled = primary('reconciliation'); reconciled = reconciled[reconciled.module.eq('ALL')]
    reconciled_row = reconciled[reconciled.policy.eq('round_robin_layers')].iloc[0]
    splits = primary('selection_stability')
    counts = splits.groupby('selected_model').size().reset_index(name='times_selected')
    split_low, split_high = splits.selected_minus_rule.quantile([.025,.975])
    availability = read('availability_audit')
    calibration = read('calibration_diagnostics')
    course = read('segments')
    course = course[course.route.eq('classifier') & course.dimension.eq('code_module')].copy()
    course['minutes_share'] = course.staff_minutes / course.groupby('protocol').staff_minutes.transform('sum')
    course['seen_in_training'] = course.segment.isin(['BBB','DDD','FFF'])
    gender = primary('segments'); gender = gender[gender.route.eq('classifier') & gender.dimension.eq('gender')]
    within = primary('course_gender'); within = within[within.route.eq('classifier') & within.interpretation_allowed]
    wide = within.pivot(index='module', columns='gender', values='coverage').dropna()
    largest = (wide.F-wide.M).abs().idxmax()
    within_gap = within[within.module.eq(largest)]
    ggg = course[course.protocol.eq('identity_disjoint') & course.segment.eq('GGG')].iloc[0]
    ddd = course[course.protocol.eq('identity_disjoint') & course.segment.eq('DDD')].iloc[0]
    returning = read('segments')
    returning = returning[returning.protocol.eq('operational') & returning.route.eq('classifier') & returning.dimension.eq('prior_enrolment')]
    sens = read('sensitivity')
    pivot = sens.pivot(index=['protocol','parameter','value'], columns='route', values='coverage').reset_index()
    pivot['risk_minus_rule_pp'] = 100*(pivot.classifier-pivot.rule)
    pivot['anomaly_minus_risk_pp'] = 100*(pivot.anomaly-pivot.classifier)
    pivot.to_csv(ROOT / 'outputs/sensitivity_comparison.csv', index=False)
    summaries = []
    for parameter, group in pivot[pivot.protocol.eq('identity_disjoint')].groupby('parameter'):
        lo, hi = group.risk_minus_rule_pp.min(), group.risk_minus_rule_pp.max()
        finding = 'positive at every tested value' if lo > 0 else ('negative at every tested value' if hi < 0 else 'changes sign or includes a tie')
        summaries.append(f'- {parameter}: risk-minus-rule ranges from {lo:.2f} to {hi:.2f} percentage points ({finding}); anomaly-minus-risk ranges from {group.anomaly_minus_risk_pp.min():.2f} to {group.anomaly_minus_risk_pp.max():.2f} points.')
    sensitivity_text = '\n'.join(summaries)
    count_metrics = routes[routes.route.isin(['classifier','anomaly','random'])].copy()
    rule_counts = pd.DataFrame([{**rule.to_dict(), 'route':'score_inactivity_rule'}])
    count_metrics = pd.concat([count_metrics, rule_counts], ignore_index=True)
    count_metrics['adverse_reviewed'] = count_metrics.review_fail_n + count_metrics.review_withdrawn_n
    count_metrics.to_csv(ROOT / 'outputs/review_tier_counts.csv', index=False)
    risk_gate = sens[sens.protocol.eq('identity_disjoint') & sens.route.eq('classifier') & sens.parameter.eq('risk_threshold')]
    gate_text = ('The tested score cutoffs produce identical risk-only queues; they do not bind in this range.'
                 if risk_gate.contact_n.nunique()==1 and risk_gate.adverse_contact_n.nunique()==1 else
                 'The tested score cutoffs change eligibility and queue size; inspect the rows before choosing a cutoff.')
    alert = sens[sens.protocol.eq('identity_disjoint') & sens.route.eq('classifier') & sens.parameter.eq('alert_budget_fraction')]
    alert_text = ('Alert shares 0.2 and 0.4 give identical counts because the alert-place cap binds.'
                  if alert[alert.value.isin([.2,.4])].alert_n.nunique()==1 else 'Alert-share changes alter the action mix.')
    gain_text = 'has a positive conditional gain interval' if chosen_result.difference_vs_rule_low>0 else 'does not establish a positive conditional gain'
    anomaly_text = 'crosses zero' if interval.difference_low <= 0 <= interval.difference_high else ('is positive' if interval.difference_low>0 else 'is negative')
    warning = []
    if chosen != 'logistic': warning.append('Selected model differs from the narrated C=1 logistic: update slides and confirmation protocol.')
    if chosen_result.difference_vs_rule_low <= 0: warning.append('The positive paired development gain no longer holds.')
    if interval.difference_low > 0: warning.append('The anomaly gain is now positive under the conditional check; reassess the recommendation.')
    if specialist_row.coverage > global_row.coverage: warning.append('Specialist coverage now exceeds the global comparator.')
    (ROOT/'outputs/conclusion_status.txt').write_text('\n'.join(warning) if warning else 'Current narrated conclusions match these outputs. This is not independent validation.\n')
    warning_text = '**Changed conclusions requiring review:** '+ ' '.join(warning) if warning else ''
    recommended_reserve = 'retain the experimental route pending confirmation' if interval.difference_low>0 else 'use zero anomaly reserve provisionally'
    calibration_main = calibration[calibration.group.isin(['all','contacted','seen_courses','unseen_courses'])]
    calibration_courses = calibration[calibration.protocol.eq('identity_disjoint') & calibration.group.str.startswith('course_')]
    boost = selection[selection.model.str.startswith('hgb')]
    calendar = read('label_availability').groupby(['training_presentation','decision_presentation','release_delay_days_assumed']).agg(
        earliest_end=('course_end_earliest','min'), latest_end=('course_end_latest','max'),
        earliest_decision=('decision_earliest','min'), status=('status', lambda values:'; '.join(sorted(set(values))))).reset_index()
    value_ci = primary('action_value_uncertainty')
    value_ci = value_ci[value_ci.route.isin(['anomaly','inactivity'])]
    text = f'''# TalentRoute: learner-support decisions under limited staff time

## Executive summary

An educational consulting team helps a university support coordinator decide which course cases staff should inspect first. TalentRoute estimates later outcomes using early activity and available assessments, then assigns review, alert or no action within a declared staffing budget. OULAD does not document current support procedures, so the workflow and effort costs are proposed assumptions.

At {params.minutes_per_100:g} minutes per hundred cases, the primary {chosen} queue contacts {int(reference.contact_n):,} of {int(reference.n):,} cases. It reaches {int(reference.adverse_contact_n):,} of {int(reference.adverse_n):,} later Fail/Withdrawn cases, compared with {int(rule.adverse_contact_n):,} for a simple score/inactivity rule. The difference is {int(reference.adverse_contact_n-rule.adverse_contact_n)} cases. The conditional gain interval is [{100*chosen_result.difference_vs_rule_low:.2f}, {100*chosen_result.difference_vs_rule_high:.2f}] percentage points. The operational companion retains mature prior enrolments and uses the same evaluation cases:

{table(headline, ['protocol','system','adverse_contact_n','coverage','difference_vs_rule_low','difference_vs_rule_high'])}

Source: `outputs/proposed_system.csv`. Table proportions use 0–1 units. The primary design excludes overlapping identities from training; the operational companion retains their earlier records. Neither is a new independent test.

**Evidence status.** These are post-feedback development results. The historical 2014J test has already been examined and is excluded from this revision. No unseen cohort is available. Final held-out confirmation remains unsatisfied; more seeds, new splits and software tests cannot restore it. Intervals condition on fitted predictions/actions and omit fitting and selection uncertainty. Historical targeting does not establish prevented failures, financial return or treatment benefit.

The connected anomaly reserve changes actions but its paired coverage interval {anomaly_text}. Therefore {recommended_reserve}. The coordinator must validate effort assumptions and coordinate repeated learners before actual outreach.

{warning_text}

## Problem recap and changes since the intermediate report

The owner is a learner-support coordinator assisted by an educational consulting team. The practical need is to make scarce staff time, excluded cases and alternative plans visible. Actual current university practice is unknown; the constructed score/inactivity comparator is a plausible alternative, not a measured institutional baseline. Corporate employee transfer would require different data and validation.

A review means inspecting one course-enrolment case. An alert is a shorter staff-mediated check. They are exclusive actions in this proposed queue. Multiple courses may belong to one person, so staff must coordinate contacts. The primary list contains {int(transitions.iloc[0].unique_students_contacted)} people across {int(reference.contact_n)} cases. It is not a deduplicated outreach schedule.

The Intermediate commitments remain: classification, engagement outlier detection, constrained decisions, reconciliation, warning profiles and course/segment analysis. Feedback led to separate review routes instead of blending incompatible scores, action-level counts, course/gender audits, a returning-learner companion and one pipeline/app. Calendar checks also changed training: some historical training outcomes were not yet mature at the intended decision date. The new population differs from the old submission; their scores are not before/after evidence of improvement.

## Proposed system

```mermaid
flowchart LR
 A[Available early-course features] --> B[Train-only transformations]
 B --> C[Three-class classifier]
 B --> D[Engagement Isolation Forest]
 C --> E[Risk-ranked queue]
 D -. Experimental review reserve .-> F[Common staff-time constraint]
 E --> F
 F --> G[Review / alert / no action]
 G --> H[Coordinator checks workload and groups]
```

Logistic regression tests a simple relationship; a bounded tree and two boosting capacities test alternatives. Three logistic penalties test sensitivity to regularization. Isolation Forest ranks unusual engagement without invented anomaly labels. Its percentile is not an outcome probability. It reserves existing review places, then the classifier fills remaining reviews and alerts. The final recommendation follows measured targeting rather than forcing the second family to succeed. Improvements concern decision validity and analysis, not adding complexity.

The budget is {params.minutes_per_100:g} minutes per hundred cases, with assumed {params.review_minutes:g}-minute reviews and {params.alert_minutes:g}-minute alerts. An initial alert-budget reservation and a {params.alert_learner_cap:.0%} alert-place cap determine whole-action capacities. Experimental routes reserve {params.reserve_fraction:.0%} of review places. The app changes these assumptions. Source: `outputs/parameters.csv`. No clustering or probability/percentile averaging is used.

## Evaluation setup and results

OULAD supplies actual Success (Pass/Distinction), Fail and Withdrawn outcomes. Predictors stop at day 28. Scores require an assumed seven-day publication lag; actual release timestamps are unavailable. IDs, demographics and outcomes are excluded from predictors. Imputation, scaling, encoding and detector reference ranks fit training only. Unequal activity windows are totals, not normalized daily trends.

Training uses mature 2013B outcomes; 2013J courses had not finished at the early 2014B decision point. Calendar bounds include unknown start days and assumed result-release delays:

{table(calendar)}

Source: `outputs/label_availability.csv`. Metadata bounds do not establish actual result publication dates.

{table(read('populations'), ['protocol','split','n','students','adverse_n','prior_enrolment_n','modules','train_validation_identity_overlap'])}

Source: `outputs/populations.csv`. Identity-disjoint training is a generalization audit, not the proposed operational training population. The companion retains mature prior records. Unseen courses receive all-zero course dummy columns through `handle_unknown='ignore'`; this avoids an encoding error but provides no learned course effect or safety guarantee.

**Primary ML metric:** adverse-outcome average precision (AP), because the task ranks cases for scarce outreach and must account for both missed adverse outcomes and false flags across thresholds. **Primary decision metric:** adverse coverage under the common staffing budget, because the coordinator needs to know how many later Fail/Withdrawn cases the affordable queue reaches. This is targeting recall, not prevented failures. Action-specific counts expose the different review and alert workloads; their benefits remain unmeasured. Brier score is a secondary probability-error diagnostic. Fail and Withdrawn retain separate predictions and metrics in `outputs/model_comparison.csv`. Detector AP measures relevance to adverse outcomes, not anomaly accuracy, because anomaly labels do not exist.

{table(scores, ['model','adverse_average_precision','average_precision_low','average_precision_high','adverse_prevalence','adverse_brier','macro_f1'])}

Sources: `outputs/model_comparison.csv`, `outputs/model_intervals.csv`. AP intervals are conditional student-cluster bootstrap intervals.

{table(selection, ['model','adverse_contact_n','coverage','adverse_average_precision','selected_development_candidate'])}

Source: `outputs/development_selection.csv`. The bounded selection rule maximizes development coverage, then AP, then fixed candidate order. It was recorded after earlier findings were known. The selected model is {chosen} and {gain_text} against the original good-enough coverage criterion on development data only; the logistic alternatives differ by {int(selection[selection.model.str.startswith('logistic')].adverse_contact_n.max()-selection[selection.model.str.startswith('logistic')].adverse_contact_n.min())} reached adverse cases. Boosting reaches {int(boost.adverse_contact_n.min())}–{int(boost.adverse_contact_n.max())}, versus {int(rule.adverse_contact_n)} for the rule. Exact CPU-platform boosting results may vary; regenerate outputs and conclusions together.

{table(counts)}

Source: `outputs/selection_stability.csv`. Fifty overlapping student-group half-splits choose on one half and assess on the other, keeping earlier-cohort fits fixed. Mean assessed gain is {100*splits.selected_minus_rule.mean():.2f} points, empirical spread [{100*split_low:.2f}, {100*split_high:.2f}]. This spread is not a confidence interval. It reuses examined data and does not change the selected model. Frequent C=0.1 selection shows the exact penalty is not decisive; the recorded C=1 choice remains frozen.

**Availability and selection remediation.** A pre-recorded retrospective audit removes every assessment-derived predictor, including score summaries, submission counts, lateness and missing-score indicators. The assessment-free model therefore does not rely on assumed score-release dates. Engagement and enrolment context remain subject to their stated day-28 definitions.

Both this model and an assessment-enabled comparator select among the existing six candidates using three learner-grouped folds within 2013B only. Preprocessing is refitted inside each fold; selection maximizes mean coverage, then AP. Only after selection and full earlier-cohort fitting is 2014B evaluated. The assessment-free variant is retained on availability grounds regardless of its score. No 2014J data is used.

{table(availability, ['protocol','variant','selected_model','adverse_average_precision','coverage','adverse_contact_n','inactivity_coverage','difference_low','difference_high'])}

Sources: `configs/availability_audit.json`, `outputs/availability_selection.csv`, `outputs/availability_audit.csv`. Intervals compare fixed model actions with an assessment-free inactivity queue under the same capacity. This removes evaluation labels from the candidate-selection step, but cannot erase prior analyst exposure to 2014B or to the original feature design. It is retrospective temporal evaluation, not independent confirmation. Report the lost targeting performance as the price of removing uncertain assessment availability. The app exposes this model separately; the original results above remain the historical development comparison.

## Ablation

Coverage is adverse-outcome recall among contacted cases. With equal contact counts, precision is an algebraic restatement, not independent evidence. Review-tier counts distinguish the more intensive action:

{table(count_metrics, ['route','coverage','contact_precision','adverse_reviewed','review_success_n','alert_fail_n','alert_withdrawn_n','staff_minutes'])}

Source: `outputs/review_tier_counts.csv`. Later-successful flagged cases are observable counts, not proof that support was unnecessary. Reviews and alerts have no measured intervention effects in OULAD.

![Paired route differences](../outputs/figures/ablation.png)

{table(transitions, ['route','changed_action_n','new_contact_n','lost_contact_n','alert_to_review_n','reserved_outside_original_contacts_n'])}

Sources: `outputs/policy_intervals.csv`, `outputs/action_transitions.csv`. The anomaly interval {anomaly_text}: [{100*interval.difference_low:.2f}, {100*interval.difference_high:.2f}] points. At this reserve size, course and inactivity controls change {int(transitions[transitions.route.eq('course')].changed_action_n.iloc[0])} and {int(transitions[transitions.route.eq('inactivity')].changed_action_n.iloc[0])} actions. They are weak perturbations here, not evidence that every alternative route is equivalent.

{table(baseline, ['baseline','average_precision','coverage','contact_precision'])}

{table(detector, ['detector','outcome_relevance_average_precision'])}

Sources: `outputs/baselines.csv`, `outputs/detector_comparison.csv`. The detector result concerns this reserve, population and objective. Unusual engagement could be high or low; that is a possible explanation, not a tested cause of the result.

## Sensitivity and stability

{table(pivot, ['protocol','parameter','value','risk_minus_rule_pp','anomaly_minus_risk_pp'])}

Sources: `outputs/sensitivity.csv`, `outputs/sensitivity_comparison.csv`. Each comparison uses the same budget/cost settings. For score-cutoff sweeps, the rule uses the same classifier eligibility mask but its own ordering; it is a shared-gate comparison, not a standalone rule threshold. At cutoff zero the baseline is independent of classifier eligibility.

{sensitivity_text}

These sweep differences are point estimates. No uncertainty intervals were estimated for the sweeps, so positive differences at all tested settings do not establish a statistically robust advantage.

{gate_text} {alert_text} Unchanged controls are reported as non-binding. These ranges are assumptions, not measured institutional costs. Larger budgets can improve reach without improving the model. Three seeds and two training-population protocols check stability, not cross-institution validity.

![Budget comparison](../outputs/figures/budget_curve.png)

{table(calibration_main, ['protocol','group','n','mean_predicted','observed_rate','prediction_minus_observed','brier','brier_skill_vs_group_prevalence'])}

Source: `outputs/calibration_diagnostics.csv`. Mean prediction minus observed rate describes over/underprediction in these samples. Brier skill compares with each group's observed prevalence as a descriptive reference, not a deployable fitted baseline. A score cutoff is not a guarantee of calibrated individual risk. Calibration diagnostics cannot identify zero-encoding or missingness as the cause of group differences. No recalibration or new model search is performed.

{table(calibration_courses, ['group','n','mean_predicted','observed_rate','prediction_minus_observed','brier_skill_vs_group_prevalence'])}

Source: `outputs/calibration_diagnostics.csv`. Course-level diagnostics separate score reliability from workload allocation. A small mean gap alone cannot establish calibration; errors can cancel. GGG's overprediction accompanies concentrated workload, whereas EEE's overprediction does not imply concentrated workload. These observations motivate auditing scores and course context, not automatic course exclusions.

{table(primary('workload_stress'), ['review_minutes','alert_minutes','frozen_required_minutes','shortfall_minutes','deferred_n','retained_coverage','replanned_coverage'])}

Source: `outputs/workload_stress.csv`. Freeze the original queue before increasing effort. The example contingency retains original alerts first, then the highest-risk reviews that fit; remaining cases are deferred. It may retain a lower-risk alert before a higher-risk review. Replanning provides a separate comparison under the same increased costs. Feasibility is not optimal intervention value.

## Deeper analyses

**1. Cross-model reconciliation.** Equal-quota interleaving combines classifier, anomaly and inactivity lists, skips duplicates and keeps capacity fixed. It differs from a small review reserve.

{table(reconciled, ['policy','coverage','contact_precision','review_success_n'])}

Source: `outputs/reconciliation.csv`. Reconciliation reaches {reconciled_row.coverage:.1%}, compared with {reference.coverage:.1%} for risk ranking. This {'does not support' if reconciled_row.coverage<=reference.coverage else 'supports only an exploratory case for'} replacing the queue on these development outcomes.

**2. Warning-positive profiles.** Compare later outcomes among flagged cases, retaining available-score denominators:

{table(profiles, ['observed_outcome','n','score_observed_n','score_median_observed','inactivity_median','no_early_assessment_rate'])}

Source: `outputs/warning_profiles.csv`. Only {int(profile_fail.score_observed_n)} of {int(profile_fail.n)} flagged Fail cases have an early score. Staff should check assessment schedules, submissions and marking availability before interpreting missingness. No score is not synonymous with non-submission. These profiles explain why a warning needs review; they do not establish resilience or an effective intervention.

**3. Course specialists and segment-sensitive decisions.** Fit specialists only where training class support permits; otherwise use the global logistic model. Both sides use the same fixed classifier family to isolate specialization.

{table(specialists, ['model','average_precision','coverage','contact_precision'])}

Source: `outputs/specialists.csv`. AP moves from {global_row.average_precision:.3f} to {specialist_row.average_precision:.3f}; coverage moves from {global_row.coverage:.1%} to {specialist_row.coverage:.1%}. {'No observed coverage gain supports extra specialist maintenance.' if specialist_row.coverage<=global_row.coverage else 'Any coverage gain requires further confirmation before extra maintenance is justified.'}

{table(course, ['protocol','segment','seen_in_training','n','adverse_n','review_n','alert_n','coverage','coverage_low','coverage_high','contact_precision','minutes_share','review_success_n'])}

Source: `outputs/segments.csv`. GGG receives {ggg.minutes_share:.1%} of staff minutes for {ggg.n/reference.n:.1%} of cases, reaching {int(ggg.adverse_contact_n)}/{int(ggg.adverse_n)} adverse cases at {ggg.contact_precision:.1%} contact precision. It contains {int(ggg.review_success_n)} of {int(reference.review_success_n)} later-successful reviewed cases. DDD reaches {int(ddd.adverse_contact_n)}/{int(ddd.adverse_n)} at {ddd.contact_precision:.1%} precision. This concentration needs a course-level audit. Causes and action value are untested. The historical GGG failure used a different population, so this is not a direct improvement claim.

{table(gender, ['segment','n','adverse_n','contact_n','adverse_contact_n','coverage','contact_precision','review_success_n'])}

{table(within_gap, ['module','gender','n','adverse_n','coverage','coverage_low','coverage_high','contact_precision'])}

Sources: `outputs/segments.csv`, `outputs/course_gender.csv`. The largest absolute within-course coverage gap is in {largest} among interpretable groups. Report denominators and overlapping uncertainty; coverage similarity does not imply equal precision or causal fairness. Protected attributes remain audit-only.

![Course queue composition](../outputs/figures/queue_composition.png)
![Within-course gender coverage](../outputs/figures/gender_by_course.png)

{table(returning, ['segment','n','adverse_n','coverage','coverage_low','coverage_high'])}

Source: `outputs/segments.csv`. Prior-enrolment groups describe the operational companion, not a new test cohort.

## Insights and recommendations

**Main findings.** The selected queue reaches more adverse cases than the constructed rule under the default budget, but the gain is modest and conditional on this development population. The anomaly reserve has no established additional coverage benefit. Course specialists do not improve coverage despite a slightly higher AP. More complicated models and more detection layers therefore do not automatically improve the staffing decision.

**Recommendations and conditions.** When score publication cannot be verified, use the assessment-free mode rather than assuming scores were available. Its lower coverage is an explicit trade-off, and its interval does not establish a gain over inactivity. If timestamped score availability is later established, reassess the assessment-enabled route prospectively. Retain the frozen classifier as a provisional prioritization tool and {recommended_reserve}. Recompute the queue when actual staff effort changes: the workload stress test shows that a previously feasible list can exceed capacity. A positive budget-sweep point estimate is insufficient to promise a gain at a new institution or staffing level. Inspect course-level coverage, precision and time shares alongside the aggregate result, especially GGG's concentration and DDD's missed adverse cases. Do not interpret the score cutoff as a validated individual probability threshold. Before contacting a flagged case, check assessment availability and the learner's context.

**Preference scenarios, not intervention returns.**

{table(value_ci, ['route','withdrawn_value','preference_difference','difference_low','difference_high'])}

Sources: `outputs/action_value_uncertainty.csv`, `outputs/action_value_scenarios.csv`, `outputs/action_break_even.csv`. Declared Fail/Withdrawn weights, review/alert weights and successful-case flag burdens use observed outcome counts after allocation. These are preference scenarios, not estimated treatment benefit or ROI. Weights should come from stakeholders, not be optimized to favor a route. Exact crossovers do not establish a statistically reliable preference.

**What failed and what replaces it**

| Trial or assumption | Finding | Response |
| --- | --- | --- |
| Extra classifier complexity | Boosting reaches {int(boost.adverse_contact_n.min())}–{int(boost.adverse_contact_n.max())} versus {int(reference.adverse_contact_n)} for the selected queue. | Retain the recorded {chosen} choice; no expanded search. |
| Anomaly reserve | Paired interval {anomaly_text}. | {recommended_reserve}. |
| Averaging probability and anomaly percentile | They represent different quantities. | Separate capacity-controlled routes. |
| Historical training calendar | Some outcomes were not mature at the early checkpoint. | Use mature earlier outcomes and disclose changed population. |
| Unknown deadlines counted as on-time | Boundary test exposed the error. | Exclude unknown deadlines from lateness. |
| Identical CPU results | Boosting fits varied across hosts. | Regenerate evidence and flag changed conclusions. |

Start with a provisional review tool, not autonomous outreach. Ask the coordinator to confirm real effort, whether alerts precede or replace reviews, repeated-person handling and acceptable flag burdens. Collect actual delivery and outcomes before claims about learning benefits. This dataset cannot determine which action prevents failure.

The app's separate policy checker recomputes time, exclusive whole actions, declared action caps and score eligibility without calling the allocator or reading outcomes. Nine anonymous examples can be edited while other cases remain fixed. Before/after views show changed actions, workload and course composition. A single-case editor changes model inputs; it is a model-response experiment, not a causal counterfactual. Export omits identities, demographics and outcomes.

## Limitations and risks

Independent confirmation remains open: 2014J was previously examined, and repeated development splits do not restore an untouched test. Conditional intervals omit the full history of model and policy selection. The operational companion addresses repeated learners but is not an independent replication.

Unknown release times and sparse early assessments limit what an early warning can mean. Course drift and unequal score reliability can distort allocation even when aggregate coverage appears stable. Clicks need not indicate learning. Assumed effort and preference weights are not observed institutional costs or treatment effects; successful flagged cases do not prove unnecessary support. No punitive decision or automatic denial of support is justified. The unexecuted future protocol is in `docs/final_confirmation_plan.md`.

## Connection to the original problem and next steps

The original consulting question was how to prioritize limited learner support. This version answers who enters an affordable review queue using real educational outcomes; it does not yet answer which intervention is worth its cost. It preserves classification plus a separately evaluated anomaly route, temporal safeguards and common-budget comparisons, while making the unsuccessful additions visible.

The next step is coordinator review of the proposed workflow and effort assumptions, followed by prospective evaluation on genuinely new cases under a frozen protocol. Record who was offered which support, delivery time and subsequent outcomes. Assess intervention benefit with an appropriate prospective comparison before claiming prevented failure or financial returns. Until then, present the application as a reproducible research demonstration for human review, not a validated institutional service.

Data: [UCI OULAD](https://archive.ics.uci.edu/dataset/349/open+university+learning+analytics+dataset), Kuzilek, Hlosta and Zdrahal, CC BY 4.0. The download recipe checks pinned source hashes.
'''
    (ROOT/'docs/final_report.md').write_text(text)
    body = re.sub(r'```.*?```', '', text, flags=re.S)
    body = '\n'.join(line for line in body.splitlines() if not line.startswith('|') and not line.startswith('!['))
    print(f'Report generated: {len(body.split())} body words; tables/figures/code excluded.')


if __name__ == '__main__':
    run()
