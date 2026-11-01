import numpy as np
import pandas as pd
import pytest
from talentroute.data import ROOT,config
from talentroute.decision import allocate,metrics
from talentroute.models import FEATURES,ENG

def test_budget_and_determinism():
    rng=np.random.default_rng(7101)
    for n in [0,1,7,100,231]:
        for budget in [0,1,150,300,600]:
            c={**config(),'staff_minutes_per_100':budget};r=rng.random(n);a=rng.random(n)
            x=allocate(r,a,c,.2); y=allocate(r,a,c,.2)
            assert np.array_equal(x,y)
            cost=(x==2).sum()*c['human_minutes']+(x==1).sum()*c['alert_minutes']
            assert cost<=n*budget/100+1e-8
            assert (x==1).sum()<=int(n*c['max_alert_fraction'])

def test_known_outcome_metrics():
    y=['Fail','Withdrawn','Success','Fail'];a=[2,0,1,1];m=metrics(y,a,config())
    assert m['adverse_coverage']==pytest.approx(2/3)
    assert m['fail_coverage']==1
    assert m['withdrawn_coverage']==0
    assert m['staff_minutes']==34

def test_predictor_allowlist():
    assert not set(FEATURES)&{'target','final_result','date_unregistration','id_student','gender','disability','split','code_presentation'}
    assert set(ENG)<=set(FEATURES)

def test_split_integrity():
    p=ROOT/'data/processed/enrolments.csv'
    if not p.exists(): pytest.skip('Run prepare-data before integration test')
    d=pd.read_csv(p)
    for a,b in [('train','validation'),('train','test'),('validation','test')]:
        assert not set(d.loc[d.split==a,'id_student'])&set(d.loc[d.split==b,'id_student'])
        assert d.loc[d.split==a,'code_presentation'].max()<d.loc[d.split==b,'code_presentation'].min()
    assert (d.date_registration<=config()['cutoff_day']).all()
    assert (d.date_unregistration.isna()|(d.date_unregistration>config()['cutoff_day'])).all()
    assert d.target.nunique()==3

def test_small_model_pipeline_repeatability():
    from talentroute.models import classifier,risk_from
    from sklearn.ensemble import IsolationForest
    rng=np.random.default_rng(7101);n=90
    frame=pd.DataFrame({c:rng.normal(size=n) for c in FEATURES if c!='code_module'})
    frame['code_module']=np.tile(['AAA','BBB','CCC'],30)
    labels=np.tile(['Fail','Withdrawn','Success'],30)
    first=classifier('logistic',7101).fit(frame,labels)
    second=classifier('logistic',7101).fit(frame,labels)
    r1,p1=risk_from(first,frame);r2,p2=risk_from(second,frame)
    assert np.array_equal(np.round(p1,12),np.round(p2,12))
    a1=IsolationForest(n_estimators=15,random_state=7101).fit(frame[ENG]).score_samples(frame[ENG])
    a2=IsolationForest(n_estimators=15,random_state=7101).fit(frame[ENG]).score_samples(frame[ENG])
    assert np.array_equal(a1,a2)
    assert np.array_equal(allocate(r1,-a1,config(),.2),allocate(r2,-a2,config(),.2))


def test_semantic_data_validation_rejects_bad_scores_and_counts():
    from talentroute.data import validate_prepared
    path=ROOT/'data/processed/enrolments.csv'
    if not path.exists(): pytest.skip('Prepare data before integration checks')
    df=pd.read_csv(path).head(100).copy();validate_prepared(df,config())
    bad=df.copy();bad.loc[bad.index[0],'score_mean']=101
    with pytest.raises(ValueError,match='score range'):validate_prepared(bad,config())
    bad=df.copy();bad.loc[bad.index[0],'clicks']=-1
    with pytest.raises(ValueError,match='Negative'):validate_prepared(bad,config())
