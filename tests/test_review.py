"""Verify that the static interface embeds exact current aggregate evidence."""
import json
from pathlib import Path
import pandas as pd
import pytest
from talentroute.data import ROOT


def payload():
    path=ROOT/'review/index.html'
    if not path.exists():pytest.skip('Run just review to generate interface')
    text=path.read_text(encoding='utf-8');raw=text.split('<script id="project-data" type="application/json">',1)[1].split('</script>',1)[0]
    return text,json.loads(raw)


def test_interface_uses_current_model_outputs_and_computed_budgets():
    text,data=payload()
    sources = {
        'models':'revision/model_comparison.csv', 'policies':'validation_decision_metrics.csv',
        'budgets':'validation_sensitivity.csv', 'intervals':'revision/forest_minus_hgb_intervals.csv',
        'layers':'revision/layer_quota_sensitivity.csv', 'jaccard':'revision/layer_selected_jaccard.csv',
        'breakEven':'revision/action_break_even.csv', 'ties':'revision/tie_sensitivity.csv',
        'profiles':'revision/warning_outcome_profiles.csv', 'ladder':'diagnostics/train_validation_metrics.csv',
        'shuffled':'diagnostics/shuffled_training_labels.csv', 'permutation':'diagnostics/grouped_permutation.csv',
    }
    for key, source in sources.items():
        expected=json.loads(pd.read_csv(ROOT/'outputs'/source).to_json(orient='records'))
        assert data[key]==expected, f'Stale interface evidence: {source}' 
    budgets={r['value'] for r in data['budgets'] if r['assumption']=='staff_minutes_per_100'}
    assert budgets=={150.,300.,600.}
    assert ('PRIOR UBUNTU VM RUN · CURRENT RESULTS LOCAL' if data['linuxVerified'] else 'LINUX EXECUTION UNVERIFIED') in text


def test_interface_excludes_student_records_and_keeps_metric_units():
    text,data=payload()
    assert not any('id_student' in row for name in ['models','policies','layers','budgets'] for row in data[name])
    assert data['outcomeCounts']['adverse']==data['outcomeCounts']['fail']+data['outcomeCounts']['withdrawn']
    assert 'https://' not in text and 'fonts.googleapis' not in text
    assert "value.toFixed(4)" in (ROOT/'review/review.js').read_text(encoding='utf-8')
    for source in ['baseline_report.md','project_definition.md','data_dictionary.md']:
        assert (ROOT/'docs'/source).is_file()


def test_saved_interface_links_resolve_in_extracted_package():
    from html.parser import HTMLParser
    class Links(HTMLParser):
        def __init__(self):
            super().__init__(); self.paths=[]
        def handle_starttag(self, tag, attrs):
            for key,value in attrs:
                if key in {'href','src'} and value and not value.startswith(('#','https:','http:','data:')):
                    self.paths.append(value)
    text,_=payload(); links=Links(); links.feed(text)
    assert links.paths
    for path in links.paths:
        assert (ROOT/'review'/path).is_file(), f'Missing submission link: {path}'


def test_development_overview_has_no_identifiers_or_test_rows():
    path=ROOT/'outputs/eda_sample_records.csv'
    if not path.exists():pytest.skip('Run just eda before checking saved overview')
    frame=pd.read_csv(path)
    assert len(frame)>0
    assert 'id_student' not in frame
    assert set(frame['split']) <= {'train','validation'}
    assert (ROOT/'outputs/eda_feature_types.csv').is_file()
    assert (ROOT/'outputs/eda_numeric_summary.csv').is_file()


def test_report_diagnostic_prose_survives_table_rendering():
    """A CSV closing fence must not swallow the next explanatory paragraph."""
    markdown=(ROOT/'docs/baseline_report.md').read_text(encoding='utf-8')
    assert all(line in {'```','```csv'} for line in markdown.splitlines() if line.startswith('```'))
    rendered=ROOT/'review/report.html'
    if not rendered.exists():pytest.skip('Run just review before checking rendered report')
    assert 'shuffled-training-label controls' in rendered.read_text(encoding='utf-8')
