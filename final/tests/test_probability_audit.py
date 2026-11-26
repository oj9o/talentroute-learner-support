"""Correction retains outcome classes and separates all three learner groups."""
import numpy as np
import pandas as pd
from talentroute.probability_audit import correct, fit_temperature, partitions


def test_temperature_improves_overconfident_calibration_sample_without_changing_classes():
    probabilities = np.tile([0.98, 0.01, 0.01], (100, 1))
    target = np.array(['Fail'] * 60 + ['Success'] * 20 + ['Withdrawn'] * 20)
    temperature = fit_temperature(probabilities, target, ['Fail', 'Success', 'Withdrawn'])
    corrected = correct(probabilities, temperature)
    assert temperature > 1
    np.testing.assert_allclose(corrected.sum(axis=1), 1)
    np.testing.assert_array_equal(corrected.argmax(axis=1), probabilities.argmax(axis=1))
    assert corrected[:, 0].mean() < probabilities[:, 0].mean()
    np.testing.assert_allclose(correct(probabilities, 1), probabilities)


def test_model_calibration_and_assessment_learners_are_disjoint():
    frame = pd.DataFrame([
        {'id_student': i, 'target': ['Fail', 'Success', 'Withdrawn'][i % 3],
         'code_presentation': '2013B'} for i in range(90) for _ in range(2)
    ])
    assessed = []
    for fit, cal, check in partitions(frame):
        groups = [set(frame.iloc[idx].id_student) for idx in (fit, cal, check)]
        assert not groups[0] & groups[1]
        assert not groups[0] & groups[2]
        assert not groups[1] & groups[2]
        assert sorted(np.concatenate([fit, cal, check])) == list(range(len(frame)))
        assessed.extend(check)
    assert sorted(assessed) == list(range(len(frame)))
