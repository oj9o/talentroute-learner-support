"""Offline final evidence page, generated solely from aggregate artifacts."""
from pathlib import Path
import html,json,re
import pandas as pd
from talentroute.data import ROOT
from talentroute.final_workflow import final_app

out=ROOT/'outputs/final';dest=ROOT/'review';dest.mkdir(exist_ok=True)
scenarios=[]
for budget in [150,300,600]:scenarios.append(final_app(budget))
(out/'artifact_scenarios.json').write_text(json.dumps(scenarios,indent=2))
metric=pd.read_csv(out/'test_metrics.csv').set_index('policy');p=metric.loc['proposed_connected'];b=metric.loc['business_rule'];c=metric.loc['classifier_only']
gate=json.loads((out/'acceptance.json').read_text())

def inline(s):
 s=html.escape(s);return re.sub(r'\*\*(.*?)\*\*',r'<strong>\1</strong>',s)
def render(text):
 lines=text.splitlines();parts=[];i=0
 while i<len(lines):
  line=lines[i]
  if line.startswith('```'):
   block=[];i+=1
   while i<len(lines) and not lines[i].startswith('```'):block.append(lines[i]);i+=1
   parts.append('<div class="flow">OULAD → decision-time features → classifier ensemble + engagement detector → budgeted review/alert queue → observed-outcome evaluation</div>')
  elif line.startswith('|'):
   records=[]
   while i<len(lines) and lines[i].startswith('|'):
    vals=[v.strip() for v in lines[i].strip('|').split('|')]
    if not all(re.fullmatch(r'[-: ]+',v) for v in vals):records.append(vals)
    i+=1
   parts.append('<div class="scroll"><table><thead><tr>'+''.join('<th>'+inline(v)+'</th>' for v in records[0])+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+inline(v)+'</td>' for v in row)+'</tr>' for row in records[1:])+'</tbody></table></div>');continue
  elif line.startswith('#'):
   level=len(line)-len(line.lstrip('#'));parts.append(f'<h{level}>'+inline(line[level:].strip())+f'</h{level}>')
  elif re.fullmatch(r'!\[.*?\]\(.*?\)',line):
   m=re.fullmatch(r'!\[(.*?)\]\((.*?)\)',line);parts.append('<figure><img src="'+html.escape(m[2],quote=True)+'" alt="'+html.escape(m[1],quote=True)+'"></figure>')
  elif line.strip():parts.append('<p>'+inline(line)+'</p>')
  i+=1
 return '\n'.join(parts)

style='''body{margin:0;background:#f5f7f8;color:#172d35;font:16px/1.65 -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif}main{max-width:1080px;margin:auto;padding:40px 30px}header{border-top:5px solid #196e77;padding:24px 0}h1{font-size:40px;line-height:1.15;max-width:850px}h2{margin-top:46px;border-top:1px solid #cedadd;padding-top:24px;font-size:24px}p{max-width:900px}.eyebrow{font-size:12px;letter-spacing:2px;color:#196e77;font-weight:700}.summary{display:flex;gap:30px;border-block:1px solid #cedadd;padding:24px 0;margin:26px 0}.summary strong{display:block;font-size:32px}.notice{border-left:4px solid #986315;padding:12px 20px;background:#fff9eb}.flow{border-block:1px solid #cedadd;padding:22px 0;font-weight:600}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-size:13px;margin:22px 0;background:white}td,th{text-align:left;padding:10px;border-bottom:1px solid #dbe3e5;white-space:nowrap}th{color:#196e77}img{width:100%;max-width:960px}button,a{color:#196e77}button{background:white;border:1px solid #196e77;padding:10px 24px;cursor:pointer;margin-right:8px}button[aria-pressed=true]{background:#196e77;color:white}#scenario{padding:18px 0}footer{margin-top:50px;border-top:1px solid #cedadd;padding:20px 0;font-size:13px}@media(max-width:650px){main{padding:24px 16px}h1{font-size:30px}.summary{flex-wrap:wrap}}'''
head=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TalentRoute | Final evidence</title><style>{style}</style><main><header><div class="eyebrow">EDUCATIONAL CONSULTANCY · FINAL EVIDENCE</div><h1>Who should receive learner support first?</h1><p>A staff-time-constrained targeting tool for consulting teams serving universities and learning providers. It evaluates actual learner outcomes; it does not claim that contact prevents failure.</p></header><div class="summary"><div><strong>{p.adverse_coverage:.2%}</strong>Connected candidate coverage</div><div><strong>{b.adverse_coverage:.2%}</strong>Simple-rule coverage</div><div><strong>{c.adverse_coverage:.2%}</strong>Original-classifier coverage</div></div><p>Held-out cohort: {int(p.n):,} enrolments. All three use {int(p.staff_minutes):,} staff minutes and {int(p.flagged_n):,} contacts.</p><div class="notice"><strong>Acceptance: {'passed' if gate['accepted'] else 'not passed'}.</strong> The candidate improves on the simple rule and original classifier, but the detector's incremental improvement over the ensemble alone remains uncertain. Retain the simpler reference pending independent evidence.</div><section class="notice"><strong>Model investigation workspace</strong><p>Follow the learning-curve, single-feature and period-difference investigations, with exact development results and interpretation limits.</p><a href="investigations.html">Open the evidence workspace →</a></section><h2>Explore the workload</h2><p>Validation-cohort scenario, not held-out performance. Change staff minutes per 100 learners. Recommendations use the frozen experimental system.</p><div id="buttons">'''+''.join(f'<button data-budget="{int(s["budget_per_100"])}" aria-pressed="false">{int(s["budget_per_100"])} minutes</button>' for s in scenarios)+'''</div><div id="scenario" aria-live="polite"></div><p><a href="../docs/final_report.md">Canonical Markdown report</a> · <a href="../outputs/final/test_metrics.csv">Test decision metrics</a> · <a href="../outputs/final/test_paired_intervals.csv">Paired uncertainty</a> · <a href="../outputs/final/freeze.json">Pre-test specification</a></p>'''
script='''<script>const scenarios=SCENARIOS;function select(b){const s=scenarios.find(x=>x.budget_per_100===b);document.querySelector('#scenario').textContent=`${s.human_reviews} human reviews · ${s.alerts} alerts · ${s.no_action} no action. Staff effort: ${s.staff_minutes} / ${s.available_minutes} available minutes.`;document.querySelectorAll('button[data-budget]').forEach(x=>x.setAttribute('aria-pressed',String(Number(x.dataset.budget)===b)))}document.querySelectorAll('button[data-budget]').forEach(x=>x.addEventListener('click',()=>select(Number(x.dataset.budget))));select(300);</script>'''.replace('SCENARIOS',json.dumps(scenarios))
(dest/'final.html').write_text(head+render((ROOT/'docs/final_report.md').read_text())+'<footer>Offline evidence page. Generated from saved aggregate outputs. Linux-container verification and the canonical local results are documented separately in the linked report and evidence files.</footer>'+script+'</main></html>')
print('Built review/final.html')
