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
