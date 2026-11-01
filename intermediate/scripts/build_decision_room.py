"""Generate an offline guided decision experience from development evidence."""
from pathlib import Path
import json
import shutil
import pandas as pd
from talentroute.data import ROOT


def build():
    out=ROOT/'outputs';dest=ROOT/'review';dest.mkdir(exist_ok=True)
    model=pd.read_csv(out/'revision/model_comparison.csv')
    policy=pd.read_csv(out/'validation_decision_metrics.csv')
    budgets=pd.read_csv(out/'validation_sensitivity.csv')
    interval=json.loads((out/'validation_paired_interval.json').read_text())
    paired=pd.read_csv(out/'revision/forest_minus_hgb_intervals.csv')
    prevalence=json.loads((out/'diagnostics/classifier_minus_rule.json').read_text())
    payload={'scope':'Exploratory validation evidence; separate final evaluation already recorded. No model fitting or test scoring occurs in this interface.',
      'models':json.loads(model.to_json(orient='records')),
      'policies':json.loads(policy.to_json(orient='records')),
      'budgets':json.loads(budgets[(budgets.assumption=='staff_minutes_per_100') & budgets.policy.isin(['business_rule','classifier_only','coupled_fixed_020'])].to_json(orient='records')),
      'model_intervals':json.loads(paired.to_json(orient='records')),
      'blend_interval':interval,'adverse_n':prevalence['adverse_cases'],
      'sources':{'models':'../outputs/revision/model_comparison.csv','intervals':'../outputs/revision/forest_minus_hgb_intervals.csv','blend':'../outputs/validation_paired_interval.json','policies':'../outputs/validation_decision_metrics.csv','budgets':'../outputs/validation_sensitivity.csv'}}
    (out/'decision_room.json').write_text(json.dumps(payload,indent=2))
    template=ROOT/'scripts/review_ui/decision_room.html'
    text=template.read_text().replace('__EVIDENCE__',json.dumps(payload).replace('<','\\u003c'))
    (dest/'decision_room.html').write_text(text)
    for name in ['decision_room.css','decision_room.js']:shutil.copy2(ROOT/'scripts/review_ui'/name,dest/name)
    print('Built offline decision room from saved development evidence')

if __name__=='__main__':build()
