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


def test_profiles_retain_policy_identity_and_missing_score_denominators():
    from talentroute.revision import warning_profiles
    n=150
    frame=pd.DataFrame({'target':np.repeat(['Fail','Success','Withdrawn'],50),
        'log_clicks':1.,'inactive_days':3.,'engagement_change':0.,
        'score_mean':np.tile(np.r_[np.full(10,70.),np.full(40,np.nan)],3),
        'no_early_assessment':0})
    profiles=warning_profiles(frame,{'reference':np.ones(n),'alternative':np.zeros(n)})
    score=profiles[profiles.feature=='score_mean']
    assert set(score.policy)=={'reference','alternative'}
    assert (score.observed_n==10).all() and (score.n==50).all()
    np.testing.assert_allclose(score.missing_fraction,.8)
    assert score[score.policy=='reference'].flagged.all()
    assert not score[score.policy=='alternative'].flagged.any()


def test_segment_results_use_shared_actions_and_guard_rare_classes():
    from talentroute.revision import segment_results
    frame=pd.DataFrame({'target':['Fail']*40+['Success']*31+['Withdrawn']*4,
        'code_module':'AAA','no_early_assessment':0})
    probability=np.tile([.4,.5,.1],(len(frame),1));actions=np.zeros(len(frame),dtype=int)
    actions[:3]=2
    from talentroute.data import config
    rows=segment_results('fixed',frame,probability,actions,config())
    module=next(row for row in rows if row['segment']=='code_module')
    assert module['flagged_n']==3 and module['human_n']==3
    assert module['withdrawn_positive_n']==4 and not module['withdrawn_stable']
    assert np.isnan(module['withdrawn_pr_auc'])
    assert module['adverse_coverage']==3/44


def test_hybrid_has_course_metrics_and_unseen_course_uses_global_fallback():
    from talentroute.data import ROOT
    import pytest
    path=ROOT/'outputs/revision/model_segments.csv'
    if not path.exists():pytest.skip('Run revision before checking course evidence')
    frame=pd.read_csv(path);subset=frame[frame.segment=='code_module']
    hybrid=subset[subset.model=='module_logistic_hybrid'].set_index('group')
    assert not hybrid.empty,'Missing per-course hybrid evidence'
    global_model=subset[subset.model=='logistic'].set_index('group')
    assert set(hybrid.index)==set(global_model.index)
    eligibility=pd.read_csv(ROOT/'outputs/revision/specialist_eligibility.csv').set_index('module')
    for module,row in eligibility.iterrows():
        if row.specialist_used:assert row.eligible and row.training_n>=300
        elif module in hybrid.index:
            assert hybrid.loc[module,'adverse_pr_auc']==pytest.approx(global_model.loc[module,'adverse_pr_auc'])


def test_population_purge_audit_contains_development_only():
    from talentroute.data import ROOT
    import pytest
    path=ROOT/'outputs/purge_population_audit.csv'
    if not path.exists():pytest.skip('Prepare data before checking population audit')
    frame=pd.read_csv(path)
    assert set(frame.split)<= {'train','validation'}
    assert set(frame.retention)=={'retained','purged'}
    assert set(frame.target)=={'Success','Fail','Withdrawn'}
    audit=__import__('json').loads((ROOT/'outputs/data_audit.json').read_text())
    assert frame.loc[frame.retention=='purged','n'].sum()==audit['purged_earlier_repeat_enrolments']
    assert frame.loc[frame.retention=='retained','n'].sum()==audit['split_counts']['train']+audit['split_counts']['validation']
