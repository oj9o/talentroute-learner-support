"""Matched comparator and configuration regressions from the final review."""
from dataclasses import replace
import numpy as np
import pandas as pd
import pytest
from talentroute.decision import Policy, allocate, observed_metrics
from talentroute.evaluation import rule_actions


def test_rule_uses_changed_budget_and_shared_eligibility():
    frame = pd.DataFrame({'heuristic': np.arange(20), 'rarity': np.arange(20),
                          'inactive_days': np.arange(20), 'code_module': ['A']*20})
    policy = replace(Policy(), minutes_per_100=600, risk_threshold=.8)
    eligible = np.arange(20) < 3  # Opposes the heuristic order deliberately.
    actions = rule_actions(frame, policy=policy, eligibility_mask=eligible)
    assert not np.any(actions[~eligible])
    assert np.any(actions[eligible])
    counts = observed_metrics(np.array(['Fail']*20), actions, policy)
    assert counts['staff_minutes'] <= 120
    assert not rule_actions(frame, policy=replace(policy, minutes_per_100=0), eligibility_mask=eligible).any()


def test_eligibility_override_does_not_change_default_allocation():
    scores = np.linspace(0,1,50)
    args = (scores, scores[::-1], scores, ['A']*50)
    policy = replace(Policy(), risk_threshold=.4)
    original = allocate(*args, policy=policy)[0]
    shared = allocate(*args, policy=policy, eligibility_mask=scores>=.4)[0]
    np.testing.assert_array_equal(original, shared)
    with pytest.raises(ValueError, match='boolean'):
        allocate(*args, eligibility_mask=np.ones(50))


def test_policy_defaults_are_recorded_configuration():
    from talentroute.data import config
    assert vars(Policy()) == config()['decision_policy']
