"""Seed stability of the added outlier component on a fixed validation split."""
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from .data import ROOT,config
from .models import preprocessing,ENG,CAT,predictions
from .decision import allocate,metrics

def stability():
    cfg=config();df=pd.read_csv(ROOT/'data/processed/enrolments.csv');train=df[df.split=='train'];val=df[df.split=='validation'].reset_index(drop=True)
    b=joblib.load(ROOT/'outputs/development_models.joblib');pred,_=predictions(b,val);rows=[]
    for seed in [7101,7102,7103]:
        m=Pipeline([('preprocess',preprocessing(ENG)),('model',IsolationForest(n_estimators=150,max_samples=512,random_state=seed,n_jobs=1))]);m.fit(train[ENG+CAT]);ref=np.sort(-m.score_samples(train[ENG+CAT]));a=np.searchsorted(ref,-m.score_samples(val[ENG+CAT]),side='right')/len(ref)
        for weight in [0.,.2,b['chosen_weight']]: rows.append({'seed':seed,'weight':weight,**metrics(pred.target,allocate(pred.risk,a,cfg,weight),cfg)})
    pd.DataFrame(rows).drop_duplicates(['seed','weight']).to_csv(ROOT/'outputs/validation_seed_stability.csv',index=False)
