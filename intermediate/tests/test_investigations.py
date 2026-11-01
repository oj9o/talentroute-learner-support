"""Guard against test-row inclusion in exploratory development diagnostics."""
import importlib.util
from pathlib import Path
import pandas as pd
spec=importlib.util.spec_from_file_location('debug_investigations',Path(__file__).parents[1]/'scripts/debug_investigations.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
def test_development_loader_excludes_reserved_and_unknown_rows(tmp_path):
    path=tmp_path/'data.csv'
    pd.DataFrame({'split':['train','validation','test','unexpected'],'target':['Fail','Success','SECRET','SECRET'],'signal':[1,2,999,999]}).to_csv(path,index=False)
    result=module.development_data(path)
    assert result.signal.tolist()==[1,2]
    assert 'SECRET' not in set(result.target)


def test_investigation_builder_recreates_review_directory_after_clean(tmp_path,monkeypatch):
    import runpy
    import shutil
    import talentroute.data as data
    original=data.ROOT
    if not (original/'outputs/investigations/manifest.json').exists():
        import pytest
        pytest.skip('Run just investigations before testing the clean-state builder')
    dest=tmp_path/'outputs/investigations';dest.mkdir(parents=True)
    for name in ['manifest.json','learning_curve.csv','single_feature.csv','period_shift.csv']:
        shutil.copy2(original/'outputs/investigations'/name,dest/name)
    shutil.copy2(original/'outputs/validation_paired_interval.json',tmp_path/'outputs/validation_paired_interval.json')
    assert not (tmp_path/'review').exists()
    monkeypatch.setattr(data,'ROOT',tmp_path)
    runpy.run_path(str(original/'scripts/build_investigations.py'),run_name='__main__')
    assert (tmp_path/'review/investigations.html').is_file()
