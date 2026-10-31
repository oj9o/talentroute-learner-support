"""Check final report structure, evidence consistency and release constraints."""
import json,re
import numpy as np
import pandas as pd
from talentroute.data import ROOT
from talentroute.final_workflow import load_frozen
bundle,manifest=load_frozen();out=ROOT/'outputs/final'
text=(ROOT/'docs/final_report.md').read_text();headings=re.findall(r'^## (\d+)\.',text,re.M)
assert headings==[str(i) for i in range(1,11)]
fenced=False;body=[]
for line in text.splitlines():
 if line.startswith('```'):fenced=not fenced;continue
 if not fenced and not line.startswith(('|','![')):body.append(line)
words=len(' '.join(body).split());assert words<=3000
m=pd.read_csv(out/'test_metrics.csv');assert len(m)==5
assert m.staff_minutes.nunique()==1 and m.flagged_n.nunique()==1
assert (m.staff_minutes<=m.n*manifest['policy']['staff_minutes_per_100']/100).all()
frame=pd.read_csv(ROOT/'data/processed/enrolments.csv');test=frame.loc[frame.split=='test'];bad=int((test.target!='Success').sum())
assert np.allclose(m.adverse_coverage,1-m.missed_adverse_n/bad)
s=pd.read_csv(out/'development_sensitivity.csv');assert s.assumption.nunique()>=3
assert pd.read_csv(out/'development_seed_stability.csv').seed.nunique()>=3
assert all((out/name).is_file() for name in ['ablation.png','sensitivity.png','test_primary_intervals.csv','test_paired_intervals.csv'])
result={'report_body_words':words,'report_sections':len(headings),'same_budget_policies':len(m),'decision_assumptions_varied':int(s.assumption.nunique()),'detector_seeds':3,'frozen_hashes_verified':True,'recorded_test_metrics_reconciled':True,'linux_container_execution':'not verified for this release','component_acceptance':json.loads((out/'acceptance.json').read_text())['accepted']}
(out/'requirements_check.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
