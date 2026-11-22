"""Check a proposed queue from its actions, independently of the allocator.

No labels, model fitting, capacity() or allocate() are used here. Limits describe
our constructed staffing scenario, not a measured institutional workflow.
"""
import math
import numpy as np


def limits(n, policy):
    policy.validate()
    budget = n * policy.minutes_per_100 / 100
    alert_cap = math.floor(n * policy.alert_learner_cap)
    reserved = min(budget * policy.alert_budget_fraction, alert_cap * policy.alert_minutes)
    reviews = min(n, math.floor((budget - reserved) / policy.review_minutes))
    alerts = min(n - reviews, alert_cap,
                 math.floor((budget - reviews * policy.review_minutes) / policy.alert_minutes))
    return budget, reviews, alerts, reserved


def check_plan(risk, actions, policy):
    """Audit whole, exclusive actions and all declared scenario constraints."""
    risk = np.asarray(risk, dtype=float)
    actions = np.asarray(actions)
    if risk.ndim != 1 or actions.shape != risk.shape:
        raise ValueError('Provide one action for every course case')
    if not np.isfinite(risk).all() or ((risk < 0) | (risk > 1)).any():
        raise ValueError('Risk scores must be finite probabilities')
    budget, review_cap, alert_cap, reserved = limits(len(risk), policy)
    whole = bool(np.isin(actions, [0, 1, 2]).all())
    reviews, alerts = int((actions == 2).sum()), int((actions == 1).sum())
    used = reviews * policy.review_minutes + alerts * policy.alert_minutes
    below = int(((actions > 0) & (risk < policy.risk_threshold)).sum())
    checks = [
        {'rule': 'One whole action per case', 'passed': whole,
         'detail': 'Only No action, Alert or Review; never two actions for one case.'},
        {'rule': 'Staff time', 'passed': whole and used <= budget + 1e-8,
         'detail': f'{used:g} of {budget:g} minutes; {budget-used:g} minutes remaining.'},
        {'rule': 'Review places', 'passed': reviews <= review_cap,
         'detail': f'{reviews} of {review_cap} places used.'},
        {'rule': 'Alert places', 'passed': alerts <= alert_cap,
         'detail': f'{alerts} of {alert_cap} places used.'},
        {'rule': 'Model score cutoff', 'passed': below == 0,
         'detail': f'{below} selected cases below the {policy.risk_threshold:.0%} threshold.'},
    ]
    return {'feasible': all(c['passed'] for c in checks), 'checks': checks,
            'used_minutes': used, 'budget_minutes': budget,
            'remaining_minutes': budget-used, 'review_cap': review_cap,
            'alert_cap': alert_cap, 'initial_alert_reserve_minutes': reserved}


def apply_edits(actions, edits):
    """Only anonymous case positions and integer actions are accepted."""
    if not isinstance(edits, list) or len(edits) > 10:
        raise ValueError('Edit at most 10 cases at a time')
    result = np.asarray(actions).copy()
    seen = set()
    for edit in edits:
        if not isinstance(edit, dict) or set(edit) != {'index', 'action'}:
            raise ValueError('Each edit needs only a case index and action')
        index, action = edit['index'], edit['action']
        if type(index) is not int or not 0 <= index < len(result) or index in seen:
            raise ValueError('Case numbers must be valid and unique')
        if type(action) is not int or action not in (0, 1, 2):
            raise ValueError('Choose one whole action: 0, 1 or 2')
        seen.add(index)
        result[index] = action
    return result


def compare_actions(before, after, modules):
    before, after, modules = map(np.asarray, (before, after, modules))
    if before.shape != after.shape or before.shape != modules.shape:
        raise ValueError('Compare the same cases in the same order')
    return {'changed': int((before != after).sum()),
            'entered': int(((before == 0) & (after > 0)).sum()),
            'left': int(((before > 0) & (after == 0)).sum()),
            'alert_to_review': int(((before == 1) & (after == 2)).sum()),
            'review_to_alert': int(((before == 2) & (after == 1)).sum()),
            'courses': [{'module': str(module),
                         'before': int(((modules == module) & (before > 0)).sum()),
                         'after': int(((modules == module) & (after > 0)).sum())}
                        for module in sorted(set(modules))]}
