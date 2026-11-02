"""Verify interpretation-only changes without fitting or scoring saved models."""
from pathlib import Path
import datetime
import hashlib
import json
import platform
import re
import subprocess
import sys
from talentroute.data import ROOT


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protected=[ROOT/'data/processed/enrolments.csv',*sorted((ROOT/'outputs').glob('validation_*.csv')),
        *sorted((ROOT/'outputs/revision').glob('*.csv')),
        *sorted((ROOT/'outputs').glob('*.joblib')),ROOT/'outputs/development_selection.json']
    before={str(p.relative_to(ROOT)):digest(p) for p in protected}
    commands=[['-m','talentroute','report'],['-m','talentroute','eda'],
        ['scripts/build_review.py'],['scripts/verify_intermediate_release.py'],['-m','pytest','-q']]
    stages=[]
    for args in commands:
        result=subprocess.run([sys.executable,*args],cwd=ROOT,capture_output=True,text=True)
        print(result.stdout,end='');print(result.stderr,end='',file=sys.stderr)
        stages.append({'command':['python',*args],'exit_code':result.returncode})
        if result.returncode:raise SystemExit(result.returncode)
        if args==['-m','pytest','-q']:
            passed=re.search(r'(\d+) passed',result.stdout)
            if not passed:raise RuntimeError('Missing pytest success count')
            count=int(passed.group(1))
    assert all(digest(ROOT/path)==sha for path,sha in before.items()),'Protected fitted artifacts changed'
    source=[*sorted((ROOT/'src').rglob('*.py')),*sorted((ROOT/'scripts').rglob('*.py')),
        *sorted((ROOT/'scripts/review_ui').glob('*')),*sorted((ROOT/'tests').glob('*.py')),
        ROOT/'pyproject.toml',ROOT/'uv.lock',ROOT/'Justfile']
    record={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'python':platform.python_version(),'platform':platform.platform(),'stages':stages,
        'tests_passed':count,'protected_artifacts_unchanged':True,'protected_sha256':before,
        'source_sha256':{str(p.relative_to(ROOT)):digest(p) for p in source if p.is_file()},
        'new_model_fitting':False,'final_test_scored':False,
        'scope':'Interpretation, EDA, interface and regression checks against saved development evidence; not a new full analytical pipeline run'}
    (ROOT/'outputs/revision_verification.json').write_text(json.dumps(record,indent=2))
    print('Verified interpretation-only revision; protected artifacts unchanged.')


if __name__=='__main__':main()
