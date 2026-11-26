"""Guard the supplementary diagnostic against identity and period leakage."""

import pandas as pd
import pytest
from talentroute.nested_audit import training_cases, outer_partitions


def test_outer_folds_keep_repeat_learners_together_and_exclude_later_periods():
    records = [
        dict(
            id_student=i,
            code_presentation="2013B",
            target=["Success", "Fail", "Withdrawn"][i % 3],
        )
        for i in range(30)
        for _ in range(2)
    ]
    records += [
        dict(id_student=999, code_presentation=period, target="Fail")
        for period in ["2014B", "2014J"]
    ]
    mixed = pd.DataFrame(records)
    train = training_cases(mixed)
    assert 999 not in set(train.id_student)
    assessed = []
    for fit, check in outer_partitions(train):
        assert not set(train.iloc[fit].id_student) & set(train.iloc[check].id_student)
        assessed.extend(check)
    assert sorted(assessed) == list(range(len(train)))
    with pytest.raises(ValueError, match="2013B only"):
        list(outer_partitions(mixed))


def test_outer_outcomes_and_future_fields_cannot_change_selection_or_actions():
    """Exercise real fitting: held-out labels never reach the two fitted families."""
    import numpy as np
    from talentroute.data import ROOT
    from talentroute.nested_audit import fit_outer_routes

    frame = training_cases(pd.read_csv(ROOT / 'data/processed/development.csv'))
    fit_idx, check_idx = next(outer_partitions(frame))
    fit = frame.iloc[fit_idx].groupby('target', group_keys=False).head(50)
    check = frame.iloc[check_idx].head(120).copy()
    spec = {'folds': 3, 'seed': 7101, 'candidates': ['logistic']}
    first = fit_outer_routes(fit, check, spec)
    changed = check.copy()
    changed['target'] = 'Success'
    changed['final_result'] = 'Pass'
    changed['score_mean'] = 999
    changed['date_unregistration'] = -999
    second = fit_outer_routes(fit, changed, spec)
    assert first[0] == second[0]
    pd.testing.assert_frame_equal(first[1], second[1])
    np.testing.assert_array_equal(first[2], second[2])
    for route in first[4]:
        np.testing.assert_array_equal(first[4][route], second[4][route])
    counts = [(int((a == 2).sum()), int((a == 1).sum())) for a in first[4].values()]
    assert len(set(counts)) == 1
