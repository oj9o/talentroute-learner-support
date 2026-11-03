"""Exploratory model and action-value checks; reserved test is never scored."""
import json
import time
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from .data import ROOT, config
from .models import FEATURES, NUM, ENG, preprocessing, classifier, model_metrics
from .decision import allocate, metrics


def candidate(name, seed):
    """Return an unfitted fixed tree, forest or supervised baseline pipeline."""
    if name == 'tree':
        estimator = DecisionTreeClassifier(max_depth=5, min_samples_leaf=40, random_state=seed)
    elif name == 'forest':
        estimator = RandomForestClassifier(n_estimators=180, max_depth=12,
            min_samples_leaf=15, max_features='sqrt', n_jobs=2, random_state=seed)
    else:
        return classifier(name, seed)
    return Pipeline([('preprocess', preprocessing(NUM + ENG)), ('model', estimator)])


def aligned_probability(model, frame):
    """Keep the meaning of each probability column consistent across specialists."""
    labels = ['Fail', 'Success', 'Withdrawn']
    raw = model.predict_proba(frame[FEATURES])
    return raw[:, [list(model.classes_).index(label) for label in labels]]


def segment_results(name, frame, probability, actions, cfg):
    """Evaluate pre-existing shared-budget actions; never reallocate within a slice."""
    rows=[]
    for field in ['code_module','no_early_assessment']:
        for group, indices in frame.groupby(field).indices.items():
            y=frame.iloc[indices].target
            if len(y)<50 or y.ne('Success').sum()<10:continue
            values=model_metrics(y,probability[indices],['Fail','Success','Withdrawn'])
            for outcome in ['Fail','Withdrawn']:
                count=int(y.eq(outcome).sum());stable=count>=10 and len(y)-count>=10
                values[outcome.lower()+'_positive_n']=count
                values[outcome.lower()+'_stable']=stable
                if not stable:values[outcome.lower()+'_pr_auc']=np.nan
            action_metrics=metrics(y,actions[indices],cfg)
            rows.append({'model':name,'segment':field,'group':group,
                'adverse_n':int(y.ne('Success').sum()),**values,**action_metrics,
                'allocation_scope':'shared cohort budget; no per-segment reallocation'})
    return rows


def warning_profiles(frame, actions_by_policy):
    """Describe observed outcomes within each fixed warning policy, without causal labels."""
    rows=[]
    fields=['log_clicks','inactive_days','engagement_change','score_mean','no_early_assessment']
    for policy, actions in actions_by_policy.items():
        part=frame[['target',*fields]].copy();part['flagged']=np.asarray(actions)>0
        for (flagged,outcome), group in part.groupby(['flagged','target']):
            if len(group)<50:continue
            for field in fields:
                observed=int(group[field].notna().sum())
                rows.append({'policy':policy,'flagged':flagged,'outcome':outcome,'feature':field,
                    'n':len(group),'observed_n':observed,'missing_fraction':1-observed/len(group),
                    'median':group[field].median(),'mean':group[field].mean()})
    return pd.DataFrame(rows)


def revision():
    """Save fixed development comparisons and three commitment audits; never score test."""
    cfg = config()
    frame = pd.read_csv(ROOT / 'data/processed/enrolments.csv')
    # Filter first; no reserved test prediction, summary or outcome metric is produced.
    dev = frame.loc[frame.split.isin(['train', 'validation'])].copy()
    del frame
    train = dev.loc[dev.split == 'train']
    val = dev.loc[dev.split == 'validation']
    out = ROOT / 'outputs/revision'; out.mkdir(exist_ok=True)
    records, segments, timings, predictions = [], [], [], {}
    for name in ['logistic', 'tree', 'forest', 'hgb_15_10']:
        start = time.monotonic()
        model = candidate(name, cfg['seed']).fit(train[FEATURES], train.target)
        p = aligned_probability(model, val)
        predictions[name] = p
        risk = 1 - p[:, 1]
        records.append({'model': name, **model_metrics(val.target, p, ['Fail','Success','Withdrawn']),
                        **metrics(val.target, allocate(risk, risk, cfg), cfg)})
        segments.extend(segment_results(name,val,p,allocate(risk,risk,cfg),cfg))
        timings.append({'model': name, 'fit_and_evaluation_seconds': time.monotonic()-start})
    # Fixed exploratory design: module-specific logistic models, eligibility from TRAINING ONLY.
    # No selecting the winning module by validation errors and then claiming independent evidence.
    p = predictions['logistic'].copy(); eligibility = []
    for module in sorted(set(train.code_module)|set(val.code_module)):
        part=train[train.code_module==module]
        counts = part.target.value_counts()
        eligible = len(part) >= 300 and all(counts.get(c, 0) >= 30 for c in ['Fail','Success','Withdrawn'])
        ix = np.flatnonzero(val.code_module.to_numpy() == module)
        eligibility.append({'module': module, 'training_n': len(part), 'eligible': eligible,
                            'validation_n': len(ix), 'specialist_used': bool(eligible and len(ix))})
        if eligible and len(ix):
            specialist = classifier('logistic', cfg['seed']).fit(part[FEATURES], part.target)
            p[ix] = aligned_probability(specialist, val.iloc[ix])
    predictions['module_logistic_hybrid']=p.copy()
    risk_hybrid = 1-p[:, 1]
    hybrid_actions=allocate(risk_hybrid,risk_hybrid,cfg)
    segments.extend(segment_results('module_logistic_hybrid',val,p,hybrid_actions,cfg))
    records.append({'model': 'module_logistic_hybrid',
        **model_metrics(val.target, p, ['Fail','Success','Withdrawn']),
        **metrics(val.target, allocate(risk_hybrid, risk_hybrid, cfg), cfg)})
    pd.DataFrame(records).to_csv(out/'model_comparison.csv', index=False)
    pd.DataFrame(segments).to_csv(out/'model_segments.csv', index=False)
    pd.DataFrame(eligibility).to_csv(out/'specialist_eligibility.csv', index=False)
    pd.DataFrame(timings).to_csv(out/'runtime.csv', index=False)
    from .model_intervals import paired_intervals
    interval_rows = paired_intervals(val.target, val.id_student,
        predictions['hgb_15_10'], predictions['forest'], 2000, cfg['seed'])
    pd.DataFrame(interval_rows).to_csv(out/'forest_minus_hgb_intervals.csv', index=False)
    from .revision_checks import robust_checks
    robust_checks(train, val, predictions, cfg, out)
    risk_hgb = 1-predictions['hgb_15_10'][:, 1]
    # Same TOTAL number of flags as classifier-only: round-robin unique warnings.
    base_actions = allocate(risk_hgb, risk_hgb, cfg)
    human_n = int((base_actions == 2).sum())
    total_flags = int((base_actions > 0).sum())
    score_arrays = {
        'classifier': risk_hgb,
        'assessment': -val.score_mean.fillna(train.score_mean.median()).to_numpy(),
        'behavior_change': -val.engagement_change.to_numpy(),
        'inactivity': val.inactive_days.to_numpy(),
    }
    orders = [np.argsort(-values, kind='stable') for values in score_arrays.values()]
    chosen, seen, cursors = [], set(), [0]*len(orders)
    while len(chosen) < total_flags:
        for j, order in enumerate(orders):
            while cursors[j] < len(order) and int(order[cursors[j]]) in seen:
                cursors[j] += 1
            if cursors[j] < len(order) and len(chosen) < total_flags:
                idx = int(order[cursors[j]]); chosen.append(idx); seen.add(idx)
    layered = np.zeros(len(val), dtype=int)
    layered[chosen[:human_n]] = 2; layered[chosen[human_n:]] = 1
    pd.DataFrame([
        {'policy': 'classifier_only', **metrics(val.target, base_actions, cfg)},
        {'policy': 'four_layer_round_robin', **metrics(val.target, layered, cfg)}
    ]).to_csv(out/'same_quota_layers.csv', index=False)
    pd.DataFrame(score_arrays).corr(method='spearman').to_csv(out/'layer_rank_correlations.csv')
    # Retrospective descriptions, not mechanisms of resilience or intervention success.
    profile = val[['target','log_clicks','inactive_days','engagement_change','score_mean',
                   'no_early_assessment']].copy()
    profile['flagged'] = layered > 0
    rows = []
    for (flagged, outcome), part in profile.groupby(['flagged','target']):
        if len(part) < 50:
            continue
        for field in ['log_clicks','inactive_days','engagement_change','score_mean',
                      'no_early_assessment']:
            rows.append({'flagged': flagged, 'outcome': outcome, 'feature': field,
                         'n': len(part), 'observed_n': int(part[field].notna().sum()),
                         'median': part[field].median()})
    pd.DataFrame(rows).to_csv(out/'warning_outcome_profiles.csv', index=False)
    # Canonical saved policies anchor profiles; historical layer descriptions stay separate.
    saved=pd.read_csv(ROOT/'outputs/validation_predictions.csv')
    assert saved.id_student.tolist()==val.id_student.tolist()
    assert saved.code_module.tolist()==val.code_module.tolist() and saved.target.tolist()==val.target.tolist()
    actions_by_policy={name:saved['action_'+name].to_numpy() for name in ['classifier_only','anomaly_rule','anomaly_only','coupled_selected']}
    warning_profiles(val,actions_by_policy).to_csv(out/'policy_warning_profiles.csv',index=False)
    layer_segments=[]
    for field in ['code_module','no_early_assessment']:
        for group,indices in val.groupby(field).indices.items():
            y=val.iloc[indices].target
            for name,actions in [('classifier_only',base_actions),('four_layer_round_robin',layered)]:
                layer_segments.append({'segment':field,'group':str(group),'policy':name,
                    'adverse_n':int(y.ne('Success').sum()),
                    'interpretation_allowed':bool(len(y)>=50 and y.ne('Success').sum()>=10),
                    **metrics(y,actions[indices],cfg)})
    pd.DataFrame(layer_segments).to_csv(out/'layer_segments.csv',index=False)
    (out/'scope.json').write_text(json.dumps({'test_scored': False,
        'status': 'exploratory post-original-validation revision; not confirmatory',
        'specialist_design': 'module logistic; train n>=300 and each class>=30; global fallback',
        'action_values': 'hypothetical relative effectiveness; not measured causal benefit'}, indent=2), encoding='utf-8')
    return records
