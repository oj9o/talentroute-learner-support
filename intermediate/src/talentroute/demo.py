"""Offline aggregate demo; no real student identifiers are displayed."""
import json
import pandas as pd
from .data import ROOT,config
from .decision import allocate

def demo(budget):
    cfg={**config(),'staff_minutes_per_100':budget};df=pd.read_csv(ROOT/'outputs/validation_predictions.csv')
    a=allocate(df.risk,df.anomaly,cfg,0.)
    print(json.dumps({'policy':'classifier_only_provisional_reference','scenario':'Validation cohort; workload illustration, not prevented failures','staff_minutes_per_100':budget,'cohort_size':len(df),'human_reviews':int((a==2).sum()),'alerts':int((a==1).sum()),'no_action':int((a==0).sum()),'total_effort_minutes':int((a==2).sum()*cfg['human_minutes']+(a==1).sum()*cfg['alert_minutes'])},indent=2))
    # A synthetic case label preserves a usable ranked worklist without exposing dataset IDs.
    work=pd.DataFrame({'case_reference':['CASE-'+str(i+1).zfill(5) for i in range(len(df))],'risk_score':df.risk,'anomaly_percentile':df.anomaly,'action':pd.Series(a).map({0:'no_action',1:'alert',2:'human_review'})})
    work.loc[a>0].sort_values('risk_score',ascending=False).to_csv(ROOT/'outputs/demo_worklist.csv',index=False)
