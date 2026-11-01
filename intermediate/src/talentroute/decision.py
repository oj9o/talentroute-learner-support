"""Transparent triage: priority human reviews and distinct low-effort alerts.

Coverage is an outcome-targeting metric, never an intervention-effect estimate.
"""
import numpy as np

def allocate(risk, anomaly, cfg, weight=0., uncertainty=None):
    """Reserve scarce human review by blended rank; alerts address remaining warnings.

    Effort costs are scenario assumptions. No causal utility is asserted.
    """
    risk=np.asarray(risk,float); anomaly=np.asarray(anomaly,float); n=len(risk)
    if n==0: return np.array([],dtype=int)
    if not np.isfinite(risk).all() or not np.isfinite(anomaly).all(): raise ValueError('Nonfinite scores')
    if not 0<=weight<=1: raise ValueError('Invalid blend')
    if not 0<=cfg['alert_budget_fraction']<=1 or not 0<=cfg['max_alert_fraction']<=1: raise ValueError('Invalid alert constraints')
    if cfg['human_minutes']<=0 or cfg['alert_minutes']<=0 or cfg['staff_minutes_per_100']<0: raise ValueError('Invalid effort budget')
    score=(1-weight)*risk+weight*anomaly
    if uncertainty is not None: score=score+cfg['uncertainty_bonus']*np.asarray(uncertainty)
    budget=n*cfg['staff_minutes_per_100']/100
    # Explicitly reserve up to 20% of budget for broad, low-effort alerts.
    reserve=min(budget*cfg['alert_budget_fraction'],int(n*cfg['max_alert_fraction'])*cfg['alert_minutes'])
    human_n=min(n,int((budget-reserve)//cfg['human_minutes']))
    order=np.argsort(-score,kind='stable'); actions=np.zeros(n,dtype=int); actions[order[:human_n]]=2
    remaining=budget-human_n*cfg['human_minutes']
    alert_n=min(n-human_n,int(n*cfg['max_alert_fraction']),int(remaining//cfg['alert_minutes']))
    # Remaining anomaly warnings can trigger low-effort alerts, with the same order for all policies.
    available=order[human_n:];actions[available[:alert_n]]=1
    assert (actions==2).sum()*cfg['human_minutes']+(actions==1).sum()*cfg['alert_minutes']<=budget+1e-8
    return actions

def metrics(y, actions, cfg):
    y=np.asarray(y); actions=np.asarray(actions); bad=y!='Success'; flagged=actions>0; human=actions==2
    result={'n':len(y),'flagged_n':int(flagged.sum()),'human_n':int(human.sum()),'alert_n':int((actions==1).sum()),'adverse_coverage':float(flagged[bad].mean()) if bad.any() else np.nan,'human_precision':float(bad[human].mean()) if human.any() else np.nan,'flag_precision':float(bad[flagged].mean()) if flagged.any() else np.nan,'missed_adverse_n':int((bad&~flagged).sum()),'staff_minutes':float(human.sum()*cfg['human_minutes']+(actions==1).sum()*cfg['alert_minutes'])}
    for label in ['Fail','Withdrawn']:
        mask=y==label; result[label.lower()+'_coverage']=float(flagged[mask].mean()) if mask.any() else np.nan
    return result
