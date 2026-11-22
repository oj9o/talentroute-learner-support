"""Matched-budget comparisons and student-cluster intervals on development data."""

from dataclasses import replace
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score
from .data import ROOT
from .decision import Policy, allocate, observed_metrics
from .models import CANDIDATES, REFERENCE, classifier

ROUTES = ['classifier', 'anomaly', 'inactivity', 'course', 'random']


def selected_model():
    """Read the single provisional choice produced by the recorded selection rule."""
    table = pd.read_csv(ROOT / 'outputs/development_selection.csv')
    chosen = table.loc[table.selected_development_candidate, 'model'].tolist()
    if len(chosen) != 1 or chosen[0] not in CANDIDATES:
        raise ValueError('Expected one valid development-selected model')
    return chosen[0]


def frame_actions(frame, route='classifier', policy=Policy(), seed=7101, model=None):
    model = selected_model() if model is None else model
    return allocate(frame[model], frame.rarity, frame.inactive_days, frame.code_module,
                    policy, route, seed)


def coverage_interval(frame, actions, reference=None, repetitions=300, seed=7101):
    """Bootstrap learners, keeping policy and actions fixed; conditional, exploratory CI."""
    adverse = frame.target.ne('Success').to_numpy()
    if not adverse.any():
        return np.nan, np.nan
    _, groups = np.unique(frame.id_student, return_inverse=True)
    denominator = np.bincount(groups, weights=adverse)
    contribution = adverse * (np.asarray(actions) > 0)
    if reference is not None:
        contribution = contribution.astype(float) - adverse * (np.asarray(reference) > 0)
    numerator = np.bincount(groups, weights=contribution)
    sample = np.random.default_rng(seed).integers(0, len(denominator), (repetitions, len(denominator)))
    counts = denominator[sample].sum(axis=1)
    ratios = numerator[sample].sum(axis=1)[counts > 0] / counts[counts > 0]
    return tuple(np.quantile(ratios, [0.025, 0.975]))


def evaluate():
    select_development_candidate()
    chosen = selected_model()
    comparisons, model_decisions, intervals, segments, composition, profiles = [], [], [], [], [], []
    ap_intervals, support_metrics = [], []
    for protocol in ['identity_disjoint', 'operational']:
        for seed in [7101, 7102, 7103]:
            frame = pd.read_csv(ROOT / f'data/processed/predictions_{protocol}_{seed}.csv')
            reference, _ = frame_actions(frame, seed=seed)
            for name in CANDIDATES:
                actions, _ = frame_actions(frame, seed=seed, model=name)
                model_decisions.append({'protocol': protocol, 'seed': seed, 'model': name,
                                        **observed_metrics(frame.target, actions)})
                if seed == 7101:
                    for unseen, group in frame.groupby('unseen_module'):
                        support_metrics.append({
                            'protocol': protocol, 'model': name, 'unseen_module': unseen,
                            'average_precision': average_precision_score(group.target.ne('Success'), group[name]),
                            **observed_metrics(group.target, actions[group.index]),
                        })
            for route in ROUTES:
                actions, reasons = frame_actions(frame, route, seed=seed)
                base = {'protocol': protocol, 'seed': seed, 'model': chosen, 'route': route}
                comparisons.append({**base, **observed_metrics(frame.target, actions)})
                if seed != 7101:
                    continue
                low, high = coverage_interval(frame, actions)
                diff_low, diff_high = coverage_interval(frame, actions, reference)
                intervals.append({**base, 'coverage_low': low, 'coverage_high': high,
                                  'difference_low': diff_low, 'difference_high': diff_high,
                                  'scope': 'fixed_actions_student_cluster_bootstrap_exploratory'})
                frame['action_' + route] = actions
                for dimension in ['code_module', 'gender', 'prior_enrolment', 'unseen_module']:
                    for value, group in frame.groupby(dimension, dropna=False):
                        selected = actions[group.index]
                        counts = observed_metrics(group.target, selected)
                        interpretable = len(group) >= 50 and counts['adverse_n'] >= 10
                        ci = coverage_interval(group, selected) if interpretable else (np.nan, np.nan)
                        segments.append({**base, 'dimension': dimension, 'segment': str(value),
                                         **counts, 'coverage_low': ci[0], 'coverage_high': ci[1],
                                         'interpretation_allowed': interpretable})
                for (module, gender), group in frame.groupby(['code_module', 'gender']):
                    selected = actions[group.index]
                    counts = observed_metrics(group.target, selected)
                    valid = len(group) >= 50 and counts['adverse_n'] >= 10
                    ci = coverage_interval(group, selected) if valid else (np.nan, np.nan)
                    composition.append({**base, 'module': module, 'gender': gender,
                                        **counts, 'coverage_low': ci[0], 'coverage_high': ci[1],
                                        'interpretation_allowed': valid,
                                        'no_early_assessment_rate': group.no_early_assessment.mean()})
                for outcome, group in frame.loc[actions > 0].groupby('target'):
                    profiles.append({**base, 'observed_outcome': outcome, 'n': len(group),
                                     'score_observed_n': group.score_mean.notna().sum(),
                                     'score_median_observed': group.score_mean.median(),
                                     'inactivity_median': group.inactive_days.median(),
                                     'no_early_assessment_rate': group.no_early_assessment.mean()})
            if seed == 7101:
                frame.to_csv(ROOT / f'data/processed/decisions_{protocol}.csv', index=False)
                ids, index = np.unique(frame.id_student, return_inverse=True)
                rng = np.random.default_rng(7101)
                for model in CANDIDATES:
                    values = []
                    for _ in range(200):
                        sampled = rng.integers(0, len(ids), len(ids))
                        weights = np.bincount(sampled, minlength=len(ids))[index]
                        values.append(average_precision_score(frame.target.ne('Success'), frame[model], sample_weight=weights))
                    lo, hi = np.quantile(values, [.025, .975])
                    ap_intervals.append({'protocol': protocol, 'model': model,
                                         'average_precision_low': lo, 'average_precision_high': hi,
                                         'scope': 'fixed_predictions_student_cluster_bootstrap_exploratory'})
    for name, records in [('policy_comparison', comparisons), ('model_decisions', model_decisions),
                          ('policy_intervals', intervals), ('segments', segments),
                          ('course_gender', composition), ('warning_profiles', profiles),
                          ('model_intervals', ap_intervals), ('seen_unseen_models', support_metrics)]:
        pd.DataFrame(records).to_csv(ROOT / f'outputs/{name}.csv', index=False)
    print('Development evaluations written; no final-test scoring.')


def rule_actions(frame, seed=7101, policy=Policy(), eligibility_mask=None):
    """Construct the score/inactivity comparator with the common budget."""
    scores = frame.heuristic.rank(method='average', pct=True).to_numpy()
    return allocate(scores, frame.rarity, frame.inactive_days, frame.code_module, policy=policy, seed=seed, eligibility_mask=eligibility_mask)[0]


def selection_assessment(selection, assessment):
    """Choose using one set of students, assess using the other; no fitting here."""
    if set(selection.id_student) & set(assessment.id_student):
        raise ValueError('Selection and assessment must contain different students')
    if any(part.target.ne('Success').nunique() < 2 for part in [selection, assessment]):
        raise ValueError('Both halves must contain successful and adverse outcomes')
    candidates = []
    for order, name in enumerate(CANDIDATES):
        actions, _ = frame_actions(selection, model=name)
        coverage = observed_metrics(selection.target, actions)['coverage']
        ap = average_precision_score(selection.target.ne('Success'), selection[name])
        candidates.append((coverage, ap, -order, name))
    winner = max(candidates)[-1]
    result = {'selected_model': winner,
              'selected_family': 'logistic' if winner.startswith('logistic') else
                                 'boosting' if winner.startswith('hgb') else 'tree'}
    policies = {
        'selected': frame_actions(assessment, model=winner)[0],
        'rule': rule_actions(assessment),
        'fixed_logistic': frame_actions(assessment, model='logistic')[0],
        'selected_anomaly': frame_actions(assessment, route='anomaly', model=winner)[0],
    }
    for name, actions in policies.items():
        counts = observed_metrics(assessment.target, actions)
        for key in ['coverage', 'contact_precision', 'staff_minutes', 'contact_n']:
            result[f'{name}_{key}'] = counts[key]
    result['selected_minus_rule'] = result['selected_coverage'] - result['rule_coverage']
    result['selected_minus_fixed'] = result['selected_coverage'] - result['fixed_logistic_coverage']
    result['anomaly_minus_selected'] = result['selected_anomaly_coverage'] - result['selected_coverage']
    result['assessment_budget_minutes'] = len(assessment) * Policy().minutes_per_100 / 100
    return result


def selection_stability(repetitions=50, seed=7104):
    """Overlapping student-group half-splits; an exploratory development diagnostic."""
    rows = []
    for protocol in ['identity_disjoint', 'operational']:
        frame = pd.read_csv(ROOT / f'data/processed/predictions_{protocol}_7101.csv')
        ids = np.sort(frame.id_student.unique())
        rng = np.random.default_rng(seed)
        for repeat in range(repetitions):
            chosen_ids = rng.permutation(ids)[:len(ids) // 2]
            mask = frame.id_student.isin(chosen_ids)
            selection = frame.loc[mask].reset_index(drop=True)
            assessment = frame.loc[~mask].reset_index(drop=True)
            mix = selection.code_module.value_counts(normalize=True).subtract(
                assessment.code_module.value_counts(normalize=True), fill_value=0)
            rows.append({'protocol': protocol, 'repeat': repeat + 1, 'split_seed': seed,
                         'selection_students': selection.id_student.nunique(),
                         'assessment_students': assessment.id_student.nunique(),
                         'selection_n': len(selection), 'assessment_n': len(assessment),
                         'assessment_adverse_n': assessment.target.ne('Success').sum(),
                         'selection_unseen_share': selection.unseen_module.mean(),
                         'assessment_unseen_share': assessment.unseen_module.mean(),
                         'largest_course_share_difference': mix.abs().max(),
                         **selection_assessment(selection, assessment)})
    pd.DataFrame(rows).to_csv(ROOT / 'outputs/selection_stability.csv', index=False)
    print('Selection/assessment split diagnostic written; no independent-test claim.')


def select_development_candidate():
    """Apply the recorded bounded rule; all selection evidence remains exploratory."""
    metrics = pd.read_csv(ROOT / 'outputs/model_comparison.csv')
    primary = pd.read_csv(ROOT / 'data/processed/predictions_identity_disjoint_7101.csv')
    decisions = [{'model': name, **observed_metrics(primary.target, frame_actions(primary, model=name)[0])}
                 for name in CANDIDATES]
    grid = metrics[(metrics.protocol == 'identity_disjoint') & (metrics.seed == 7101)].merge(
        pd.DataFrame(decisions), on='model')
    grid['candidate_order'] = grid.model.map({name: index for index, name in enumerate(CANDIDATES)})
    grid = grid.sort_values(['coverage', 'adverse_average_precision', 'candidate_order'],
                            ascending=[False, False, True])
    chosen = grid.iloc[0].model
    grid['selected_development_candidate'] = grid.model.eq(chosen)
    grid.to_csv(ROOT / 'outputs/development_selection.csv', index=False)
    settings = []
    for name in CANDIDATES:
        parameters = classifier(name, 7101)['model'].get_params()
        for key in ['C', 'max_depth', 'min_samples_leaf', 'max_leaf_nodes',
                    'l2_regularization', 'learning_rate', 'max_iter', 'early_stopping']:
            if key in parameters:
                settings.append({'model': name, 'parameter': key, 'value': parameters[key]})
    pd.DataFrame(settings).to_csv(ROOT / 'outputs/model_settings.csv', index=False)
    records = []
    for protocol in ['identity_disjoint', 'operational']:
        frame = pd.read_csv(ROOT / f'data/processed/predictions_{protocol}_7101.csv')
        rule = rule_actions(frame)
        risk_only, _ = frame_actions(frame, model=chosen)
        risk_counts = observed_metrics(frame.target, risk_only)
        for name, actions in [('score_inactivity_rule', rule),
                              ('fixed_boosting_reference', frame_actions(frame, model=REFERENCE)[0]),
                              ('selected_risk_queue', risk_only),
                              ('selected_with_anomaly', frame_actions(frame, 'anomaly', model=chosen)[0])]:
            counts = observed_metrics(frame.target, actions)
            low, high = coverage_interval(frame, actions)
            rule_low, rule_high = coverage_interval(frame, actions, rule)
            risk_low, risk_high = coverage_interval(frame, actions, risk_only)
            records.append({'protocol': protocol, 'model': chosen, 'system': name, **counts,
                            'coverage_low': low, 'coverage_high': high,
                            'difference_vs_rule_low': rule_low, 'difference_vs_rule_high': rule_high,
                            'difference_vs_selected_low': risk_low, 'difference_vs_selected_high': risk_high,
                            'original_rule_gate_met_exploratory': rule_low > 0,
                            'detector_gate_met_exploratory': (name == 'selected_with_anomaly' and risk_low > 0
                                and counts['contact_precision'] >= risk_counts['contact_precision'] - .02)})
    pd.DataFrame(records).to_csv(ROOT / 'outputs/proposed_system.csv', index=False)


def baselines():
    """Credible constructed comparators, not an observed university workflow."""
    rows = []
    for protocol in ['identity_disjoint', 'operational']:
        frame = pd.read_csv(ROOT / f'data/processed/predictions_{protocol}_7101.csv')
        for seed in [7101, 7102, 7103]:
            rng = np.random.default_rng(seed)
            for name, values in [('score_inactivity_rule', frame.heuristic),
                                 ('inactivity_rule', frame.inactive_days),
                                 ('random_order', rng.random(len(frame)))]:
                # Allocation uses only ordering here. These are not probabilities.
                order_scores = pd.Series(values).rank(method='average', pct=True).to_numpy()
                actions, _ = allocate(order_scores, frame.rarity, frame.inactive_days,
                                      frame.code_module, seed=seed)
                rows.append({'protocol': protocol, 'seed': seed, 'baseline': name,
                             'average_precision': average_precision_score(frame.target.ne('Success'), values),
                             **observed_metrics(frame.target, actions)})
    pd.DataFrame(rows).to_csv(ROOT / 'outputs/baselines.csv', index=False)


def sensitivity():
    """Vary five interpretable decision assumptions; other settings remain fixed."""
    rows = []
    settings = {
        'minutes_per_100': [150, 300, 600, 900],
        'review_minutes': [15, 30, 45, 60],
        'reserve_fraction': [0, 0.1, 0.2, 0.3],
        'risk_threshold': [0, 0.25, 0.5, 0.75],
        'alert_budget_fraction': [0, 0.1, 0.2, 0.4],
    }
    for protocol in ['identity_disjoint', 'operational']:
        frame = pd.read_csv(ROOT / f'data/processed/predictions_{protocol}_7101.csv')
        for parameter, values in settings.items():
            for value in values:
                policy = replace(Policy(), **{parameter: value})
                # The rule has ordinal ranks, not calibrated risk. For cutoff sweeps,
                # use the same classifier eligibility mask and compare ordering only.
                eligible = (frame[selected_model()] >= policy.risk_threshold).to_numpy()
                rule = rule_actions(frame, policy=policy, eligibility_mask=eligible)
                rows.append({'protocol': protocol, 'model': 'score_inactivity_rule',
                             'parameter': parameter, 'value': value, 'route': 'rule',
                             'eligibility': 'shared_classifier_cutoff',
                             **observed_metrics(frame.target, rule, policy)})
                for route in ROUTES:
                    actions, _ = frame_actions(frame, route, policy)
                    rows.append({'protocol': protocol, 'model': selected_model(), 'parameter': parameter, 'value': value,
                                 'route': route, **observed_metrics(frame.target, actions, policy)})
    pd.DataFrame(rows).to_csv(ROOT / 'outputs/sensitivity.csv', index=False)
    from .report import budget_figure
    budget_figure()
    print('Sensitivity: budget, review effort, reserve share, score cutoff and alert share.')


def calibration_diagnostics():
    """Descriptive checks of existing fitted scores; no calibration fit or reselection."""
    rows = []
    for protocol in ['identity_disjoint', 'operational']:
        frame = pd.read_csv(ROOT / f'data/processed/predictions_{protocol}_7101.csv')
        model = selected_model()
        actions = frame_actions(frame, model=model)[0]
        groups = {'all': np.ones(len(frame), dtype=bool),
                  'contacted': actions > 0,
                  'seen_courses': ~frame.unseen_module.to_numpy(),
                  'unseen_courses': frame.unseen_module.to_numpy()}
        groups.update({'course_' + str(m): frame.code_module.eq(m).to_numpy()
                       for m in sorted(frame.code_module.unique())})
        for group, mask in groups.items():
            sub = frame.loc[mask]
            y = sub.target.ne('Success').to_numpy(dtype=float)
            scores = sub[model].to_numpy()
            prevalence = y.mean()
            brier = np.mean((scores-y)**2)
            constant = prevalence*(1-prevalence)
            rows.append({'protocol': protocol, 'model': model, 'group': group,
                         'n': len(sub), 'adverse_n': int(y.sum()),
                         'mean_predicted': scores.mean(), 'observed_rate': prevalence,
                         'prediction_minus_observed': scores.mean()-prevalence,
                         'brier': brier, 'constant_prevalence_brier': constant,
                         'brier_skill_vs_group_prevalence': 1-brier/constant if constant else np.nan})
    pd.DataFrame(rows).to_csv(ROOT / 'outputs/calibration_diagnostics.csv', index=False)


if __name__ == '__main__':
    evaluate()
    sensitivity()
