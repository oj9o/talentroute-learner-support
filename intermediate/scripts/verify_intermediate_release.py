"""Check required Intermediate artifacts and word count; not a grading prediction."""
from html.parser import HTMLParser
from pathlib import Path
import json
from talentroute.data import ROOT


def verify():
    excluded={'FEEDBACK_PRESERVATION.md','INTERMEDIATE_REVISION.md'}
    markdown=[ROOT/'README.md',*[p for p in (ROOT/'docs').glob('*.md') if p.name not in excluded],*(ROOT/'evidence').rglob('README.md')]
    counts={str(p.relative_to(ROOT)):len(p.read_text().split()) for p in markdown}
    assert sum(counts.values())<3000,counts
    required=['pyproject.toml','uv.lock','.python-version','Justfile','docs/project_definition.md','docs/data_dictionary.md','docs/baseline_report.md','review/index.html','review/report.html','review/investigations.html','review/decision_room.html','outputs/validation_model_search.csv','outputs/validation_anomaly_proxy_metrics.csv','outputs/validation_decision_metrics.csv','outputs/validation_primary_intervals.csv','outputs/submission_claim_checks.json','outputs/investigations/manifest.json','outputs/development_evidence.json','outputs/development_segment_tradeoffs.csv']
    assert all((ROOT/p).is_file() for p in required)
    assert len(list((ROOT/'outputs').glob('*.png')))==10
    missing=[]
    class Links(HTMLParser):
        def handle_starttag(self,tag,attrs):
            for key,val in attrs:
                if key in {'href','src'} and val and not val.startswith(('#','http:','https:','data:')):
                    if not (ROOT/'review'/val).is_file():missing.append(val)
    for file in ['index.html','report.html','investigations.html','decision_room.html']:
        Links().feed((ROOT/'review'/file).read_text())
    assert not missing,missing
    manifest=json.loads((ROOT/'outputs/investigations/manifest.json').read_text())
    assert manifest['test_rows_used']==0
    interpretation=json.loads((ROOT/'outputs/development_evidence.json').read_text())
    assert interpretation['test_rows_used']==0 and not interpretation['new_model_selection']
    assert interpretation['final_2014J_already_observed']
    result={'scope':'Artifact and consistency checks, not a grading or deployment certificate','combined_markdown_words':sum(counts.values()),'word_counts':counts,'required_files_checked':len(required),'eda_figures':10,'interface_links_resolve':True,'new_diagnostics_test_rows':0,'separate_final_evaluation_already_observed':True,'rubric_evidence':{'setup':'pyproject.toml, uv.lock, .python-version','automation':'Justfile; outputs/current_pipeline_verification.json','definition':'docs/project_definition.md; docs/system_diagram.md','data':'docs/data_dictionary.md; outputs/data_audit.json','evaluation':'docs/baseline_report.md; outputs/validation_*','eda':'outputs/eda_*.png and overview CSVs','first_pass_system':'src/talentroute/models.py, decision.py, evaluation.py; outputs/validation_decision_metrics.csv'}}
    (ROOT/'outputs/intermediate_readiness.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in ['word_counts','rubric_evidence']},indent=2))

if __name__=='__main__':verify()
