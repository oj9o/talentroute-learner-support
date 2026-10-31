"""Development diagnostics inspired by Labs 9/10; no reserved test predictions."""
import hashlib
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from .data import ROOT, config
from .models import FEATURES, ENG, NUM, classifier, model_metrics, predictions, risk_from
from .decision import allocate
from .evaluation import cluster_interval


def diagnostics():
    cfg=config();out=ROOT/'outputs';dest=out/'diagnostics';dest.mkdir(parents=True,exist_ok=True)
    frame=pd.read_csv(ROOT/'data/processed/enrolments.csv')
    dev=frame[frame.split.isin(['train','validation'])].copy();del frame
    train=dev[dev.split=='train'];val=dev[dev.split=='validation'].reset_index(drop=True)
    bundle=joblib.load(out/'development_models.joblib');selected=bundle['selected_model']
    rows=[]
    for name in ['logistic',selected]:
        for split,part in [('train_resubstitution',train),('validation_selection',val)]:
            _,p=risk_from(bundle['models'][name],part)
            rows.append({'model':name,'split':split,'n':len(part),**model_metrics(part.target,p,bundle['classes'])})
    pd.DataFrame(rows).to_csv(dest/'train_validation_metrics.csv',index=False)
    pred,_=predictions(bundle,val)
    base=allocate(pred.risk,pred.anomaly,cfg);rule=allocate(pred.rule,pred.rule,cfg)
    interval=cluster_interval(pred,base,rule,cfg['bootstrap_repeats'],cfg['seed'])
    bad=(pred.target!='Success').to_numpy()
    (dest/'classifier_minus_rule.json').write_text(json.dumps({
        'coverage_difference':float((base[bad]>0).mean()-(rule[bad]>0).mean()),
        'extra_adverse_cases_flagged':int((bad&(base>0)).sum()-(bad&(rule>0)).sum()),
        'adverse_cases':int(bad.sum()),'ci95':interval,'bootstrap_repeats':cfg['bootstrap_repeats'],
        'status':'exploratory validation; fixed fitted models and operating rules; selection not removed'
    },indent=2),encoding='utf-8')
    # Limited negative control: repeat the full fixed-model training with shuffled training labels.
    # This is a diagnostic, not a proof of absence of leakage or an independent hypothesis test.
    shuffled=[]
    for repeat in range(10):
        seed=cfg['seed']+repeat
        labels=np.random.default_rng(seed).permutation(train.target.to_numpy())
        model=classifier(selected,seed).fit(train[FEATURES],labels)
        risk,_=risk_from(model,val)
        shuffled.append({'repeat':repeat,'seed':seed,'adverse_roc_auc':roc_auc_score(val.target!='Success',risk)})
    pd.DataFrame(shuffled).to_csv(dest/'shuffled_training_labels.csv',index=False)
    # Move correlated features together to retain their internal consistency.
    groups={'assessment':NUM[:5], 'engagement':ENG, 'study_history':NUM[5:], 'module':['code_module']}
    model=bundle['models'][selected];risk,_=risk_from(model,val)
    original=roc_auc_score(val.target!='Success',risk);permuted=[]
    for name,columns in groups.items():
        for repeat in range(5):
            changed=val[FEATURES].copy();order=np.random.default_rng(cfg['seed']+repeat).permutation(len(val))
            changed[columns]=val[columns].iloc[order].to_numpy()
            shifted,_=risk_from(model,changed)
            permuted.append({'feature_group':name,'repeat':repeat,'metric':'adverse_roc_auc',
                'original':original,'permuted':roc_auc_score(val.target!='Success',shifted),
                'decrease':original-roc_auc_score(val.target!='Success',shifted)})
    pd.DataFrame(permuted).to_csv(dest/'grouped_permutation.csv',index=False)
    sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted((ROOT/'src/talentroute').glob('*.py'))}
    fingerprint={'code_sha256':sources,'config':cfg,'data_manifest':json.loads((ROOT/'data/raw/manifest.json').read_text(encoding='utf-8')),
        'development_frame_sha256':hashlib.sha256(pd.util.hash_pandas_object(dev[FEATURES+['target','split']],index=False).values.tobytes()).hexdigest(),
        'model':selected,'test_scored':False,'scope':'validation diagnostics after original model selection; not a final-specification freeze'}
    (dest/'evidence_fingerprint.json').write_text(json.dumps(fingerprint,indent=2),encoding='utf-8')
