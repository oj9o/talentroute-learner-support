"""Post-freeze exploratory diagnostics on development data only.

No model selection, label correction, final-test evaluation, or frozen-source edits.
"""
import hashlib,json
from datetime import datetime,timezone
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import train_test_split,GroupShuffleSplit
from sklearn.metrics import average_precision_score,roc_auc_score
from talentroute.data import ROOT,config
from talentroute.models import FEATURES,classifier,risk_from

DEST=ROOT/'outputs/investigations'

def development_data(path):
    # Discard test rows before computing diagnostic statistics or features.
    frame=pd.read_csv(path)
    return frame.loc[frame.split.isin(['train','validation'])].copy()

def run():
    DEST.mkdir(parents=True,exist_ok=True)
    cfg=config();seed=cfg['seed'];dev=development_data(ROOT/'data/processed/enrolments.csv')
    tr=dev[dev.split=='train'];va=dev[dev.split=='validation'];rows=[]
    protocol={'created_utc':datetime.now(timezone.utc).isoformat(),'scope':'Exploratory development diagnostics added after the recorded final evaluation; not an independent confirmation or pre-registered study.',
      'test_used_by_this_analysis':False,'splits':['train','validation'],'learning_fractions':[.2,.5,1.], 'seeds':[seed,seed+1,seed+2],
      'models':['logistic','hgb_15_10'],'hypotheses':[
      {'question':'Would more training data help?','expectation':'A shrinking training-validation gap suggests sampling limitations; a flat validation curve offers limited evidence for more data. Temporal shift remains a rival.'},
      {'question':'Is a single feature suspiciously predictive?','expectation':'Very high single-feature performance motivates a timestamp/provenance audit; it does not prove leakage.'},
      {'question':'Can features distinguish development periods?','expectation':'Out-of-student classification above chance suggests detectable covariate differences; it does not prove concept drift or explain outcome error.'}]}
    (DEST/'protocol.json').write_text(json.dumps(protocol,indent=2))
    for kind in protocol['models']:
      for repeat in protocol['seeds']:
       for fraction in protocol['learning_fractions']:
        sub=tr if fraction==1 else train_test_split(tr,train_size=fraction,stratify=tr.target,random_state=repeat)[0]
        model=classifier(kind,repeat)
        # Fix iteration count across the automatic early-stopping size threshold.
        if kind!='logistic': model.set_params(model__early_stopping=False)
        model.fit(sub[FEATURES],sub.target)
        for split,part in [('training',sub),('validation',va)]:
         risk,_=risk_from(model,part)
         rows.append(dict(model=kind,seed=repeat,fraction=fraction,n_train=len(sub),split=split,adverse_ap=average_precision_score(part.target!='Success',risk)))
    pd.DataFrame(rows).to_csv(DEST/'learning_curve.csv',index=False)
    rows=[]
    for feature in FEATURES:
      transform=ColumnTransformer([('feature',OneHotEncoder(handle_unknown='ignore',sparse_output=False) if feature=='code_module' else SimpleImputer(strategy='median',add_indicator=True),[feature])])
      model=make_pipeline(transform,HistGradientBoostingClassifier(max_iter=100,max_leaf_nodes=7,l2_regularization=10,random_state=seed))
      model.fit(tr[[feature]],tr.target!='Success');risk=model.predict_proba(va[[feature]])[:,1]
      rows.append(dict(feature=feature,adverse_ap=average_precision_score(va.target!='Success',risk),adverse_roc_auc=roc_auc_score(va.target!='Success',risk)))
    pd.DataFrame(rows).sort_values('adverse_ap',ascending=False).to_csv(DEST/'single_feature.csv',index=False)
    # Domain label is an observed split indicator, not an invented learner outcome.
    domain=(dev.split=='validation').astype(int);rows=[]
    for repeat in protocol['seeds']:
      a,b=next(GroupShuffleSplit(n_splits=1,test_size=.3,random_state=repeat).split(dev,domain,groups=dev.id_student))
      assert set(dev.iloc[a].id_student).isdisjoint(set(dev.iloc[b].id_student))
      transform=ColumnTransformer([('numeric',SimpleImputer(strategy='median',add_indicator=True),FEATURES[:-1]),('module',OneHotEncoder(handle_unknown='ignore',sparse_output=False),['code_module'])])
      model=make_pipeline(transform,HistGradientBoostingClassifier(max_iter=100,max_leaf_nodes=7,l2_regularization=10,random_state=repeat))
      model.fit(dev.iloc[a][FEATURES],domain.iloc[a]);risk=model.predict_proba(dev.iloc[b][FEATURES])[:,1]
      rows.append(dict(seed=repeat,domain_roc_auc=roc_auc_score(domain.iloc[b],risk),fit_n=len(a),evaluation_n=len(b)))
    pd.DataFrame(rows).to_csv(DEST/'period_shift.csv',index=False)
    manifest={'created_utc':datetime.now(timezone.utc).isoformat(),'train_n':len(tr),'validation_n':len(va),'validation_adverse_prevalence':float((va.target!='Success').mean()),'test_rows_used':0,'script_sha256':hashlib.sha256(__import__('pathlib').Path(__file__).read_bytes()).hexdigest(),'development_sha256':hashlib.sha256(pd.util.hash_pandas_object(dev[FEATURES+['target','split']],index=False).values.tobytes()).hexdigest(),'scope':protocol['scope']}
    (DEST/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps(manifest,indent=2))
if __name__=='__main__':run()
