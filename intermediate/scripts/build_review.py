"""Build an offline evidence interface from aggregate output files only."""
from pathlib import Path
import csv
import html
import json
import re
import shutil
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs'; DEST=ROOT/'review'; UI=Path(__file__).parent/'review_ui'
DEST.mkdir(exist_ok=True)
# Figures have one canonical location in outputs; avoid duplicate asset copies.
if (DEST/'assets').exists():shutil.rmtree(DEST/'assets')

def rows(name):
    return json.loads(pd.read_csv(OUT/name).to_json(orient='records'))

sources={'policies':'validation_decision_metrics.csv','budgets':'validation_sensitivity.csv',
    'models':'revision/model_comparison.csv','intervals':'revision/forest_minus_hgb_intervals.csv',
    'layers':'revision/layer_quota_sensitivity.csv','jaccard':'revision/layer_selected_jaccard.csv',
    'breakEven':'revision/action_break_even.csv','ties':'revision/tie_sensitivity.csv',
    'profiles':'revision/warning_outcome_profiles.csv','ladder':'diagnostics/train_validation_metrics.csv',
    'shuffled':'diagnostics/shuffled_training_labels.csv','permutation':'diagnostics/grouped_permutation.csv'}
data={key:rows(name) for key,name in sources.items()}
frame=pd.read_csv(ROOT/'data/processed/enrolments.csv');frame=frame[frame.split.isin(['train','validation'])]
audit=json.loads((OUT/'data_audit.json').read_text(encoding='utf-8'))
data['segmentTradeoffs']=rows('development_segment_tradeoffs.csv')
data['developmentEvidence']=json.loads((OUT/'development_evidence.json').read_text())
data['quality']={'development_rows':len(frame),'duplicate_keys':int(frame.duplicated(['code_module','code_presentation','id_student']).sum()),'missing_early_score_n':int(frame.score_mean.isna().sum()),'audit':audit}
val=frame[frame.split=='validation'];data['outcomeCounts']={'adverse':int((val.target!='Success').sum()),'fail':int((val.target=='Fail').sum()),'withdrawn':int((val.target=='Withdrawn').sum())}
data['blendInterval']=json.loads((OUT/'validation_paired_interval.json').read_text(encoding='utf-8'))
data['baselineInterval']=json.loads((OUT/'diagnostics/classifier_minus_rule.json').read_text(encoding='utf-8'))
verification=ROOT/'evidence/platform-validation-2026-10-31/linux_verification.json'
data['linuxVerified']=verification.exists() and json.loads(verification.read_text(encoding='utf-8')).get('pipeline_exit_code')==0
payload=json.dumps(data,ensure_ascii=False).replace('<','\\u003c')
(DEST/'index.html').write_text((UI/'index.html').read_text(encoding='utf-8').replace('__DATA__',payload).replace('LINUX EXECUTION UNVERIFIED','PRIOR UBUNTU VM RUN · CURRENT RESULTS LOCAL' if data['linuxVerified'] else 'LINUX EXECUTION UNVERIFIED'),encoding='utf-8')
for name in ['review.css','review.js']:shutil.copy2(UI/name,DEST/name)

def readable_report(text):
    """Render this project's restricted Markdown subset without a network dependency."""
    parts=[];fenced=False;block=[]
    for line in text.splitlines():
        if line.startswith('```'):
            if fenced:
                records=list(csv.reader(block))
                if records:
                    parts.append('<div class="scroll"><table><thead><tr>'+''.join('<th scope="col">'+html.escape(c)+'</th>' for c in records[0])+'</tr></thead><tbody>')
                    parts.extend('<tr>'+''.join('<td>'+html.escape(c)+'</td>' for c in row)+'</tr>' for row in records[1:])
                    parts.append('</tbody></table></div>')
                block=[]
            fenced=not fenced;continue
        if fenced:block.append(line);continue
        image=re.fullmatch(r'!\[(.*?)\]\((.*?)\)',line)
        if image:parts.append(f'<figure><img src="{html.escape(image[2],quote=True)}" alt="{html.escape(image[1],quote=True)}"></figure>');continue
        if line.startswith('#'):
            count=len(line)-len(line.lstrip('#'));parts.append(f'<h{count}>'+html.escape(line[count:].strip())+f'</h{count}>')
        elif line.strip():parts.append('<p>'+html.escape(line)+'</p>')
    return '\n'.join(parts)

report=readable_report((ROOT/'docs/baseline_report.md').read_text(encoding='utf-8'))
(DEST/'report.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TalentRoute · Intermediate report</title><link rel="stylesheet" href="review.css"><body><main class="report-body"><a href="index.html">← Back to TalentRoute</a>'+report+'<p><a href="../docs/baseline_report.md" download>Download canonical Markdown report</a></p></main></body></html>',encoding='utf-8')
print('Built offline TalentRoute interface and readable report from aggregate evidence.')

from build_decision_room import build as build_decision_room
build_decision_room()
