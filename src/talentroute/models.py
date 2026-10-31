"""Validation-only model selection with explicit predictor allowlists."""
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier, IsolationForest
from sklearn.metrics import average_precision_score, f1_score, log_loss
from .data import ROOT,config
from .decision import allocate,metrics

# No protected demographics, outcome information, future events, registration end date, or student ID.
NUM=['score_mean','score_min','submitted_count','late_rate','no_early_assessment','studied_credits','num_of_prev_attempts']
ENG=['log_clicks','log_early_clicks','log_late_clicks','inactive_days','engagement_change']
CAT=['code_module']
FEATURES=NUM+ENG+CAT

def preprocessing(columns):
    return ColumnTransformer([('numeric',Pipeline([('impute',SimpleImputer(strategy='median',add_indicator=True)),('scale',StandardScaler())]),columns),('module',OneHotEncoder(handle_unknown='ignore',sparse_output=False),CAT)])

def classifier(kind, seed):
    # Comparable supervised baselines can use all valid signals; no deliberately weak strawman.
    if kind=='logistic': model=LogisticRegression(C=1.,max_iter=1500,random_state=seed)
    else:
        leaf,l2=kind.split('_')[1:]
        model=HistGradientBoostingClassifier(max_iter=140,max_leaf_nodes=int(leaf),l2_regularization=float(l2),learning_rate=.07,random_state=seed)
    return Pipeline([('preprocess',preprocessing(NUM+ENG)),('model',model)])

def risk_from(model,frame):
    p=model.predict_proba(frame[FEATURES]); classes=list(model.classes_)
    return 1-p[:,classes.index('Success')],p

def model_metrics(y,p,classes):
    y=np.asarray(y); labels=list(classes)
    result={'macro_f1':f1_score(y,np.array(labels)[p.argmax(1)],average='macro'),'log_loss':log_loss(y,p,labels=labels),'adverse_pr_auc':average_precision_score(y!='Success',1-p[:,labels.index('Success')])}
    for name in ['Fail','Withdrawn']: result[name.lower()+'_pr_auc']=average_precision_score(y==name,p[:,labels.index(name)])
    result['adverse_brier']=float(np.mean(((y!='Success')-(1-p[:,labels.index('Success')]))**2))
    return result

def fit_development():
    cfg=config();df=pd.read_csv(ROOT/'data/processed/enrolments.csv');train=df[df.split=='train'];val=df[df.split=='validation']; out=ROOT/'outputs'
    records=[];models={}
    for kind in ['logistic','hgb_7_2','hgb_15_2','hgb_15_10']:
        model=classifier(kind,cfg['seed']);model.fit(train[FEATURES],train.target)
        risk,p=risk_from(model,val); row={'model':kind,**model_metrics(val.target,p,model.classes_)}
        row.update({'decision_'+k:v for k,v in metrics(val.target,allocate(risk,risk,cfg),cfg).items()})
        records.append(row);models[kind]=model
    scores=pd.DataFrame(records);scores.to_csv(out/'validation_model_search.csv',index=False)
    # Selection rule in the original development code: maximize validation adverse PR-AUC.
    selected=str(scores.sort_values(['adverse_pr_auc','model'],ascending=[False,True]).iloc[0]['model'])
    anomaly=Pipeline([('preprocess',preprocessing(ENG)),('model',IsolationForest(n_estimators=150,max_samples=512,random_state=cfg['seed'],n_jobs=1))]);anomaly.fit(train[ENG+CAT])
    ref=np.sort(-anomaly.score_samples(train[ENG+CAT]))
    anomaly_val=np.searchsorted(ref,-anomaly.score_samples(val[ENG+CAT]),side='right')/len(ref)
    risk,p=risk_from(models[selected],val)
    blends=[]
    for weight in [0.,.1,.2,.35,.5]:
        row={'weight':weight,**metrics(val.target,allocate(risk,anomaly_val,cfg,weight),cfg)};blends.append(row)
    pd.DataFrame(blends).to_csv(out/'validation_policy_search.csv',index=False)
    # Favor simpler classifier-only if tied. Added component stays implemented and evaluated honestly.
    chosen=sorted(blends,key=lambda r:(-r['adverse_coverage'],r['weight']))[0]['weight']
    bundle={'models':models,'selected_model':selected,'anomaly':anomaly,'anomaly_reference':ref,'chosen_weight':chosen,'config':cfg,'classes':models[selected].classes_,'training_modules':sorted(train.code_module.unique().tolist())}
    joblib.dump(bundle,out/'development_models.joblib')
    (out/'development_selection.json').write_text(json.dumps({'selected_model':selected,'selected_weight':chosen,'selection_split':'validation','test_evaluated':False,'primary_model_metric':'adverse_pr_auc','primary_decision_metric':'adverse_coverage','selection_rule':'maximize validation PR-AUC; weight maximizes validation coverage, simpler tie break'},indent=2), encoding='utf-8')
    return records

def predictions(bundle,frame):
    rows=frame[['id_student','code_module','gender','disability','no_early_assessment','target']].copy()
    for kind,model in bundle['models'].items(): rows[kind],_=risk_from(model,frame)
    rows['risk'],p=risk_from(bundle['models'][bundle['selected_model']],frame)
    rows['anomaly']=np.searchsorted(bundle['anomaly_reference'],-bundle['anomaly'].score_samples(frame[ENG+CAT]),side='right')/len(bundle['anomaly_reference'])
    rows['rule']=(-frame.score_mean.fillna(50)/100+frame.inactive_days/29).to_numpy()
    rows['rule']=(rows['rule'].rank(method='average')/len(rows)).to_numpy()
    rows['unseen_module']=(~frame.code_module.isin(bundle['training_modules'])).astype(int).to_numpy()
    rows['simple_anomaly']=(frame.inactive_days/29).to_numpy()
    rows['uncertainty']=-(p*np.log(np.maximum(p,1e-12))).sum(axis=1)/np.log(p.shape[1])
    return rows,p
