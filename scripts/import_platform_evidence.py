"""Import checksum-verified public CI evidence without replacing canonical metrics."""
import argparse,hashlib,json,subprocess,zipfile,re
from pathlib import Path
import pandas as pd
from talentroute.data import ROOT
from talentroute.final_workflow import load_frozen

p=argparse.ArgumentParser();p.add_argument('archive');p.add_argument('repository');args=p.parse_args()
archive=Path(args.archive);expected='4e57af7a11c96a92fe663510fe04faab6d08f68a66dda141f3cb4264b6bf15ca'
assert hashlib.sha256(archive.read_bytes()).hexdigest()==expected,'CI artifact digest differs from GitHub display'
commit='dfa1b8eec395708b6ee22a8e26ac7ea3fd6f9e89';repo=Path(args.repository)
_,freeze=load_frozen();parts=[]
for path in sorted((ROOT/'src').rglob('*.py'))+[ROOT/'configs/policy.json']:
    rel=str(path.relative_to(ROOT));blob=subprocess.check_output(['git','-C',str(repo),'show',commit+':'+rel])
    parts.append(rel+hashlib.sha256(blob).hexdigest())
source_hash=hashlib.sha256(''.join(parts).encode()).hexdigest()
assert source_hash==freeze['implementation_sha256'],'Tested analytical code differs from the canonical release'
target=ROOT/'evidence/linux-container-2026-11-01';target.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(archive) as z:
    assert set(z.namelist())=={'container_verification.json','test_metrics.csv','requirements_check.json','runtime.json'}
    for name in z.namelist(): (target/name).write_bytes(z.read(name))
raw=json.loads((target/'container_verification.json').read_text());assert raw['container']=='python:3.14-slim'
excerpt=(target/'pytest-log-excerpt.txt').read_text();assert re.search(r'24 passed',excerpt)
receipt={'run_url':'https://github.com/oj9o/talentroute-learner-support/actions/runs/41237286645',
    'tested_commit':commit,'status':'success','artifact_sha256':expected,'implementation_sha256':source_hash,
    'container':raw['container'],'platform':raw['platform'],'python':raw['python'],'tests_passed':24,
    'tests_skipped':0,'pipeline_seconds':raw['runtime']['elapsed_seconds'],
    'scope':'Same analytical src/config as canonical Mac freeze. Later report/presentation changes are separate.',
    'raw_checks_note':'The archived requirements file predates external CI attestation; its static unverified label is retained verbatim.'}
(target/'attestation.json').write_text(json.dumps(receipt,indent=2));(ROOT/'outputs/final/platform_evidence.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps(receipt,indent=2))
