"""Small command dispatcher; the pipeline executes each stage once."""

import argparse
import shutil
from time import perf_counter
import subprocess
import sys
import pandas as pd
from . import availability_audit, analyses, calendar_audit, data, evaluation, models, report


def test():
    subprocess.run([sys.executable, '-m', 'pytest', '-q'], cwd=data.ROOT, check=True)


def clean():
    """Delete generated artifacts only; preserve raw data and authored documentation; the generated report is removed."""
    for directory in ['outputs', 'data/processed']:
        shutil.rmtree(data.ROOT / directory, ignore_errors=True)
        (data.ROOT / directory).mkdir(parents=True, exist_ok=True)
    (data.ROOT / 'docs/final_report.md').unlink(missing_ok=True)


STAGES = {
    'download-data': data.download,
    'calendar-audit': calendar_audit.run,
    'prepare-data': data.prepare,
    'eda': report.eda,
    'fit-models': models.fit_development,
    'run-baseline': evaluation.baselines,
    'evaluate': evaluation.evaluate,
    'selection-stability': evaluation.selection_stability,
    'sensitivity': evaluation.sensitivity,
    'calibration': evaluation.calibration_diagnostics,
    'deep-dives': analyses.run,
    'availability-audit': availability_audit.run,
    'report': report.run,
    'test': test,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=[*STAGES, 'run-model', 'pipeline', 'ablation', 'clean'])
    command = parser.parse_args().command
    (data.ROOT / 'outputs').mkdir(exist_ok=True)
    if command == 'pipeline':
        times = []
        for name, function in STAGES.items():
            start = perf_counter()
            print(f'Running {name}', flush=True)
            function()
            times.append({'stage': name, 'seconds': perf_counter() - start})
        pd.DataFrame(times).to_csv(data.ROOT / 'outputs/runtime.csv', index=False)
        print(f'Pipeline complete: {sum(row["seconds"] for row in times):.1f} seconds', flush=True)
    elif command == 'clean':
        clean()
    elif command == 'run-model':
        models.fit_development()
        evaluation.evaluate()
    elif command == 'ablation':
        evaluation.evaluate()
        report.ablation_figure()
    else:
        STAGES[command]()


if __name__ == '__main__':
    main()
