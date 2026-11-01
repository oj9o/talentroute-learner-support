"""Exploratory robustness checks: labels evaluate, never rank or allocate."""
from itertools import permutations, combinations
import numpy as np
import pandas as pd
from .decision import allocate, metrics


def seeded_order(scores, seed):
    """Descending score, random fixed-seed secondary key; labels are never consulted."""
    values = np.asarray(scores, float)
    return np.lexsort((np.random.default_rng(seed).random(len(values)), -values))


def shuffled_allocate(scores, cfg, seed):
    permutation = np.random.default_rng(seed).permutation(len(scores))
    result = np.empty(len(scores), dtype=int)
    result[permutation] = allocate(np.asarray(scores)[permutation], np.asarray(scores)[permutation], cfg)
    return result


def robust_checks(train, val, probabilities, cfg, out):
    risk_hgb = 1-probabilities['hgb_15_10'][:, 1]
    bad = (val.target.to_numpy() != 'Success')
    y = val.target.to_numpy()
    budget = len(val)*cfg['staff_minutes_per_100']/100
    baseline = allocate(risk_hgb, risk_hgb, cfg)
    base_h = int((baseline == 2).sum()); total = int((baseline > 0).sum())
    # Feasible near-full-budget action mixes with varying alert caps. Actual labels
    # are used only AFTER selecting cases by risk. No causal effectiveness estimate.
    rows = []
    order = seeded_order(risk_hgb, cfg['seed'])
    base_alert_n = int((baseline == 1).sum())
    base_hbad = int(bad[order[:base_h]].sum())
    base_abad = int(bad[order[base_h:base_h+base_alert_n]].sum())
    for cap in [.2, .4, .6, 1.]:
        for desired_alert_n in sorted({int(len(val)*f) for f in [0., .1, .2, .4, .6, 1.]} | {base_alert_n}):
            alert_n = min(desired_alert_n, int(len(val)*cap), int(budget//cfg['alert_minutes']))
            human_n = min(len(val)-alert_n, int((budget-alert_n*cfg['alert_minutes'])//cfg['human_minutes']))
            spent = human_n*cfg['human_minutes']+alert_n*cfg['alert_minutes']
            if budget-spent >= cfg['human_minutes']:
                continue
            human, alert = order[:human_n], order[human_n:human_n+alert_n]
            hbad, abad = int(bad[human].sum()), int(bad[alert].sum())
            for multiplier in [1., 5., 10., 15., 20.]:
                rows.append({'alert_cap_fraction':cap,'human_n':human_n,'alert_n':alert_n,
                    'staff_minutes':spent,'unused_minutes':budget-spent,
                    'human_adverse_n':hbad,'alert_adverse_n':abad,
                    'reference_tie_rule':'seeded rank; mix matches historical counts, not necessarily historical identities',
                    'targeting_advantage_at_multiplier_1':hbad+abad-base_hbad-base_abad,
                    'crossing_within_scanned_1_to_20':bool(hbad!=base_hbad and 1 <= (base_abad-abad)/(hbad-base_hbad) <= 20),
                    'human_effectiveness_multiplier_assumed':multiplier,
                    'observed_weighted_targeting_units_scenario':multiplier*hbad+abad,
                    'reference_operating_mix':human_n==base_h and alert_n==int((baseline==1).sum()),
                    'reference_weighted_targeting_units_scenario':multiplier*base_hbad+base_abad,
                    'break_even_multiplier_same_reference_effectiveness':
                        (base_abad-abad)/(hbad-base_hbad) if hbad!=base_hbad else np.nan,
                    'break_even_status':'unique_positive' if hbad!=base_hbad and (base_abad-abad)/(hbad-base_hbad)>0 else ('identical_all_multipliers' if hbad==base_hbad and abad==base_abad else 'no_unique_positive_crossing')})
    pd.DataFrame(rows).drop_duplicates().to_csv(out/'action_break_even.csv',index=False)
    # Exact reference operating mix is always included and evaluated with same ordering.
    assert any(r['reference_operating_mix'] for r in rows)
    scores = {'classifier':risk_hgb,
        'assessment':-val.score_mean.fillna(train.score_mean.median()).to_numpy(),
        'behavior_change':-val.engagement_change.to_numpy(),
        'inactivity':val.inactive_days.to_numpy(),
        'business_rule':(-val.score_mean.fillna(50)/100+val.inactive_days/29).to_numpy(),
        'tree':1-probabilities['tree'][:,1]}
    tie_rows = []
    for name, score in scores.items():
        for seed in [7101, 7102, 7103, 7104, 7105]:
            actions = shuffled_allocate(score, cfg, seed)
            tie_rows.append({'score':name,'tie_seed':seed,'unique_score_values':len(np.unique(score)),
                'inactive_29_n':int((val.inactive_days==29).sum()),**metrics(y,actions,cfg)})
    pd.DataFrame(tie_rows).to_csv(out/'tie_sensitivity.csv',index=False)
    layers = ['classifier','assessment','behavior_change','inactivity']
    results, overlap = [], []
    # Fixed exploratory grid; do not select/report just the best permutation or share.
    for seed in [7101,7102,7103]:
        orders = {name:seeded_order(scores[name],seed) for name in layers}
        for a,b in combinations(layers,2):
            sa,sb=set(orders[a][:total]),set(orders[b][:total])
            overlap.append({'seed':seed,'layer_a':a,'layer_b':b,'quota_each':total,
                'jaccard':len(sa&sb)/len(sa|sb)})
        for share in [0., .5, .75, .9, 1.]:
            for layer_order in permutations(layers):
                chosen=list(orders['classifier'][:int(total*share)])
                seen=set(chosen); cursors={name:0 for name in layers}
                while len(chosen)<total:
                    for name in layer_order:
                        order_layer=orders[name]
                        while cursors[name]<len(val) and int(order_layer[cursors[name]]) in seen:
                            cursors[name]+=1
                        if cursors[name]<len(val) and len(chosen)<total:
                            idx=int(order_layer[cursors[name]]);chosen.append(idx);seen.add(idx)
                assert len(chosen) == total
                # Action split is deliberately outside this flag-set diagnostic.
                flagged=np.zeros(len(val),bool);flagged[chosen]=True
                row={'tie_seed':seed,'classifier_first_share':share,
                    'layer_order':'|'.join(layer_order),'flagged_n':int(flagged.sum()),
                    'adverse_coverage':float(flagged[bad].mean()),
                    'escaped_adverse_n':int((bad&~flagged).sum())}
                for outcome in ['Fail','Withdrawn']:
                    mask=y==outcome;row[outcome.lower()+'_coverage']=float(flagged[mask].mean())
                results.append(row)
    pd.DataFrame(results).to_csv(out/'layer_quota_sensitivity.csv',index=False)
    pd.DataFrame(overlap).to_csv(out/'layer_selected_jaccard.csv',index=False)
