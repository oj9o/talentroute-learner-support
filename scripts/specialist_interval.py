"""Paired development-only specialist check; no test prediction or selection."""
import pandas as pd
from talentroute.data import ROOT,config
from talentroute.models import classifier,FEATURES
from talentroute.revision import aligned_probability
from talentroute.model_intervals import paired_intervals

def main():
    df=pd.read_csv(ROOT/'data/processed/enrolments.csv');train=df.loc[df.split=='train'];val=df.loc[df.split=='validation'];del df
    seed=config()['seed'];global_model=classifier('logistic',seed).fit(train[FEATURES],train.target)
    original=aligned_probability(global_model,val);hybrid=original.copy()
    for module,part in train.groupby('code_module'):
        counts=part.target.value_counts();ix=(val.code_module.to_numpy()==module).nonzero()[0]
        if len(part)>=300 and all(counts.get(c,0)>=30 for c in ['Fail','Success','Withdrawn']) and len(ix):
            m=classifier('logistic',seed).fit(part[FEATURES],part.target);hybrid[ix]=aligned_probability(m,val.iloc[ix])
    rows=paired_intervals(val.target,val.id_student,original,hybrid,2000,seed)
    pd.DataFrame(rows).to_csv(ROOT/'outputs/revision/specialist_minus_global_intervals.csv',index=False)
if __name__=='__main__':main()
