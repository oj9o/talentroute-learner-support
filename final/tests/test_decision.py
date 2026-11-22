import numpy as np
import pandas as pd
import pytest
from talentroute.decision import Policy, allocate, capacity


@pytest.mark.parametrize('budget', [0, 3, 150, 300, 600, 1200])
def test_routes_preserve_total_budget_and_matched_action_counts(budget):
    n = 113
    rng = np.random.default_rng(22)
    risk, rarity, inactivity = rng.random((3, n))
    modules = np.array(['A', 'B', 'C'])[np.arange(n) % 3]
    policy = Policy(minutes_per_100=budget)
    review_n, alert_n, total = capacity(n, policy)
    for route in ['classifier', 'anomaly', 'inactivity', 'random', 'course']:
        actions, _ = allocate(risk, rarity, inactivity, modules, policy, route)
        assert (actions == 2).sum() == review_n
        assert (actions == 1).sum() == alert_n
        assert review_n * policy.review_minutes + alert_n * policy.alert_minutes <= total


def test_gate_changes_contact_eligibility_without_changing_probability():
    risk = np.linspace(0, 1, 100)
    original = risk.copy()
    actions, _ = allocate(risk, 1-risk, risk, ['A']*100, Policy(risk_threshold=0.9), 'anomaly')
    assert not actions[risk < 0.9].any()
    np.testing.assert_array_equal(risk, original)


def test_anomaly_route_changes_real_decisions_at_fixed_capacity():
    risk = np.linspace(0, 1, 100)
    args = (risk, 1-risk, risk, ['A']*100)
    base, _ = allocate(*args, route='classifier')
    alternative, reasons = allocate(*args, route='anomaly')
    assert np.any(base != alternative)
    assert (reasons == 'anomaly_review').sum() == int((base == 2).sum() * 0.2)
    assert (alternative > 0).sum() == (base > 0).sum()


def test_zero_reserve_exactly_recovers_classifier_decisions():
    risk = np.linspace(0, 1, 100)
    args = (risk, 1-risk, risk, ['A']*100)
    base, _ = allocate(*args)
    for route in ['anomaly', 'inactivity', 'course', 'random']:
        actions, _ = allocate(*args, policy=Policy(reserve_fraction=0), route=route)
        np.testing.assert_array_equal(actions, base)


def test_repeatability_includes_ties_and_course_order():
    args = (np.ones(100)*0.5, np.ones(100)*0.5, np.ones(100), ['A','B']*50)
    first, reasons = allocate(*args, route='course', seed=7)
    second, again = allocate(*args, route='course', seed=7)
    np.testing.assert_array_equal(first, second)
    np.testing.assert_array_equal(reasons, again)


def test_invalid_values_are_rejected():
    with pytest.raises(ValueError):
        allocate([np.nan], [0.2], [1], ['A'])
    with pytest.raises(ValueError):
        allocate([0.2], [0.2], [1], ['A'], Policy(review_minutes=0))
def test_default_route_uses_selected_model_instead_of_old_reference(monkeypatch):
    from talentroute import evaluation
    monkeypatch.setattr(evaluation, 'selected_model', lambda: 'logistic')
    frame = pd.DataFrame({'logistic': [.9, .1], 'hgb_15_10': [.1, .9],
                          'rarity': [0, 0], 'inactive_days': [0, 0], 'code_module': ['A', 'A']})
    policy = Policy(minutes_per_100=1500, alert_learner_cap=0)
    actions, _ = evaluation.frame_actions(frame, policy=policy)
    np.testing.assert_array_equal(actions, [2, 0])

