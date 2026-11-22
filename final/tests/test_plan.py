import numpy as np
import pytest
from talentroute.decision import Policy
from talentroute.plan import apply_edits, check_plan, compare_actions


def test_exact_budget_and_one_extra_alert_rejected():
    # 100 cases, 300 minutes, 20-alert cap: 8 reviews + 20 alerts = 280.
    policy = Policy()
    risk = np.full(100, .8)
    actions = np.array([2]*8 + [1]*20 + [0]*72)
    result = check_plan(risk, actions, policy)
    assert result['feasible']
    assert result['used_minutes'] == 280
    assert result['remaining_minutes'] == 20
    assert result['review_cap'] == 8
    assert result['alert_cap'] == 20
    actions[28] = 1
    assert not check_plan(risk, actions, policy)['feasible']
    actions[28] = 2
    assert not check_plan(risk, actions, policy)['feasible']


def test_boundary_gate_and_budget_and_fractional_action():
    p = Policy(minutes_per_100=240, alert_budget_fraction=0, risk_threshold=.5)
    actions = np.array([2.]*8+[0.]*92)
    risk = np.full(100, .5)
    assert check_plan(risk, actions, p)['remaining_minutes'] == 0
    assert check_plan(risk, actions, p)['feasible']
    risk[0] = .499
    assert not check_plan(risk, actions, p)['feasible']
    risk[0] = .5
    actions[0] = 1.5
    assert not check_plan(risk, actions, p)['feasible']
    assert check_plan(risk, np.zeros(100), Policy(minutes_per_100=0))['feasible']


@pytest.mark.parametrize('edits', [[{'index':0,'action':1},{'index':0,'action':2}],
                                  [{'index':-1,'action':2}], [{'index':0,'action':1.5}],
                                  [{'index':True,'action':1}], [{'index':0,'action':True}],
                                  [{'index':100,'action':0}]])
def test_invalid_edits_rejected(edits):
    with pytest.raises(ValueError):
        apply_edits(np.zeros(100, dtype=int), edits)


def test_edits_preserve_unedited_cases_and_comparison_counts():
    original = np.array([2,1,0,0])
    new = apply_edits(original, [{'index':0,'action':0},{'index':2,'action':2}])
    assert original.tolist() == [2,1,0,0]
    assert new.tolist() == [0,1,2,0]
    diff = compare_actions(original,new,['AAA','AAA','BBB','BBB'])
    assert (diff['changed'],diff['entered'],diff['left']) == (2,1,1)
    assert diff['courses'] == [{'module':'AAA','before':2,'after':1},
                               {'module':'BBB','before':0,'after':1}]


def test_allocator_satisfies_independent_audit_across_costs_gates_and_routes():
    from talentroute.decision import allocate
    rng = np.random.default_rng(91)
    risk, rarity, inactivity = rng.random((3, 113))
    modules = np.array(['AAA']*60+['BBB']*53)
    for budget in [0, 3, 150, 300, 600]:
        for gate in [0, .5, 1]:
            for route in ['classifier', 'anomaly', 'inactivity', 'course', 'random']:
                policy = Policy(minutes_per_100=budget, risk_threshold=gate,
                                review_minutes=17.5, alert_minutes=1.3)
                actions, _ = allocate(risk, rarity, inactivity, modules, policy, route)
                assert check_plan(risk, actions, policy)['feasible']
