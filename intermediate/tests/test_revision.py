"""Check specialist probability alignment and new candidate contracts on synthetic data."""
import numpy as np
import pandas as pd
from talentroute.revision import aligned_probability, candidate
from talentroute.models import FEATURES


def test_specialist_probability_columns_are_aligned():
    class Fake:
        classes_ = np.array(['Withdrawn', 'Fail', 'Success'])
        def predict_proba(self, frame):
            return np.tile([.2, .3, .5], (len(frame), 1))
    frame = pd.DataFrame({key: [0] for key in FEATURES})
    np.testing.assert_allclose(aligned_probability(Fake(), frame), [[.3,.5,.2]])


def test_tree_candidates_produce_valid_reproducible_probabilities():
    rng = np.random.default_rng(5)
    frame = pd.DataFrame({key: rng.normal(size=90) for key in FEATURES if key!='code_module'})
    frame['code_module'] = 'AAA'
    labels = np.tile(['Fail','Success','Withdrawn'], 30)
    for name in ['tree','forest']:
        first = candidate(name, 7).fit(frame, labels)
        second = candidate(name, 7).fit(frame, labels)
        p = aligned_probability(first, frame)
        np.testing.assert_allclose(p.sum(axis=1), 1)
        np.testing.assert_allclose(p, aligned_probability(second, frame))


def test_seeded_ties_keep_score_order_without_file_order_bias():
    from talentroute.revision_checks import seeded_order
    scores = np.array([2.,1.,1.,1.,0.])
    order = seeded_order(scores, 4)
    assert order[0] == 0 and order[-1] == 4
    np.testing.assert_array_equal(order, seeded_order(scores, 4))
    assert any(not np.array_equal(order, seeded_order(scores, seed)) for seed in range(10))


def test_break_even_grid_budget_and_reference():
    from pathlib import Path
    from talentroute.data import ROOT, config
    p = ROOT/'outputs/revision/action_break_even.csv'
    if not p.exists():
        import pytest
        pytest.skip('Run revision before evidence checks')
    d = pd.read_csv(p); cfg = config()
    n = int(pd.read_csv(ROOT/'outputs/revision/model_comparison.csv').iloc[0]['n'])
    budget = n*cfg['staff_minutes_per_100']/100
    assert (d.staff_minutes <= budget+1e-8).all()
    assert (d.unused_minutes < cfg['human_minutes']).all()
    assert (d.alert_n <= np.floor(n*d.alert_cap_fraction)).all()
    assert d.reference_operating_mix.any()
    np.testing.assert_allclose(d.observed_weighted_targeting_units_scenario,
        d.human_effectiveness_multiplier_assumed*d.human_adverse_n+d.alert_adverse_n)


def test_paired_bootstrap_identical_predictions_have_zero_difference():
    from talentroute.model_intervals import paired_intervals
    y = np.tile(['Fail','Success','Withdrawn'], 10)
    p = np.tile([.3,.4,.3], (len(y),1))
    result = paired_intervals(y, np.repeat(np.arange(15),2), p, p, repeats=20, seed=8)
    assert len(result) == 3
    for row in result:
        assert row['ci95_lower'] == row['ci95_upper'] == 0
        assert row['contains_zero']


def test_original_operating_mix_uses_same_effectiveness_on_both_sides():
    from talentroute.data import ROOT
    p=ROOT/'outputs/revision/action_break_even.csv'
    if not p.exists():
        import pytest
        pytest.skip('Run revision before checking evidence')
    d=pd.read_csv(p);r=d[d.reference_operating_mix]
    assert len(r)>0
    assert np.isclose(r.alert_cap_fraction,.2).any()
    np.testing.assert_allclose(r.observed_weighted_targeting_units_scenario,
        r.reference_weighted_targeting_units_scenario)
    assert (r.break_even_status=='identical_all_multipliers').all()


def test_full_classifier_share_recovers_same_quota_reference():
    from talentroute.data import ROOT
    p=ROOT/'outputs/revision/layer_quota_sensitivity.csv'
    if not p.exists():
        import pytest
        pytest.skip('Run revision before checking evidence')
    d=pd.read_csv(p);r=d[d.classifier_first_share==1]
    reference=pd.read_csv(ROOT/'outputs/revision/model_comparison.csv')
    expected=reference[reference.model=='hgb_15_10'].iloc[0]
    assert (r.flagged_n==expected.flagged_n).all()
    np.testing.assert_allclose(r.adverse_coverage,expected.adverse_coverage)
