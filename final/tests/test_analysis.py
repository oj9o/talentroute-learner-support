import numpy as np
import pandas as pd
from talentroute.analyses import Values, assumed_value, break_even
from talentroute.data import split_frames, prior_registration_ids
from talentroute.models import FEATURES, classifier


def test_utility_uses_observed_action_counts_and_declared_units():
    counts = dict(review_fail_n=2, review_withdrawn_n=1, alert_fail_n=4,
                  alert_withdrawn_n=3, review_success_n=2, alert_success_n=3, staff_minutes=100)
    value = assumed_value(counts, Values())
    assert np.isclose(value, 3*3+7-2*.5-3*.05-100*.01)


def test_operational_protocol_keeps_prior_records_while_identity_disjoint_excludes_them():
    frame = pd.DataFrame({'split': ['train', 'train', 'validation'],
                          'identity_disjoint_train': [False, True, False], 'id_student': [7, 8, 7]})
    strict, val = split_frames(frame, 'identity_disjoint')
    operational, val2 = split_frames(frame, 'operational')
    assert set(strict.id_student) == {8}
    assert set(operational.id_student) == {7, 8}
    pd.testing.assert_frame_equal(val, val2)


def test_model_ignores_protected_and_future_fields_and_repeats_deterministically():
    rng = np.random.default_rng(7)
    frame = pd.DataFrame(rng.random((60, len(FEATURES)-1)), columns=FEATURES[:-1])
    frame['code_module'] = ['A', 'B'] * 30
    target = np.array(['Success', 'Fail', 'Withdrawn'] * 20)
    model = classifier('tree', 7).fit(frame, target)
    first = model.predict_proba(frame)
    frame['gender'] = 'changed'
    frame['final_result'] = 'invented'
    frame['id_student'] = np.arange(len(frame))
    np.testing.assert_array_equal(first, model.predict_proba(frame))
    again = classifier('tree', 7).fit(frame[FEATURES], target)
    np.testing.assert_array_equal(first, again.predict_proba(frame[FEATURES]))
    from talentroute.decision import allocate
    risk = 1 - first[:, list(model.classes_).index('Success')]
    repeated_risk = 1 - again.predict_proba(frame[FEATURES])[:, list(again.classes_).index('Success')]
    inputs = (np.zeros(60), np.zeros(60), frame.code_module)
    np.testing.assert_array_equal(allocate(risk, *inputs, seed=7)[0],
                                  allocate(repeated_risk, *inputs, seed=7)[0])


def test_prior_enrolment_requires_registration_known_by_decision():
    rows = pd.DataFrame({'code_presentation': ['2013J'] * 4 + ['2014J'],
                         'id_student': [1, 2, 3, 4, 5],
                         'date_registration': [0, 121, 122, np.nan, -200]})
    assert prior_registration_ids(rows) == {1, 2}


def test_break_even_matches_direct_value_difference():
    from dataclasses import replace
    from talentroute.decision import observed_metrics
    y = ['Fail', 'Success', 'Withdrawn', 'Success']
    reference = observed_metrics(y, [2, 2, 1, 0])
    candidate = observed_metrics(y, [2, 1, 2, 0])
    result = break_even(candidate, reference)
    crossing = result['review_weight_break_even']
    values = replace(Values(), review_weight=crossing)
    assert np.isclose(assumed_value(candidate, values), assumed_value(reference, values))


def test_value_uncertainty_preserves_paired_identity_and_observed_difference():
    from talentroute.analyses import value_difference_interval
    from talentroute.decision import observed_metrics
    frame = pd.DataFrame({'id_student': [1, 1, 2, 3],
                          'target': ['Fail', 'Success', 'Withdrawn', 'Success']})
    a, b = np.array([2, 1, 0, 0]), np.array([1, 0, 2, 0])
    identical = value_difference_interval(frame, a, a, Values())
    assert all(value == 0 for value in identical.values())
    result = value_difference_interval(frame, a, b, Values())
    expected = assumed_value(observed_metrics(frame.target, a)) - assumed_value(observed_metrics(frame.target, b))
    assert np.isclose(result['preference_difference'], expected)


def test_app_explains_missing_pipeline_outputs_instead_of_dropping_request(monkeypatch):
    from types import SimpleNamespace
    from talentroute import app
    def missing():
        raise FileNotFoundError('development_selection.csv')
    monkeypatch.setattr(app, 'selected_model', missing)
    responses = []
    request = SimpleNamespace(path='/configuration',
                              reply=lambda body, status=200: responses.append((status, body)))
    app.Handler.do_GET(request)
    assert responses[0][0] == 503
    assert 'just pipeline' in responses[0][1]['error']


def test_assessment_labels_cannot_change_the_selection_and_identity_overlap_is_rejected():
    import pytest
    from talentroute.evaluation import selection_assessment
    from talentroute.models import CANDIDATES
    rng = np.random.default_rng(19)
    frame = pd.DataFrame({'id_student': np.repeat(np.arange(100), 2),
                          'target': ['Success', 'Fail', 'Withdrawn', 'Success'] * 50,
                          'code_module': ['A', 'B'] * 100,
                          'rarity': rng.random(200), 'inactive_days': rng.integers(0, 29, 200),
                          'heuristic': rng.random(200)})
    for name in CANDIDATES:
        frame[name] = rng.random(200)
    selection, assessment = frame.iloc[:100].copy(), frame.iloc[100:].copy()
    before = selection_assessment(selection, assessment)
    assessment['target'] = np.roll(assessment.target.to_numpy(), 1)
    after = selection_assessment(selection, assessment)
    assert before['selected_model'] == after['selected_model']
    assert before['selected_contact_n'] == after['selected_contact_n']
    assert before['selected_staff_minutes'] <= before['assessment_budget_minutes']
    assessment.iloc[0, assessment.columns.get_loc('id_student')] = selection.id_student.iloc[0]
    with pytest.raises(ValueError, match='different students'):
        selection_assessment(selection, assessment)


def test_frozen_workload_shortfall_and_retention_are_not_hidden_by_reallocation():
    from talentroute.analyses import workload_stress
    from talentroute.decision import Policy, retain_within_budget
    # Budget 100 minutes. The fixed plan needs 92; longer reviews need 137.
    frame = pd.DataFrame({'logistic': [.9, .8, .7, .6, .5, .4, .3, .2, .1, 0],
                          'rarity': np.zeros(10), 'inactive_days': np.zeros(10),
                          'code_module': ['A'] * 10,
                          'target': ['Fail', 'Success'] * 5})
    original = np.array([2, 2, 2, 1, 0, 0, 0, 0, 0, 0])
    policy = Policy(minutes_per_100=1000)
    rows = workload_stress(frame, original, 'logistic', policy)
    base, stressed = rows[0], rows[2]
    assert base['frozen_feasible'] and base['shortfall_minutes'] == 0
    assert not stressed['frozen_feasible']
    assert stressed['frozen_required_minutes'] == 137
    assert stressed['shortfall_minutes'] == 37
    assert stressed['deferred_n'] == 1
    assert all(row['retained_minutes'] <= 100 and row['replanned_minutes'] <= 100 for row in rows)
    retained = retain_within_budget(original, frame.logistic, Policy(minutes_per_100=1000, review_minutes=45))
    np.testing.assert_array_equal(retained, [2, 2, 0, 1, 0, 0, 0, 0, 0, 0])
    np.testing.assert_array_equal(original, [2, 2, 2, 1, 0, 0, 0, 0, 0, 0])
    np.testing.assert_array_equal(retain_within_budget(original, frame.logistic,
                                  Policy(minutes_per_100=0)), np.zeros(10))
