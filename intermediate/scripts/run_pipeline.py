"""Run reproducible stages and record the actual environment, tests and timings."""
from pathlib import Path
import datetime
import json
import platform
import re
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs';OUT.mkdir(exist_ok=True)
start=time.monotonic();stages=[]
commands=[['just','download-data'],['just','prepare-data'],['just','eda'],['just','run-baseline'],
    ['uv','run','python','-m','talentroute','stability'],
    ['uv','run','python','-m','talentroute','data-sensitivity'],['just','revision'],
    ['just','diagnostics'],['just','investigations'],['just','eda'],['uv','run','python','scripts/verify_submission.py'],['just','report'],['just','review'],['just','readiness'],['just','test']]
record={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'platform':platform.platform(),'python':platform.python_version(),
    'pipeline_exit_code':None,'final_test_scored_by_this_pipeline':False,'separate_final_evaluation_already_observed':True,'stages':stages,
    'scope':'Current local pipeline execution; operating system measured, VM/container type not inferred'}


def save():
    record['elapsed_seconds']=round(time.monotonic()-start,2)
    (OUT/'current_pipeline_verification.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    if platform.system()=='Linux':
        (OUT/'linux_verification.json').write_text(json.dumps(record,indent=2),encoding='utf-8')


def run(command):
    begun=time.monotonic();print('Stage: '+' '.join(command),flush=True)
    result=subprocess.run(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    print(result.stdout,end='',flush=True)
    stages.append({'command':command,'exit_code':result.returncode,'elapsed_seconds':round(time.monotonic()-begun,2)})
    if result.returncode:raise subprocess.CalledProcessError(result.returncode,command)
    if command==['just','test']:
        passed=re.search(r'(\d+) passed',result.stdout)
        if passed:record['tests_passed']=int(passed.group(1))


try:
    for command in commands:run(command)
    record['pipeline_exit_code']=0
    record['data_access']=json.loads((ROOT/'data/raw/manifest.json').read_text(encoding='utf-8')).get('access','official archive extraction')
    save()
    # Refresh explanatory artifacts after verification exists; no model is refitted.
    run(['just','report']);run(['just','review']);run(['just','test']);save()
except subprocess.CalledProcessError as error:
    record['pipeline_exit_code']=error.returncode;save();sys.exit(error.returncode)
