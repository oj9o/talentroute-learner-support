"""Evidence contract checks; development diagnostics must not expose held-out rows."""
import json
import pandas as pd
import pytest
from talentroute.data import ROOT


def test_diagnostic_fingerprint_and_negative_controls():
    dest=ROOT/'outputs/diagnostics'
    if not (dest/'evidence_fingerprint.json').exists():
        pytest.skip('Run diagnostics before checking generated evidence')
    fingerprint=json.loads((dest/'evidence_fingerprint.json').read_text(encoding='utf-8'))
    assert fingerprint['test_scored'] is False
    assert fingerprint['code_sha256']
    trials=pd.read_csv(dest/'shuffled_training_labels.csv')
    assert trials.seed.nunique()==10
    assert trials.adverse_roc_auc.between(0,1).all()
    ladder=pd.read_csv(dest/'train_validation_metrics.csv')
    assert set(ladder.split)=={'train_resubstitution','validation_selection'}
    baseline=json.loads((dest/'classifier_minus_rule.json').read_text(encoding='utf-8'))
    assert baseline['adverse_cases']>0
    assert baseline['ci95'][0]<=baseline['ci95'][1]
