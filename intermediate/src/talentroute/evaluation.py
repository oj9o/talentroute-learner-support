"""Development evaluation only; this pipeline does not score the separate final cohort."""
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score
from .data import ROOT,config
from .decision import allocate,metrics
from .models import predictions,model_metrics


def policy_actions(pred,cfg,weight):
    return {'business_rule':allocate(pred.rule,pred.rule,cfg),'logistic':allocate(pred.logistic,pred.anomaly,cfg),'classifier_only':allocate(pred.risk,pred.anomaly,cfg),'anomaly_rule':allocate(pred.simple_anomaly,pred.simple_anomaly,cfg),'anomaly_only':allocate(pred.anomaly,pred.anomaly,cfg),'coupled_selected':allocate(pred.risk,pred.anomaly,cfg,weight),'coupled_fixed_020':allocate(pred.risk,pred.anomaly,cfg,.2)}

def cluster_interval(pred,a,b,repeats,seed):
    """Paired student-cluster bootstrap of coverage difference for fixed held-out actions."""
    bad=(pred.target!='Success').to_numpy(); ids=pred.id_student.to_numpy();groups=np.unique(ids);rng=np.random.default_rng(seed)
    # Aggregate cluster numerators/denominators, preserving repeated enrolments.
    temp=pd.DataFrame({'id':ids,'delta':bad*((a>0).astype(int)-(b>0).astype(int)),'bad':bad.astype(int)}).groupby('id').sum().reindex(groups)
    vals=[]
    for _ in range(repeats):
        sample=temp.iloc[rng.integers(0,len(groups),len(groups))];den=sample.bad.sum()
        if den: vals.append(sample.delta.sum()/den)
    return np.quantile(vals,[.025,.975]).tolist()

def evaluate_development():
    cfg=config();out=ROOT/'outputs';bundle=joblib.load(out/'development_models.joblib');df=pd.read_csv(ROOT/'data/processed/enrolments.csv');val=df[df.split=='validation'].reset_index(drop=True)
    pred,p=predictions(bundle,val);acts=policy_actions(pred,cfg,bundle['chosen_weight'])
    pd.DataFrame([{'policy':name,**metrics(pred.target,a,cfg)} for name,a in acts.items()]).to_csv(out/'validation_decision_metrics.csv',index=False)
    pd.DataFrame([{'model':bundle['selected_model'],**model_metrics(pred.target,p,bundle['classes'])}]).to_csv(out/'validation_selected_ml_metrics.csv',index=False)
    # Labels indicate adverse-outcome relevance; they are NOT verified anomaly ground truth.
    anomaly_metrics={'proxy_adverse_pr_auc':average_precision_score(pred.target!='Success',pred.anomaly),**metrics(pred.target,acts['anomaly_only'],cfg)}
    pd.DataFrame([{'detector':'isolation_forest',**anomaly_metrics},{'detector':'inactivity_rule','proxy_adverse_pr_auc':average_precision_score(pred.target!='Success',pred.simple_anomaly),**metrics(pred.target,acts['anomaly_rule'],cfg)}]).to_csv(out/'validation_anomaly_proxy_metrics.csv',index=False)
    interval=cluster_interval(pred,acts['coupled_selected'],acts['classifier_only'],cfg['bootstrap_repeats'],cfg['seed'])
    (out/'validation_paired_interval.json').write_text(json.dumps({'metric':'adverse_coverage_difference','comparison':'coupled_selected minus classifier_only','ci95':interval,'caveat':'validation-selected policy; exploratory uncertainty, not independent confirmatory evidence'},indent=2), encoding='utf-8')
    from sklearn.metrics import average_precision_score as ap
    rng=np.random.default_rng(cfg['seed']);groups=list(pred.groupby('id_student').indices.values());samples=[]
    for _ in range(cfg['bootstrap_repeats']):
        idx=np.concatenate([groups[j] for j in rng.integers(0,len(groups),len(groups))]);truth=(pred.target.to_numpy()[idx]!='Success')
        samples.append([ap(truth,pred.risk.to_numpy()[idx]),(acts['coupled_selected'][idx]>0)[truth].mean()])
    bounds=np.quantile(samples,[.025,.975],axis=0)
    pd.DataFrame([{'metric':name,'ci95_low':bounds[0,j],'ci95_high':bounds[1,j],'status':'exploratory validation; selection optimism not removed'} for j,name in enumerate(['adverse_pr_auc','adverse_coverage'])]).to_csv(out/'validation_primary_intervals.csv',index=False)
    # Private intermediate output only; demo uses aggregate counts rather than real student identifiers.
    for name,a in acts.items(): pred['action_'+name]=a
    pred.to_csv(out/'validation_predictions.csv',index=False)
    overlap=[]
    c=acts['classifier_only']>0; a=acts['anomaly_only']>0
    for outcome in ['Success','Fail','Withdrawn']:
        mask=(pred.target==outcome).to_numpy()
        overlap.append({'outcome':outcome,'n':int(mask.sum()),'both_flag':int((mask&c&a).sum()),'classifier_only_flag':int((mask&c&~a).sum()),'anomaly_only_flag':int((mask&~c&a).sum()),'escape_both':int((mask&~c&~a).sum()),'interpretation':'diagnostic union of independently quota-limited layers; NOT a feasible union policy under the original budget'})
    pd.DataFrame(overlap).to_csv(out/'validation_layer_overlap.csv',index=False)
    sensitivity=[]
    for key,values in {'staff_minutes_per_100':[150,300,600],'human_minutes':[20,30,45],'alert_minutes':[1,2,5],'anomaly_weight':[0,.1,.2,.35,.5]}.items():
        for value in values:
            scenario={**cfg,key:value};weight=value if key=='anomaly_weight' else bundle['chosen_weight']
            for name,a in policy_actions(pred,scenario,weight).items(): sensitivity.append({'assumption':key,'value':value,'policy':name,**metrics(pred.target,a,scenario)})
    pd.DataFrame(sensitivity).to_csv(out/'validation_sensitivity.csv',index=False)
    segments=[]
    for column in ['code_module','gender','disability','no_early_assessment','unseen_module']:
        for group,part in pred.groupby(column):
            idx=part.index.to_numpy()
            for name in ['classifier_only','coupled_selected','coupled_fixed_020']:
                segments.append({'segment':column,'group':str(group),'adverse_n':int((part.target!='Success').sum()),'interpretation_allowed':bool(len(part)>=50 and (part.target!='Success').sum()>=10),'policy':name,**metrics(part.target,acts[name][idx],cfg)})
    pd.DataFrame(segments).to_csv(out/'validation_challenge_segments.csv',index=False)
    uncertain=allocate(pred.risk,pred.anomaly,cfg,bundle['chosen_weight'],pred.uncertainty)
    pd.DataFrame([{'policy':'coupled_selected',**metrics(pred.target,acts['coupled_selected'],cfg)},{'policy':'uncertainty_priority_exploratory',**metrics(pred.target,uncertain,cfg)}]).to_csv(out/'validation_uncertainty_analysis.csv',index=False)
    # Minimum-n guard is explicit in reporting, never suppressed silently in source data.
    return {'selected_model':bundle['selected_model'],'chosen_weight':bundle['chosen_weight'],'ci':interval}
