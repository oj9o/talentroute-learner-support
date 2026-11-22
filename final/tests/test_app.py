import json
import numpy as np
import pandas as pd
import pytest
from talentroute.app import artifacts, case_inputs, clean_json, predict_case, scenario
from talentroute.data import ROOT

pytestmark = pytest.mark.skipif(not (ROOT / 'outputs/models_identity_disjoint.joblib').exists(),
                                reason='Run model stage before integration tests')


def test_observed_case_predictions_match_saved_model_scores_even_with_missing_assessments():
    frame, _ = artifacts('identity_disjoint')
    examples = [0, int(frame.loc[frame.submitted_count.eq(0)].index[0]),
                int(frame.loc[frame.submitted_count.gt(0)].index[0]),
                int(frame.loc[frame.submitted_count.gt(0) & frame.score_mean.isna()].index[0])]
    for index in examples:
        inputs = case_inputs(index, 'identity_disjoint')
        result = predict_case({'protocol': 'identity_disjoint', 'model': 'logistic', 'inputs': inputs})
        assert np.isclose(result['risk'], frame.iloc[index].logistic)
        assert np.isclose(sum(result['probabilities'].values()), 1)


def test_threshold_and_zero_budget_reallocate_without_changing_fitted_predictions():
    frame, _ = artifacts('identity_disjoint')
    before = frame.logistic.copy()
    result = scenario({'model': 'logistic', 'policy': {'minutes_per_100': 0}})
    assert result['metrics']['contact_n'] == 0
    assert result['metrics']['staff_minutes'] == 0
    gated = scenario({'model': 'logistic', 'policy': {'risk_threshold': .9}})
    assert all(row['model_risk'] >= .9 for row in gated['queue'])
    pd.testing.assert_series_equal(frame.logistic, before)
    json.dumps(clean_json(gated), allow_nan=False)
    assert not any(key in json.dumps(gated['queue']) for key in ['id_student', 'gender', 'final_result'])


def test_impossible_activity_inputs_rejected():
    inputs = case_inputs(0)
    inputs.update(early_clicks=0, late_clicks=0, inactive_days=2)
    with pytest.raises(ValueError, match='No day'):
        predict_case({'inputs': inputs})


def test_extrapolation_warns_and_anomaly_reference_is_sorted():
    _, bundle = artifacts('identity_disjoint')
    assert len(bundle['reference']) > 0
    assert np.all(np.diff(bundle['reference']) >= 0)
    inputs = case_inputs(0)
    inputs.update(submitted_count=100, score_mean=50, score_min=40, late_rate=.5)
    result = predict_case({'model': 'logistic', 'inputs': inputs})
    assert any('submitted_count: outside' in message for message in result['warnings'])


def test_activity_boundary_matches_cohort_day_cutoff():
    inputs = case_inputs(0)
    for early, late, inactive in [(1, 0, 14), (0, 1, 13), (0, 0, 29)]:
        inputs.update(early_clicks=early, late_clicks=late, inactive_days=inactive)
        assert 0 <= predict_case({'inputs': inputs})['risk'] <= 1


def test_independent_plan_audit_and_comparison_do_not_change_predictions():
    from talentroute.app import check_edited_plan
    frame, _ = artifacts('operational')
    scores = frame.logistic.copy()
    baseline = {'protocol': 'operational', 'model': 'logistic'}
    result = scenario(baseline)
    assert result['decision_rules']['feasible']
    assert len(result['editable_cases']) <= 9
    checked = check_edited_plan({**baseline, 'edits': []})
    assert checked['feasible'] and checked['changes']['changed'] == 0
    overloaded = check_edited_plan({**baseline, 'edits': [
        {'index': r['index'], 'action': 2} for r in result['editable_cases']]})
    assert not overloaded['feasible']
    changed = scenario({**baseline, 'previous': baseline,
                        'policy': {'minutes_per_100': 600}})
    assert changed['comparison']['changed'] > 0
    assert changed['comparison']['entered'] > 0
    assert sum(c['after']-c['before'] for c in changed['comparison']['courses']) == (
        changed['comparison']['entered']-changed['comparison']['left'])
    with pytest.raises(ValueError, match='population protocol'):
        scenario({**baseline, 'previous': {'protocol':'identity_disjoint'}})
    pd.testing.assert_series_equal(frame.logistic, scores)


def test_checker_never_reads_outcomes(monkeypatch):
    import talentroute.app as app
    frame, bundle = artifacts('operational')
    # Deliberately remove evaluation outcomes from the checker input.
    monkeypatch.setattr(app, 'artifacts', lambda protocol: (frame.drop(columns='target'), bundle))
    assert app.check_edited_plan({'model':'logistic'})['feasible']
