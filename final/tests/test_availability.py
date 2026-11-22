"""Check that assessment data cannot affect the availability-safe predictor."""
import numpy as np
import pandas as pd
from talentroute.app import artifacts, case_inputs, predict_case, scenario
from talentroute.availability_audit import ASSESSMENT_COLUMNS, SAFE_NUM
from talentroute.models import risk_from


def test_assessment_and_outcome_mutations_do_not_change_safe_predictions():
    frame, bundle = artifacts('identity_disjoint')
    model = bundle['models']['assessment_free']
    assert not ASSESSMENT_COLUMNS.intersection(model.feature_names_in_)
    original = risk_from(model, frame)[0]
    changed = frame.copy()
    for column in ASSESSMENT_COLUMNS:
        changed[column] = np.arange(len(frame))*123.0
    changed['target'] = 'Success'
    changed['final_result'] = 'Pass'
    np.testing.assert_array_equal(original, risk_from(model, changed)[0])


def test_safe_app_mode_ignores_valid_assessment_edits():
    inputs = case_inputs(0)
    first = predict_case({'model': 'assessment_free', 'inputs': inputs})
    inputs.update(submitted_count=1, score_mean=100, score_min=100, late_rate=0)
    second = predict_case({'model': 'assessment_free', 'inputs': inputs})
    assert first['risk'] == second['risk']
    result = scenario({'model': 'assessment_free'})
    assert result['decision_rules']['feasible']
    assert result['metrics']['contact_n'] > 0


def test_selection_rejects_evaluation_rows_before_fitting():
    import pytest
    from talentroute.availability_audit import select_on_training
    frame = pd.DataFrame({'code_presentation': ['2013B', '2014B']})
    with pytest.raises(ValueError, match='2013B training records only'):
        select_on_training(frame, SAFE_NUM, {})
