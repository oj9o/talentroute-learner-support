"""Concise evidence report and decision-relevant figures from computed CSV files."""

from dataclasses import asdict
import os
from .data import ROOT, config
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.cache/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from .decision import Policy
from .models import FEATURES

def table(frame, columns=None, digits=3):
    """Small Markdown table without another runtime dependency."""
    frame = frame[columns] if columns else frame
    def fmt(value):
        if pd.isna(value):
            return '—'
        if isinstance(value, (float, np.floating)):
            return f'{value:.{digits}f}'
        return str(value).replace('|', '/')
    lines = ['| ' + ' | '.join(frame.columns) + ' |', '| ' + ' | '.join(['---'] * len(frame.columns)) + ' |']
    lines.extend('| ' + ' | '.join(fmt(v) for v in row) + ' |' for row in frame.itertuples(index=False, name=None))
    return '\n'.join(lines)


def eda():
    data = pd.read_csv(ROOT / 'data/processed/development.csv')
    rows = []
    for (period, module), group in data.groupby(['code_presentation', 'code_module']):
        rows.append({'presentation': period, 'module': module, 'n': len(group),
                     'students': group.id_student.nunique(), 'adverse_rate': group.target.ne('Success').mean(),
                     'assessment_missing_rate': group.score_mean.isna().mean(),
                     'no_clicks_rate': group.clicks.eq(0).mean()})
    pd.DataFrame(rows).to_csv(ROOT / 'outputs/course_observability.csv', index=False)
    pd.DataFrame({'feature': FEATURES, 'missing_n': data[FEATURES].isna().sum().values}).to_csv(ROOT / 'outputs/missingness.csv', index=False)
    parameters = {**asdict(Policy()), 'cutoff_day': config()['cutoff_day'],
                  'score_delay_days_assumed': config()['score_delay_days'],
                  'original_precision_loss_margin': .02}
    pd.DataFrame([parameters]).to_csv(ROOT / 'outputs/parameters.csv', index=False)
    folder = ROOT / 'outputs/figures'
    folder.mkdir(exist_ok=True)
    observability = pd.DataFrame(rows)
    for metric, title in [('assessment_missing_rate', 'Early-score availability differs by course and cohort'),
                          ('adverse_rate', 'Observed outcome prevalence differs by course and cohort')]:
        matrix = observability.pivot(index='module', columns='presentation', values=metric)
        ax = (matrix * 100).plot.bar(figsize=(8, 4), color=['#126c69', '#c77a35'])
        ax.set(title=title, ylabel='Cases (%)', xlabel='Course')
        ax.figure.tight_layout()
        ax.figure.savefig(folder / (metric + '.png'), dpi=160)
        plt.close(ax.figure)



def budget_figure():
    (ROOT / 'outputs/figures').mkdir(exist_ok=True)
    data = pd.read_csv(ROOT / 'outputs/sensitivity.csv')
    subset = data[(data.protocol == 'identity_disjoint') & (data.parameter == 'minutes_per_100')]
    fig, ax = plt.subplots(figsize=(8, 4))
    for route, color, style in [('classifier', '#355c9b', '-'), ('rule', '#6b788a', ':'), ('anomaly', '#8056a6', '--')]:
        rows = subset[subset.route == route]
        ax.plot(rows.value, rows.coverage * 100, style, marker='o', color=color, label=route)
    ax.set(title='How coverage changes with staff time', xlabel='Staff minutes per 100 enrolment cases',
           ylabel='Observed adverse outcomes contacted (%)')
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(ROOT / 'outputs/figures/budget_curve.png', dpi=160, bbox_inches='tight')
    plt.close(fig)


def run():
    from .final_report import run as generate_final_report
    generate_final_report()
