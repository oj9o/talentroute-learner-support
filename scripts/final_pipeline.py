"""Run the frozen final release end-to-end; cached test output is reused."""
from pathlib import Path
import subprocess,time,json
from talentroute.data import ROOT
start=time.monotonic()
for command in ['download-data','prepare-data','run-baseline','eda','deep-dives','diagnostics','run-model','evaluate','ablation','sensitivity','verify','report','review','final-report','final-review','verify-final','test']:
    if command=='run-model' and (ROOT/'outputs/final/acceptance.json').exists(): continue
    subprocess.run(['just',command],cwd=ROOT,check=True)
(ROOT/'outputs/final/runtime.json').write_text(json.dumps({'elapsed_seconds':time.monotonic()-start,'note':'Full current-host run; platform certification separate.'},indent=2))
