"""Check submitted claims against current development artifacts, without scoring test outcomes."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from talentroute.data import ROOT,config
from talentroute.models import FEATURES

out=ROOT/'outputs';cfg=config();checks=[]
def check(name,condition,evidence):
    checks.append({'claim':name,'passed':bool(condition),'evidence':evidence})
    if not condition:raise AssertionError(name)

frame=pd.read_csv(ROOT/'data/processed/enrolments.csv')
audit=json.loads((out/'data_audit.json').read_text(encoding='utf-8'))
check('Partition counts match prepared data',frame.groupby('split').size().to_dict()==audit['split_counts'],'data_audit.json')
check('Enrolment keys are unique',not frame.duplicated(['id_student','code_module','code_presentation']).any(),'prepared enrolments')
ids={s:set(frame.loc[frame.split==s,'id_student']) for s in ['train','validation','test']}
check('Student IDs are disjoint across partitions',all(not ids[a]&ids[b] for a,b in [('train','validation'),('train','test'),('validation','test')]),'prepared grouping keys; no test outcomes evaluated')
check('Predictors exclude protected fields, IDs and outcomes',not set(FEATURES)&{'id_student','gender','disability','target','final_result','date_unregistration'},'models.FEATURES')
val=frame.loc[frame.split=='validation'].reset_index(drop=True)
pred=pd.read_csv(out/'validation_predictions.csv')
check('Predictions align with validation rows only',len(pred)==len(val) and pred.id_student.tolist()==val.id_student.tolist() and pred.target.tolist()==val.target.tolist(),'validation_predictions.csv')
check('Reserved test IDs have no predictions',not set(pred.id_student)&ids['test'],'validation prediction IDs')
rows=pd.read_csv(out/'validation_decision_metrics.csv');bad=pred.target.ne('Success').to_numpy()
for row in rows.itertuples(index=False):
    actions=pred['action_'+row.policy].to_numpy();flagged=actions>0
    cost=int((actions==2).sum())*cfg['human_minutes']+int((actions==1).sum())*cfg['alert_minutes']
    check(row.policy+': coverage and cost reconcile',np.isclose(row.adverse_coverage,flagged[bad].mean()) and np.isclose(row.staff_minutes,cost) and cost<=len(pred)*cfg['staff_minutes_per_100']/100,'validation_decision_metrics.csv + saved actions')
check('All ten figure files exist',len(list(out.glob('*.png')))==10,'outputs/*.png')
# Describe the actual missed cases. These associations do not diagnose causes.
profile=[]
for field in ['no_early_assessment','code_module']:
    for group,idx in pred.groupby(field).groups.items():
        part=pred.loc[idx];adverse=part.target.ne('Success');flag=part.action_classifier_only.gt(0)
        profile.append({'segment':field,'group':str(group),'n':len(part),'adverse_n':int(adverse.sum()),'flagged_adverse_n':int((adverse&flag).sum()),'missed_adverse_n':int((adverse&~flag).sum()),'coverage':float(flag[adverse].mean()) if adverse.any() else None,'interpretation_allowed':bool(len(part)>=50 and adverse.sum()>=10)})
pd.DataFrame(profile).to_csv(out/'missed_case_profile.csv',index=False)
(out/'submission_claim_checks.json').write_text(json.dumps({'scope':'Checks of current prepared data and development artifacts; not a causal or deployment certificate','test_outcomes_scored':False,'checks':checks},indent=2),encoding='utf-8')
print(f'{len(checks)} submission claim checks passed; reserved test outcomes not scored.')
selected=json.loads((out/'development_selection.json').read_text(encoding='utf-8'))
reference=rows.set_index('policy').loc['classifier_only']
walkthrough=f'''TalentRoute: executed workflow and evidence

1. Problem: a distance-learning coordinator prioritises support at day 28. False warnings consume time; missed cases receive no warning. Success is better targeting at equal staff effort, not prevention proved.
2. Source: seven original public OULAD tables, CC BY 4.0. just download-data verifies configured archive/CSV hashes (src/talentroute/data.py).
3. Prepare: enforce decision-time availability and eligibility, build features, fit preprocessing on training only. Counts: {audit['raw_enrolments']} raw; {audit['eligible_enrolments']} eligible; {audit['purged_earlier_repeat_enrolments']} earlier repeats purged. See outputs/data_audit.json.
4. Partition: {len(frame[frame.split=='train'])} train, {len(val)} validation, {len(frame[frame.split=='test'])} reserved test. Only grouping/count metadata from test is used here; no test outcome performance is scored.
5. Models: logistic baseline and boosting candidates; engagement Isolation Forest versus inactivity baseline; exploratory tree/forest/module-logistic comparison. Selected original classifier: {selected['selected_model']}. See outputs/validation_model_search.csv and revision/model_comparison.csv.
6. Decide: shared staff-time constraints, assumed review/alert costs. Provisional operating policy: classifier-only, blend weight zero. The validation-selected blend remains an experiment. See decision.py, demo.py and validation_decision_metrics.csv.
7. Evaluate: classifier-only flags {int(reference.flagged_n)} of {len(val)} enrolments, reaches {reference.adverse_coverage:.2%} of later adverse cases, and uses {reference.staff_minutes:g} staff minutes. No claim that contact changes outcomes. See validation_paired_interval.json and missed_case_profile.csv.
8. Layers: compare escape under one total quota, historical warning-positive profiles, and global/specialist models. Signals share features; statistical independence is not established. See outputs/revision/.
9. Diagnose: training/validation metrics, shuffled-training-label controls and grouped permutation. These generate clues, not proof of no leakage or causal mechanisms. See outputs/diagnostics/.
10. Reproduce: just install; just pipeline. just verify checks {len(checks)} current artifact claims. Test results/runtime belong in outputs/current_pipeline_verification.json. Report: docs/baseline_report.md; browser: review/report.html.

A separate frozen final implementation has already evaluated 2014J. This pipeline scores development data only. Future model revisions need independent validation. Current-run portability evidence is scoped to the recorded environment.
'''
(ROOT/'WALKTHROUGH.txt').write_text(walkthrough,encoding='utf-8')
