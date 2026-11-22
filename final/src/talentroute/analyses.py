"""The three promised analyses and conditional action-value scenarios."""

from dataclasses import dataclass, replace
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

from .data import ROOT, split_frames
from .decision import Policy, allocate, capacity, observed_metrics, rank, retain_within_budget
from .evaluation import frame_actions, historical_selected_model
from .models import FEATURES, classifier, risk_from


@dataclass(frozen=True)
class Values:
    """Preference-unit scenarios, not estimated causal effects or financial ROI."""
    fail_value: float = 1
    withdrawn_value: float = 1
    review_weight: float = 3
    alert_weight: float = 1
    review_success_burden: float = 0.5
    alert_success_burden: float = 0.05
    effort_units_per_minute: float = 0.01


def assumed_value(counts, values=Values()):
    """Apply external weights to observed outcomes reached, never to model scores."""
    if any(not np.isfinite(x) or x < 0 for x in vars(values).values()):
        raise ValueError('Scenario weights must be finite and nonnegative')
    review_targeting = counts['review_fail_n'] * values.fail_value + counts['review_withdrawn_n'] * values.withdrawn_value
    alert_targeting = counts['alert_fail_n'] * values.fail_value + counts['alert_withdrawn_n'] * values.withdrawn_value
    burden = (counts['review_success_n'] * values.review_success_burden +
              counts['alert_success_n'] * values.alert_success_burden +
              counts['staff_minutes'] * values.effort_units_per_minute)
    return values.review_weight * review_targeting + values.alert_weight * alert_targeting - burden


def break_even(candidate, reference, values=Values()):
    """Solve the review-weight crossover, holding every other preference fixed.

    Delta value = intercept + slope * review_weight. A positive slope favors
    the candidate above the crossover; a negative slope favors it below.
    """
    zero = replace(values, review_weight=0)
    one = replace(values, review_weight=1)
    intercept = assumed_value(candidate, zero) - assumed_value(reference, zero)
    slope = (assumed_value(candidate, one) - assumed_value(reference, one)) - intercept
    crossing = -intercept / slope if abs(slope) > 1e-10 else np.nan
    if abs(slope) < 1e-10:
        region = 'equal' if abs(intercept) < 1e-10 else ('always_above' if intercept > 0 else 'always_below')
    elif crossing < 0:
        region = 'always_above_for_nonnegative_weights' if slope > 0 else 'always_below_for_nonnegative_weights'
    else:
        region = 'above_crossover' if slope > 0 else 'below_crossover'
    return {'delta_intercept': intercept, 'delta_slope': slope,
            'review_weight_break_even': crossing, 'candidate_preferred_region': region}


def route_changes(frame, reference, candidate, reasons):
    """Explain equal coverage using contact membership and action transitions."""
    adverse = frame.target.ne('Success').to_numpy()
    reserved = np.array([str(reason).endswith('_review') and reason != 'risk_review'
                         for reason in reasons])
    return {
        'changed_action_n': int((reference != candidate).sum()),
        'new_contact_n': int(((reference == 0) & (candidate > 0)).sum()),
        'lost_contact_n': int(((reference > 0) & (candidate == 0)).sum()),
        'new_adverse_contact_n': int(((reference == 0) & (candidate > 0) & adverse).sum()),
        'lost_adverse_contact_n': int(((reference > 0) & (candidate == 0) & adverse).sum()),
        'alert_to_review_n': int(((reference == 1) & (candidate == 2)).sum()),
        'review_to_alert_n': int(((reference == 2) & (candidate == 1)).sum()),
        'reserved_review_n': int(reserved.sum()),
        'reserved_outside_original_contacts_n': int((reserved & (reference == 0)).sum()),
        'unique_students_contacted': int(frame.loc[candidate > 0, 'id_student'].nunique()),
        'multiple_contact_students': int(frame.loc[candidate > 0, 'id_student'].value_counts().gt(1).sum()),
    }


def reconciliation(frame, model=None):
    """Round-robin classifier/detector/inactivity lists at the SAME contact quota."""
    rng = np.random.default_rng(7101)
    tie = rng.random(len(frame))
    orders = [rank(frame[name], tie) for name in [model or historical_selected_model(), 'rarity', 'inactive_days']]
    reviews, alerts, _ = capacity(len(frame), Policy())
    chosen, seen = [], set()
    pointers = [0, 0, 0]
    while len(chosen) < reviews + alerts:
        for layer, order in enumerate(orders):
            while pointers[layer] < len(order) and int(order[pointers[layer]]) in seen:
                pointers[layer] += 1
            if pointers[layer] < len(order):
                index = int(order[pointers[layer]])
                seen.add(index)
                chosen.append(index)
            if len(chosen) == reviews + alerts:
                break
    actions = np.zeros(len(frame), dtype=int)
    actions[chosen[:reviews]] = 2
    actions[chosen[reviews:]] = 1
    return actions


def value_difference_interval(frame, candidate, reference, values, repetitions=300):
    """Paired learner-cluster interval for fixed-action preference differences.

    This resamples contributions, not a newly allocated budget. It omits model
    fitting and selection uncertainty and is not an intervention-effect interval.
    """
    def contributions(actions):
        outcome_value = np.where(frame.target.eq('Fail'), values.fail_value,
                                 np.where(frame.target.eq('Withdrawn'), values.withdrawn_value, 0))
        success = frame.target.eq('Success').to_numpy()
        review = np.asarray(actions) == 2
        alert = np.asarray(actions) == 1
        return (outcome_value * (review * values.review_weight + alert * values.alert_weight)
                - success * (review * values.review_success_burden + alert * values.alert_success_burden)
                - values.effort_units_per_minute * (review * Policy().review_minutes + alert * Policy().alert_minutes))
    _, group = np.unique(frame.id_student, return_inverse=True)
    difference = np.bincount(group, weights=contributions(candidate) - contributions(reference))
    sampled = np.random.default_rng(7101).integers(0, len(difference), (repetitions, len(difference)))
    low, high = np.quantile(difference[sampled].sum(axis=1), [.025, .975])
    return {'preference_difference': difference.sum(), 'difference_low': low, 'difference_high': high}


def review_route_analysis(frame, protocol, model=None):
    """Separate action changes, crossover arithmetic and conditional uncertainty."""
    transition_rows, crossover_rows, uncertainty_rows = [], [], []
    reference, _ = frame_actions(frame, model=model)
    reference_counts = observed_metrics(frame.target, reference)
    for route in ['classifier', 'anomaly', 'inactivity', 'course', 'random']:
        actions, reasons = frame_actions(frame, route, model=model)
        counts = observed_metrics(frame.target, actions)
        transition_rows.append({'protocol': protocol, 'route': route,
                                **route_changes(frame, reference, actions, reasons), **counts})
        for withdrawn_value in [1, 2]:
            values = Values(withdrawn_value=withdrawn_value)
            crossover_rows.append({'protocol': protocol, 'route': route,
                                   'reference_route': 'classifier', **vars(values),
                                   **break_even(counts, reference_counts, values)})
            uncertainty_rows.append({'protocol': protocol, 'route': route, **vars(values),
                                     **value_difference_interval(frame, actions, reference, values)})
    return transition_rows, crossover_rows, uncertainty_rows


def reconciliation_analysis(frame, protocol, model=None):
    """Compare equal contact quotas, overall and by course."""
    reconciliation_rows = []
    reconciled = reconciliation(frame, model)
    reference, _ = frame_actions(frame, model=model)
    for name, actions in [('round_robin_layers', reconciled), ('classifier', reference)]:
        for module in ['ALL'] + sorted(frame.code_module.unique()):
            mask = np.ones(len(frame), dtype=bool) if module == 'ALL' else frame.code_module.eq(module).to_numpy()
            reconciliation_rows.append({'protocol': protocol, 'policy': name, 'module': module,
                                        **observed_metrics(frame.target[mask], actions[mask])})
    return reconciliation_rows


def specialist_analysis(frame, train, protocol):
    """Fit only training-eligible specialists and compare against global logistic."""
    specialist_rows, eligibility = [], []
    # Preserve the promised training-eligible course specialist comparison.
    # This is an explicitly exploratory follow-up, not a new selection claim.
    global_model = classifier('logistic', 7101).fit(train[FEATURES], train.target)
    hybrid, _ = risk_from(global_model, frame)
    for module in sorted(frame.code_module.unique()):
        local = train.loc[train.code_module.eq(module)]
        counts = local.target.value_counts().reindex(['Success', 'Fail', 'Withdrawn'], fill_value=0)
        can_fit = len(local) >= 300 and counts.min() >= 30
        eligibility.append({'protocol': protocol, 'module': module, 'training_n': len(local),
                            'smallest_class_n': counts.min(), 'specialist_fitted': can_fit})
        mask = frame.code_module.eq(module).to_numpy()
        if can_fit:
            model = classifier('logistic', 7101).fit(local[FEATURES], local.target)
            hybrid[mask], _ = risk_from(model, frame.loc[mask])
    hybrid_actions, _ = allocate(hybrid, frame.rarity, frame.inactive_days, frame.code_module)
    global_actions, _ = frame_actions(frame, model='logistic')
    for name, score, actions in [('module_logistic', hybrid, hybrid_actions),
                                 ('global_logistic', frame.logistic.to_numpy(), global_actions)]:
        for module in ['ALL'] + sorted(frame.code_module.unique()):
            mask = np.ones(len(frame), dtype=bool) if module == 'ALL' else frame.code_module.eq(module).to_numpy()
            specialist_rows.append({'protocol': protocol, 'model': name, 'module': module,
                                    'average_precision': average_precision_score(frame.target[mask].ne('Success'), score[mask]),
                                    **observed_metrics(frame.target[mask], actions[mask])})
    return specialist_rows, eligibility


def conditional_value_analysis(frame, protocol, model=None):
    """Sweep declared action preferences; do not fit causal treatment benefits."""
    value_rows = []
    for alert_share in [0, 0.05, 0.1, 0.2]:
        policy = Policy(alert_budget_fraction=alert_share)
        for route in ['classifier', 'anomaly', 'inactivity', 'course']:
            actions, _ = frame_actions(frame, route, policy, model=model)
            counts = observed_metrics(frame.target, actions, policy)
            for review_weight in [1, 3, 10]:
                for withdrawn_value in [1, 2]:
                    values = Values(review_weight=review_weight, withdrawn_value=withdrawn_value)
                    value_rows.append({'protocol': protocol, 'route': route,
                                       'alert_budget_fraction': alert_share,
                                       'alert_learner_cap': policy.alert_learner_cap,
                                       **vars(values), **counts,
                                       'assumed_preference_units': assumed_value(counts, values),
                                       'causal_benefit_estimated': False})
    return value_rows


def workload_stress(frame, actions, model, policy=Policy(), route='classifier'):
    """Freeze a case plan, stress effort, then compare deferral with replanning."""
    budget = capacity(len(frame), policy)[2]
    rows = []
    for review_multiplier in [1, 1.5, 2]:
        for alert_multiplier in [1, 1.5]:
            stressed = replace(policy, review_minutes=policy.review_minutes * review_multiplier,
                               alert_minutes=policy.alert_minutes * alert_multiplier)
            frozen = observed_metrics(frame.target, actions, stressed)
            retained = retain_within_budget(actions, frame[model], stressed)
            replanned, _ = frame_actions(frame, route, stressed, model=model)
            kept = observed_metrics(frame.target, retained, stressed)
            revised = observed_metrics(frame.target, replanned, stressed)
            rows.append({'review_multiplier': review_multiplier, 'alert_multiplier': alert_multiplier,
                         'review_minutes': stressed.review_minutes, 'alert_minutes': stressed.alert_minutes,
                         'budget_minutes': budget, 'frozen_required_minutes': frozen['staff_minutes'],
                         'shortfall_minutes': max(0, frozen['staff_minutes'] - budget),
                         'frozen_feasible': frozen['staff_minutes'] <= budget + 1e-8,
                         'deferred_n': int(((np.asarray(actions) > 0) & (retained == 0)).sum()),
                         'retained_coverage': kept['coverage'], 'retained_minutes': kept['staff_minutes'],
                         'replanned_coverage': revised['coverage'], 'replanned_minutes': revised['staff_minutes'],
                         'replanned_minus_retained': revised['coverage'] - kept['coverage']})
    return rows


def run():
    """Execute promised analyses on development data, never on the final test."""
    data = pd.read_csv(ROOT / 'data/processed/development.csv')
    results = {name: [] for name in ['reconciliation', 'specialists', 'specialist_eligibility',
                                   'action_value_scenarios', 'action_transitions',
                                   'action_break_even', 'action_value_uncertainty', 'workload_stress']}
    for protocol in ['identity_disjoint', 'operational']:
        frame = pd.read_csv(ROOT / f'data/processed/predictions_{protocol}_7101.csv')
        train, _ = split_frames(data, protocol)
        transitions, crossovers, uncertainty = review_route_analysis(frame, protocol)
        specialists, eligibility = specialist_analysis(frame, train, protocol)
        rows = dict(reconciliation=reconciliation_analysis(frame, protocol),
                    specialists=specialists, specialist_eligibility=eligibility,
                    action_value_scenarios=conditional_value_analysis(frame, protocol),
                    action_transitions=transitions, action_break_even=crossovers,
                    action_value_uncertainty=uncertainty,
                    workload_stress=[{'protocol': protocol, **row} for row in
                                     workload_stress(frame, frame_actions(frame)[0], historical_selected_model())])
        for name, records in rows.items():
            results[name].extend(records)
    for name, rows in results.items():
        output = pd.DataFrame(rows)
        output['routing_model'] = historical_selected_model()
        output.to_csv(ROOT / f'outputs/{name}.csv', index=False)
    print('Executed reconciliation, specialists and conditional action-value analysis.')


if __name__ == '__main__':
    run()
