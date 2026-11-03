"""Paired student-cluster bootstrap conditional on already fitted models."""
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score


def paired_intervals(y, student_ids, first, second, repeats=300, seed=7101):
    """Return second-minus-first AP intervals from paired student-cluster resamples."""
    y=np.asarray(y);ids=np.asarray(student_ids)
    unique,inverse=np.unique(ids,return_inverse=True)
    rng=np.random.default_rng(seed);rows=[]
    targets={'adverse':y!='Success','fail':y=='Fail','withdrawn':y=='Withdrawn'}
    for _ in range(repeats):
        cluster_counts=np.bincount(rng.integers(0,len(unique),len(unique)),minlength=len(unique))
        weights=cluster_counts[inverse]
        if not all(weights[target].sum()>0 and weights[~target].sum()>0 for target in targets.values()):
            continue
        values={}
        for key,target in targets.items():
            column={'fail':0,'withdrawn':2}.get(key)
            p1=1-first[:,1] if column is None else first[:,column]
            p2=1-second[:,1] if column is None else second[:,column]
            values[key]=average_precision_score(target,p2,sample_weight=weights)-average_precision_score(target,p1,sample_weight=weights)
        rows.append(values)
    if not rows:raise ValueError('No valid paired bootstrap draws')
    records=[]
    for key in targets:
        values=np.array([r[key] for r in rows]);lo,hi=np.quantile(values,[.025,.975])
        records.append({'metric':key+'_pr_auc','difference_mean':values.mean(),'ci95_lower':lo,
            'ci95_upper':hi,'valid_repeats':len(values),'contains_zero':bool(lo<=0<=hi),
            'interpretation':'exploratory, conditional on fitted models and original validation selection'})
    return records
