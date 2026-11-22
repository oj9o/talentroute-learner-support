"""Explicit review routes under one common staffing budget, without score blending."""

from dataclasses import dataclass
import numpy as np
import json
from pathlib import Path

_DEFAULTS = json.loads((Path(__file__).resolve().parents[2] / "configs/policy.json").read_text())["decision_policy"]


@dataclass(frozen=True)
class Policy:
    minutes_per_100: float = _DEFAULTS["minutes_per_100"]
    review_minutes: float = _DEFAULTS["review_minutes"]
    alert_minutes: float = _DEFAULTS["alert_minutes"]
    alert_budget_fraction: float = _DEFAULTS["alert_budget_fraction"]
    alert_learner_cap: float = _DEFAULTS["alert_learner_cap"]
    reserve_fraction: float = _DEFAULTS["reserve_fraction"]
    risk_threshold: float = _DEFAULTS["risk_threshold"]

    def validate(self):
        for value in vars(self).values():
            if not np.isfinite(value):
                raise ValueError('Policy values must be finite')
        if self.minutes_per_100 < 0 or min(self.review_minutes, self.alert_minutes) <= 0:
            raise ValueError('Invalid budget or effort cost')
        for name in ['alert_budget_fraction', 'alert_learner_cap', 'reserve_fraction', 'risk_threshold']:
            if not 0 <= getattr(self, name) <= 1:
                raise ValueError(f'{name} must lie in [0, 1]')


def rank(values, tie_breaker):
    """Descending values, deterministic random tie-breaking unrelated to outcome."""
    values = np.asarray(values, dtype=float)
    if not np.isfinite(values).all():
        raise ValueError('Ranking scores must be finite')
    return np.lexsort((tie_breaker, -values))


def capacity(n, policy):
    policy.validate()
    budget = n * policy.minutes_per_100 / 100
    alert_reserve = min(budget * policy.alert_budget_fraction,
                        int(n * policy.alert_learner_cap) * policy.alert_minutes)
    review_n = min(n, int((budget - alert_reserve) // policy.review_minutes))
    alert_n = min(n - review_n, int(n * policy.alert_learner_cap),
                  int((budget - review_n * policy.review_minutes) // policy.alert_minutes))
    return review_n, alert_n, budget


def course_order(risk, modules, tie_breaker, seed=7101):
    """Round-robin courses; each course's candidates remain risk-ranked."""
    modules = np.asarray(modules)
    global_order = rank(risk, tie_breaker)
    module_order = np.random.default_rng(seed).permutation(sorted(set(modules)))
    queues = [global_order[modules[global_order] == module] for module in module_order]
    result = []
    for level in range(max(map(len, queues), default=0)):
        for queue in queues:
            if level < len(queue):
                result.append(queue[level])
    return np.asarray(result, dtype=int)


def allocate(risk, rarity, inactivity, modules, policy=Policy(), route='classifier', seed=7101, eligibility_mask=None):
    """Reserve human-review slots, then fill remaining capacity with risk ranking.

    The reserve is carved from review capacity, never added on top. Anomaly and
    inactivity ranks are alternative queues, not outcome probabilities. A global
    risk gate is optional; when it excludes cases, budget can remain unused.
    """
    risk = np.asarray(risk, dtype=float)
    n = len(risk)
    if any(len(values) != n for values in [rarity, inactivity, modules]):
        raise ValueError('Inputs must have matching row counts')
    if not np.isfinite(risk).all() or np.any((risk < 0) | (risk > 1)):
        raise ValueError('Risk must be a finite probability')
    review_n, alert_n, budget = capacity(n, policy)
    actions = np.zeros(n, dtype=int)
    reasons = np.full(n, 'outside_capacity', dtype=object)
    tie_breaker = np.random.default_rng(seed).random(n)
    risk_order = rank(risk, tie_breaker)
    eligible = risk >= policy.risk_threshold
    if eligibility_mask is not None:
        eligible = np.asarray(eligibility_mask)
        if eligible.shape != (n,) or eligible.dtype != np.dtype(bool):
            raise ValueError('Eligibility mask must contain one boolean per case')
    reasons[~eligible] = 'below_risk_gate'
    if route == 'classifier':
        alternative = np.array([], dtype=int)
    elif route == 'anomaly':
        alternative = rank(rarity, tie_breaker)
    elif route == 'inactivity':
        alternative = rank(inactivity, tie_breaker)
    elif route == 'random':
        alternative = np.random.default_rng(np.random.SeedSequence([seed, 1])).permutation(n)
    elif route == 'course':
        alternative = course_order(risk, modules, tie_breaker, seed)
    else:
        raise ValueError('Unknown review route')
    reserve_n = int(review_n * policy.reserve_fraction) if route != 'classifier' else 0
    reserve = alternative[eligible[alternative]][:reserve_n]
    actions[reserve] = 2
    reasons[reserve] = route + '_review'
    available = risk_order[eligible[risk_order] & (actions[risk_order] == 0)]
    reviewed = available[:review_n - len(reserve)]
    actions[reviewed] = 2
    reasons[reviewed] = 'risk_review'
    available = risk_order[eligible[risk_order] & (actions[risk_order] == 0)]
    alerted = available[:alert_n]
    actions[alerted] = 1
    reasons[alerted] = 'risk_alert'
    cost = (actions == 2).sum() * policy.review_minutes + (actions == 1).sum() * policy.alert_minutes
    if cost > budget + 1e-8:
        raise AssertionError('Staffing budget exceeded')
    return actions, reasons


def observed_metrics(target, actions, policy=Policy()):
    """Outcome-targeting counts; never causal intervention effects."""
    target = np.asarray(target)
    actions = np.asarray(actions)
    adverse = target != 'Success'
    contacted = actions > 0
    result = {
        'n': len(target), 'adverse_n': int(adverse.sum()),
        'contact_n': int(contacted.sum()),
        'adverse_contact_n': int((adverse & contacted).sum()),
        'coverage': float((adverse & contacted).sum() / adverse.sum()) if adverse.any() else np.nan,
        'contact_precision': float(adverse[contacted].mean()) if contacted.any() else np.nan,
        'staff_minutes': float((actions == 2).sum() * policy.review_minutes + (actions == 1).sum() * policy.alert_minutes),
    }
    for action, name in [(2, 'review'), (1, 'alert'), (0, 'no_action')]:
        selected = actions == action
        result[name + '_n'] = int(selected.sum())
        for outcome in ['Success', 'Fail', 'Withdrawn']:
            result[name + '_' + outcome.lower() + '_n'] = int((selected & (target == outcome)).sum())
    return result


def retain_within_budget(actions, risk, policy, seed=7101):
    """A declared contingency: retain original alerts first, then original reviews.

    Each queue is risk-ranked. Defer cases that do not fit; do not introduce new
    cases or convert action types. This example is not an optimal-value solver.
    """
    actions = np.asarray(actions)
    risk = np.asarray(risk, dtype=float)
    if len(actions) != len(risk) or not np.isin(actions, [0, 1, 2]).all():
        raise ValueError('Expected matching risk and valid action arrays')
    remaining = capacity(len(actions), policy)[2]
    order = rank(risk, np.random.default_rng(seed).random(len(actions)))
    retained = np.zeros(len(actions), dtype=int)
    for action, effort in [(1, policy.alert_minutes), (2, policy.review_minutes)]:
        original = order[actions[order] == action]
        chosen = original[:int((remaining + 1e-8) // effort)]
        retained[chosen] = action
        remaining -= len(chosen) * effort
    return retained
