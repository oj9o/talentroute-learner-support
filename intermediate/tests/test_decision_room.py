"""Ensure the guided experience uses exact aggregate evidence and safe boundaries."""
import json
import pandas as pd
import pytest
from talentroute.data import ROOT


def payload():
    path=ROOT/'review/decision_room.html'
    if not path.exists():pytest.skip('Run just review to generate the decision room')
    text=path.read_text()
    raw=text.split('<script id="room-evidence" type="application/json">',1)[1].split('</script>',1)[0]
    return json.loads(raw),text


def test_decision_room_reconciles_models_and_same_budget_inputs():
    data,_=payload()
    for key,file in [('models','revision/model_comparison.csv'),('policies','validation_decision_metrics.csv')]:
        assert data[key]==json.loads(pd.read_csv(ROOT/'outputs'/file).to_json(orient='records'))
    assert data['blend_interval']==json.loads((ROOT/'outputs/validation_paired_interval.json').read_text())
    rows=pd.DataFrame(data['budgets'])
    assert set(rows.value)=={150,300,600}
    for _,part in rows.groupby('value'):
        assert part.n.nunique()==1 and part.staff_minutes.nunique()==1
        assert (part.staff_minutes<=part.n*part.value/100).all()


def test_decision_room_contains_no_row_level_records_or_external_dependencies():
    data,text=payload()
    for key in ['models','policies','budgets']:
        assert all('id_student' not in row and 'target' not in row for row in data[key])
    assert 'ILLUSTRATIVE STAKEHOLDER QUESTION' in text
    assert 'https://' not in text
    script=(ROOT/'review/decision_room.js').read_text()
    assert 'fetch(' not in script and 'localStorage' not in script
