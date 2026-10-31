"""Refit fixed candidates under alternative cutoff/score-availability assumptions.

Cohorts differ across cutoffs: compare policies WITHIN a scenario, not raw
coverage differences across cohorts as model improvement.
"""
import json
from io import StringIO
import pandas as pd
from .data import ROOT,config,prepare
from .models import classifier,FEATURES,risk_from
from .decision import allocate,metrics

def data_sensitivity():
    cfg=config();sel=json.loads((ROOT/'outputs/development_selection.json').read_text(encoding='utf-8'));rows=[]
    for cutoff,delay in [(21,7),(28,0),(28,7),(28,14),(35,7)]:
        scenario={**cfg,'cutoff_day':cutoff,'score_delay_days':delay}
        df,audit=prepare(scenario,write_outputs=False)
        df=pd.read_csv(StringIO(df.to_csv(index=False)))
        train=df[df.split=='train'];val=df[df.split=='validation']
        for kind in ['logistic',sel['selected_model']]:
            m=classifier(kind,cfg['seed']).fit(train[FEATURES],train.target);risk,_=risk_from(m,val);actions=allocate(risk,risk,scenario)
            rows.append({'cutoff_day':cutoff,'score_delay_days_assumed':delay,'model':kind,'no_assessment_rate':float(val.no_early_assessment.mean()),**metrics(val.target,actions,scenario)})
    pd.DataFrame(rows).to_csv(ROOT/'outputs/validation_data_assumptions.csv',index=False)
