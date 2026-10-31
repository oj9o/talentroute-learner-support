"""Fixed final candidate, auditable freeze, and held-out evaluation.

Final candidate is deliberately fixed before any test scoring. A negative outcome
must be reported: inclusion of an experimental component is not endorsement.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score
from .data import ROOT,config
from .models import FEATURES,predictions,model_metrics
from .revision import candidate,aligned_probability
from .decision import allocate,metrics
from .evaluation import cluster_interval

LABELS=['Fail','Success','Withdrawn']

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def implementation_hash():
    paths=sorted((ROOT/'src').rglob('*.py'))+[ROOT/'configs/policy.json']
    return hashlib.sha256(''.join(str(p.relative_to(ROOT))+digest(p) for p in paths).encode()).hexdigest()

def fit_final():
    """Train fixed equal-weight forest/boosting ensemble and reuse train-only IF.

    No new validation grid is searched. This tests model-family reconciliation
    and the previously studied 0.2 detector contribution, rather than inventing
    a second operational task unsupported by the dataset.
    """
    out=ROOT/'outputs/final';out.mkdir(exist_ok=True)
    if (out/'test_metrics.csv').exists():
        raise RuntimeError('Final test already scored. Do not retrain or retune this release.')
    df=pd.read_csv(ROOT/'data/processed/enrolments.csv');train=df.loc[df.split=='train'];del df
    old=joblib.load(ROOT/'outputs/development_models.joblib')
    forest=candidate('forest',config()['seed']).fit(train[FEATURES],train.target)
    bundle={'development':old,'forest':forest,'ensemble_forest_weight':.5,'anomaly_weight':.2}
    joblib.dump(bundle,out/'frozen_models.joblib')
    manifest={'frozen_at_utc':datetime.now(timezone.utc).isoformat(),'candidate':'equal forest/HGB probability ensemble + 0.2 engagement IF blend',
        'rationale':'Fixed model-family reconciliation; IF retained as an experimental component, not a claimed improvement.',
        'scope':'New design after extensive validation exploration; final test not used for design.',
        'implementation_sha256':implementation_hash(),'model_sha256':digest(out/'frozen_models.joblib'),
        'processed_sha256':digest(ROOT/'data/processed/enrolments.csv'),
        'policy':config(),'classes':LABELS,'forest_weight':.5,'anomaly_weight':.2,
        'acceptance':{'coverage_difference_lower_bound_gt':0,'max_flag_precision_loss':.02},
        'final_test_scored_at_freeze':False}
    (out/'freeze.json').write_text(json.dumps(manifest,indent=2))
    return manifest

def load_frozen():
    out=ROOT/'outputs/final';manifest=json.loads((out/'freeze.json').read_text())
    for actual,expected in [(implementation_hash(),manifest['implementation_sha256']),
        (digest(out/'frozen_models.joblib'),manifest['model_sha256']),
        (digest(ROOT/'data/processed/enrolments.csv'),manifest['processed_sha256'])]:
        if actual!=expected: raise RuntimeError('Frozen implementation, model or data changed; final evaluation refused.')
    return joblib.load(out/'frozen_models.joblib'),manifest

def scored_frame(bundle,frame):
    pred,p=predictions(bundle['development'],frame)
    old_model=bundle['development']['models'][bundle['development']['selected_model']]
    p=aligned_probability(old_model,frame)
    proposed=(1-bundle['ensemble_forest_weight'])*p+bundle['ensemble_forest_weight']*aligned_probability(bundle['forest'],frame)
    pred['proposed_risk']=1-proposed[:,1]
    return pred,proposed

def final_evaluate():
    """Report fixed held-out test results; never select using these outcomes."""
    bundle,manifest=load_frozen();cfg=manifest['policy'];out=ROOT/'outputs/final'
    if (out/'acceptance.json').exists():
        return pd.read_csv(out/'test_metrics.csv')  # Recorded final result; no reselection.
    df=pd.read_csv(ROOT/'data/processed/enrolments.csv');test=df.loc[df.split=='test'].reset_index(drop=True);del df
    pred,pp=scored_frame(bundle,test)
    policies={'business_rule':allocate(pred.rule,pred.rule,cfg),'classifier_only':allocate(pred.risk,pred.anomaly,cfg),
        'ensemble_without_detector':allocate(pred.proposed_risk,pred.anomaly,cfg),
        'detector_only':allocate(pred.anomaly,pred.anomaly,cfg),
        'proposed_connected':allocate(pred.proposed_risk,pred.anomaly,cfg,bundle['anomaly_weight'])}
    rows=[{'policy':name,**metrics(pred.target,a,cfg)} for name,a in policies.items()]
    pd.DataFrame(rows).to_csv(out/'test_metrics.csv',index=False)
    ml=[]
    for name,model in bundle['development']['models'].items():
        ml.append({'model':name,**model_metrics(pred.target,aligned_probability(model,test),LABELS)})
    ml.append({'model':'proposed_ensemble',**model_metrics(pred.target,pp,LABELS)})
    pd.DataFrame(ml).to_csv(out/'test_ml_metrics.csv',index=False)
    pd.DataFrame([{'detector':name,'proxy_adverse_pr_auc':average_precision_score(pred.target!='Success',score),
        **metrics(pred.target,allocate(score,score,cfg),cfg)} for name,score in [('isolation_forest',pred.anomaly),('inactivity',pred.simple_anomaly)]]).to_csv(out/'test_detector_relevance.csv',index=False)
    intervals=[]
    for base in ['business_rule','classifier_only','ensemble_without_detector']:
        ci=cluster_interval(pred,policies['proposed_connected'],policies[base],2000,cfg['seed'])
        intervals.append({'comparison':'proposed_connected minus '+base,'low':ci[0],'high':ci[1]})
    pd.DataFrame(intervals).to_csv(out/'test_paired_intervals.csv',index=False)
    # Primary metric uncertainty with student clusters, preserving repeated enrolments.
    groups=list(pred.groupby('id_student').indices.values());rng=np.random.default_rng(cfg['seed']);samples=[]
    for _ in range(2000):
        ix=np.concatenate([groups[j] for j in rng.integers(0,len(groups),len(groups))]);bad=pred.target.to_numpy()[ix]!='Success'
        samples.append([average_precision_score(bad,pred.proposed_risk.to_numpy()[ix]),(policies['proposed_connected'][ix]>0)[bad].mean()])
    bounds=np.quantile(samples,[.025,.975],axis=0)
    pd.DataFrame([{'metric':m,'low':bounds[0,j],'high':bounds[1,j]} for j,m in enumerate(['adverse_pr_auc','adverse_coverage'])]).to_csv(out/'test_primary_intervals.csv',index=False)
    # Test segments are descriptive; never used to retrain or pick another release.
    segments=[]
    for field in ['code_module','no_early_assessment','gender','disability']:
        for group,ix in pred.groupby(field).indices.items():
            y=pred.iloc[ix].target
            for name,a in policies.items():
                segments.append({'segment':field,'group':str(group),'policy':name,'interpretation_allowed':len(ix)>=50 and (y!='Success').sum()>=10,**metrics(y,a[ix],cfg)})
    pd.DataFrame(segments).to_csv(out/'test_segments.csv',index=False)
    gate=pd.DataFrame(rows).set_index('policy');proposal=gate.loc['proposed_connected']
    passed=all(r['low']>0 for r in intervals) and all(proposal.flag_precision>=gate.loc[b,'flag_precision']-.02 for b in ['business_rule','classifier_only','ensemble_without_detector'])
    (out/'acceptance.json').write_text(json.dumps({'accepted':bool(passed),'recommendation':'limited human-reviewed pilot only; no causal claim' if passed else 'Do not endorse the added complexity. Retain the simpler reference pending new independent evidence.',
        'note':'Failure is reported without changing the frozen candidate. This is targeting evaluation, not intervention effectiveness.'},indent=2))
    return pd.DataFrame(rows)

def analysis_outputs():
    """Publish actual component ablation and development sensitivity plots."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out=ROOT/'outputs/final';out.mkdir(exist_ok=True)
    ab=pd.read_csv(out/'test_metrics.csv');ab.to_csv(out/'ablation.csv',index=False)
    fig,ax=plt.subplots(figsize=(9,4));ax.barh(ab.policy,ab.adverse_coverage);ax.set(xlabel='Observed adverse-outcome coverage',title='Fixed held-out policies at the same staff-time budget');fig.tight_layout();fig.savefig(out/'ablation.png',dpi=150);plt.close(fig)
    # Validation sensitivity does not become confirmatory test evidence.
    bundle,manifest=load_frozen()
    frame=pd.read_csv(ROOT/'data/processed/enrolments.csv');val=frame.loc[frame.split=='validation'].reset_index(drop=True);del frame
    pred,_=scored_frame(bundle,val);cfg=manifest['policy'];srows=[]
    for key,values in {'staff_minutes_per_100':[150,300,600],'human_minutes':[20,30,45],'alert_minutes':[1,2,5]}.items():
        for value in values:
            scenario={**cfg,key:value}
            for name,risk,weight in [('classifier_only',pred.risk,0),('proposed_connected',pred.proposed_risk,bundle['anomaly_weight'])]:
                srows.append({'assumption':key,'value':value,'policy':name,**metrics(pred.target,allocate(risk,pred.anomaly,scenario,weight),scenario)})
    sens=pd.DataFrame(srows);sens.to_csv(out/'development_sensitivity.csv',index=False)
    fig,axs=plt.subplots(1,3,figsize=(12,3.6))
    for ax,key in zip(axs,['staff_minutes_per_100','human_minutes','alert_minutes']):
        for name,g in sens[(sens.assumption==key)&sens.policy.isin(['classifier_only','proposed_connected'])].groupby('policy'):
            ax.plot(g.value,g.adverse_coverage,marker='o',label=name)
        ax.set(xlabel=key,ylabel='Adverse coverage',title='Exploratory validation');ax.legend(fontsize=7)
    fig.tight_layout();fig.savefig(out/'sensitivity.png',dpi=150);plt.close(fig)
    from sklearn.ensemble import IsolationForest
    from sklearn.pipeline import Pipeline
    from .models import preprocessing,ENG,CAT
    frame=pd.read_csv(ROOT/'data/processed/enrolments.csv');train=frame.loc[frame.split=='train'];del frame
    stability=[]
    for seed in [7101,7102,7103]:
        model=Pipeline([('preprocess',preprocessing(ENG)),('model',IsolationForest(n_estimators=150,max_samples=512,random_state=seed,n_jobs=1))]).fit(train[ENG+CAT])
        ref=np.sort(-model.score_samples(train[ENG+CAT]));score=np.searchsorted(ref,-model.score_samples(val[ENG+CAT]),side='right')/len(ref)
        stability.append({'seed':seed,**metrics(pred.target,allocate(pred.proposed_risk,score,cfg,bundle['anomaly_weight']),cfg)})
    pd.DataFrame(stability).to_csv(out/'development_seed_stability.csv',index=False)
    return ab

def final_app(budget):
    """Offline validation-cohort scenario worklist from the frozen final candidate."""
    bundle,manifest=load_frozen();cfg={**manifest['policy'],'staff_minutes_per_100':float(budget)}
    frame=pd.read_csv(ROOT/'data/processed/enrolments.csv');val=frame.loc[frame.split=='validation'].reset_index(drop=True);del frame
    pred,_=scored_frame(bundle,val);weight=bundle['anomaly_weight']
    actions=allocate(pred.proposed_risk,pred.anomaly,cfg,weight)
    score=(1-weight)*pred.proposed_risk+weight*pred.anomaly
    work=pd.DataFrame({'case_reference':['CASE-'+str(i+1).zfill(5) for i in range(len(val))],
        'risk':pred.proposed_risk,'anomaly_percentile':pred.anomaly,'priority_score':score,
        'action':pd.Series(actions).map({0:'no_action',1:'alert',2:'human_review'})})
    work.loc[actions>0].sort_values('priority_score',ascending=False,kind='stable').to_csv(ROOT/'outputs/final/demo_worklist.csv',index=False)
    result={'scenario':'Validation-cohort illustration using frozen experimental final system; not prevented failures',
        'budget_per_100':float(budget),'human_reviews':int((actions==2).sum()),'alerts':int((actions==1).sum()),
        'no_action':int((actions==0).sum()),'staff_minutes':float((actions==2).sum()*cfg['human_minutes']+(actions==1).sum()*cfg['alert_minutes']),
        'available_minutes':float(len(actions)*budget/100)}
    print(json.dumps(result,indent=2));return result
