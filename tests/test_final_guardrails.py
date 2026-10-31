"""Protect frozen evaluation and the final candidate's budget semantics."""
import json
import numpy as np
import pandas as pd
import pytest
from talentroute.decision import allocate
from talentroute import final_workflow as workflow

def test_frozen_data_change_refuses_evaluation(tmp_path,monkeypatch):
    monkeypatch.setattr(workflow,'ROOT',tmp_path)
    (tmp_path/'src').mkdir();(tmp_path/'configs').mkdir();(tmp_path/'configs/policy.json').write_text('{}')
    out=tmp_path/'outputs/final';out.mkdir(parents=True)
    model=out/'frozen_models.joblib';model.write_bytes(b'not loaded unless hashes pass')
    data=tmp_path/'data/processed';data.mkdir(parents=True)
    f=data/'enrolments.csv';f.write_text('split\ntrain\n')
    manifest={'implementation_sha256':workflow.implementation_hash(),'model_sha256':workflow.digest(model),'processed_sha256':workflow.digest(f)}
    (out/'freeze.json').write_text(json.dumps(manifest))
    f.write_text('split\ntest\n')
    with pytest.raises(RuntimeError,match='changed'):
        workflow.load_frozen()

def test_shared_capacity_not_union_of_separate_layer_budgets():
    cfg={'staff_minutes_per_100':300,'human_minutes':30,'alert_minutes':2,'alert_budget_fraction':.2,'max_alert_fraction':.2}
    risk=np.linspace(.45,.55,100);anomaly=np.linspace(1,0,100)
    a=allocate(risk,anomaly,cfg,.2)
    assert (a==2).sum()*30+(a==1).sum()*2<=300
    assert np.array_equal(a,allocate(risk,anomaly,cfg,.2))
    # Both inputs must affect a nontrivial connected candidate's prioritisation.
    assert not np.array_equal(a,allocate(risk,np.roll(anomaly,50),cfg,.2))
