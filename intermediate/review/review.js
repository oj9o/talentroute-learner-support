'use strict';
const DATA=JSON.parse(document.getElementById('project-data').textContent);
let outcome='adverse',budget=300,opener=null;
const $=id=>document.getElementById(id);
const esc=s=>String(s??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pct=v=>(v*100).toFixed(2)+'%';
const integer=v=>Math.round(v).toLocaleString('en-US');
const names={business_rule:'Model-free rule',classifier_only:'Classifier-only reference',coupled_fixed_020:'Classifier + anomaly blend',logistic:'Logistic regression',tree:'Decision tree',forest:'Random forest',hgb_15_10:'Historical boosting',module_logistic_hybrid:'Module logistic hybrid'};
const outcomes={adverse:'Fail + Withdrawn',fail:'Fail',withdrawn:'Withdrawn'};
const metric=()=>outcome+'_coverage';
function table(headers,rows,caption){return `<table><caption>${esc(caption)}</caption><thead><tr>${headers.map(h=>`<th scope="col">${esc(h)}</th>`).join('')}</tr></thead><tbody>`+rows.map(row=>'<tr>'+row.map(v=>`<td>${esc(v)}</td>`).join('')+'</tr>').join('')+'</tbody></table>';}
function bar(label,value,color='var(--ref)',percentage=true,detail='',benchmark=null){
 const formatted=percentage?pct(value):value.toFixed(4);
 return `<div><div class="bar-label"><span>${esc(label)}${detail?`<small>${esc(detail)}</small>`:''}</span><b>${formatted}</b></div><div class="track" aria-hidden="true"><div class="fill" style="width:${Math.max(0,Math.min(100,value*100))}%;background:${color}"></div>${benchmark===null?'':`<span class="benchmark" style="left:${benchmark*100}%" title="Random-ranking prevalence benchmark">▴</span>`}</div></div>`;
}
function showView(name){document.querySelectorAll('.view').forEach(x=>x.hidden=x.id!==name);document.querySelectorAll('[data-view]').forEach(b=>{b.classList.toggle('active',b.dataset.view===name);b.setAttribute('aria-current',b.dataset.view===name?'page':'false');});window.scrollTo({top:0,behavior:'instant'});}
function renderHome(){
 const reference=DATA.policies.find(r=>r.policy==='classifier_only');
 const blend=DATA.policies.find(r=>r.policy==='coupled_selected');
 $('homeCoverage').textContent=pct(reference.adverse_coverage);
 $('homeCases').textContent=`${integer(reference.adverse_coverage*DATA.outcomeCounts.adverse)} of ${integer(DATA.outcomeCounts.adverse)} later adverse cases.`;
 $('homeExtra').textContent='+'+integer(DATA.baselineInterval.extra_adverse_cases_flagged)+' cases';
 $('homeDifference').textContent=`A ${(DATA.baselineInterval.coverage_difference*100).toFixed(2)} percentage-point coverage difference at the same staff effort.`;
 $('homeBlend').textContent=`${integer((blend.adverse_coverage-reference.adverse_coverage)*DATA.outcomeCounts.adverse)} additional adverse cases flagged by the selected blend.`;
 const ci=DATA.blendInterval.ci95, includesZero=ci[0]<=0&&ci[1]>=0;
 $('blendVerdict').textContent=includesZero?'The gain is inconclusive.':'Inspect the estimated difference.';
 $('blendInterpretation').textContent=`Exploratory paired interval: ${ci[0].toFixed(4)} to ${ci[1].toFixed(4)}. Review separate Fail and Withdrawn outcomes before choosing a policy.`;
 if(DATA.linuxVerified)$('runStatus').textContent='PRIOR UBUNTU VM RUN · Current results local · Development evidence';
}
function renderDecision(){
 const rows=DATA.budgets.filter(r=>r.assumption==='staff_minutes_per_100'&&r.value===budget&&['business_rule','classifier_only','coupled_fixed_020'].includes(r.policy));
 const reference=rows.find(r=>r.policy==='classifier_only');
 $('decisionTitle').textContent=`${outcomes[outcome]} cases reached at budget ${budget}`;
 $('policyBars').innerHTML=rows.map(r=>bar(names[r.policy],r[metric()],r.policy==='classifier_only'?'var(--ref)':r.policy==='business_rule'?'#738092':'var(--alt)',true,`${integer(r[metric()]*DATA.outcomeCounts[outcome])} of ${integer(DATA.outcomeCounts[outcome])} later cases`)).join('');
 $('mainCoverage').textContent=pct(reference[metric()]);
 $('coverageMeaning').textContent=`${integer(reference[metric()]*DATA.outcomeCounts[outcome])} of ${integer(DATA.outcomeCounts[outcome])} later ${outcomes[outcome]} cases reached.`;
 $('workload').innerHTML=`<div><b>${integer(reference.human_n)}</b><span>human reviews</span></div><div><b>${integer(reference.alert_n)}</b><span>alerts</span></div><div class="wide"><b>${integer(reference.staff_minutes)} min</b><span>staff effort used across ${integer(reference.n)} learners</span></div>`;
 const ties=DATA.ties.filter(r=>r.score==='business_rule');
 $('tieNote').textContent=budget===300?`The historical rule breaks ties by source order. Five seeded tie checks gave pooled coverage ${pct(Math.min(...ties.map(r=>r.adverse_coverage)))}–${pct(Math.max(...ties.map(r=>r.adverse_coverage)))} versus historical ${pct(DATA.policies.find(r=>r.policy==='business_rule').adverse_coverage)}. This separate diagnostic concerns pooled outcomes at budget 300.`:'Tie sensitivity was computed only at the reference budget of 300.';
}
function renderScenario(){
 const m=Number($('multiplier').value),cap=Number($('alertCap').value);
 const rows=DATA.breakEven.filter(r=>r.human_effectiveness_multiplier_assumed===m&&r.alert_cap_fraction===cap);
 $('scenarioTable').innerHTML=rows.length?table(['Reviews','Alerts','Minutes','Unused','Hypothetical units','Difference vs reference','Break-even multiplier','Mix'],rows.map(r=>[r.human_n,r.alert_n,r.staff_minutes,r.unused_minutes,r.observed_weighted_targeting_units_scenario.toFixed(1),(r.observed_weighted_targeting_units_scenario-r.reference_weighted_targeting_units_scenario).toFixed(1),r.break_even_status==='unique_positive'?r.break_even_multiplier_same_reference_effectiveness.toFixed(2):'No unique positive crossing',r.reference_operating_mix?'Reference mix':'Alternative mix']),'Hypothetical weighted targeting · fixed budget 300; pooled outcomes'):'<p>No feasible mixes for these settings.</p>';
}
function renderLayers(){
 const share=Number($('share').value),rows=DATA.layers.filter(r=>r.classifier_first_share===share);
 const lo=Math.min(...rows.map(r=>r[metric()])),hi=Math.max(...rows.map(r=>r[metric()]));
 const reference=DATA.policies.find(r=>r.policy==='classifier_only');
 $('layerTitle').textContent=`${outcomes[outcome]} · ${share*100}% classifier-first`;
 $('layerBars').innerHTML=`<div><div class="bar-label"><span>Range over tested orders/seeds</span><b>${lo===hi?pct(lo):pct(lo)+'–'+pct(hi)}</b></div><div class="range-track" aria-hidden="true"><div class="range-line" style="left:${lo*100}%;width:${(hi-lo)*100}%"></div><i class="range-dot" style="left:${lo*100}%"></i><i class="range-dot" style="left:${hi*100}%"></i></div></div>`+bar('Classifier-only reference',reference[metric()]);
 const missed=rows.map(r=>outcome==='adverse'?r.escaped_adverse_n:Math.round(DATA.outcomeCounts[outcome]*(1-r[metric()])));
 const low=Math.min(...missed),high=Math.max(...missed);$('escaped').textContent=low===high?integer(low):`${integer(low)}–${integer(high)}`;
 $('escapeCaption').textContent=`Same total quota: ${integer(rows[0].flagged_n)} flags out of ${integer(reference.n)} learners. Outcome denominator: ${integer(DATA.outcomeCounts[outcome])}. Range scale: 0–100%.`;
}
function renderModels(){
 $('modelTitle').textContent=`${outcomes[outcome]} PR-AUC`;
 $('modelBars').innerHTML=DATA.models.map(r=>bar(names[r.model],r[outcome+'_pr_auc'],r.model==='hgb_15_10'?'var(--ref)':'var(--alt)',false,'',DATA.outcomeCounts[outcome]/DATA.policies[0].n)).join('');
 $('prevalence').textContent=`Random-ranking reference (prevalence): ${(DATA.outcomeCounts[outcome]/DATA.policies[0].n).toFixed(4)}. This is a benchmark, not a lower bound.`;
 const X=v=>180+(v+.05)/.1*530;
 let svg=`<desc>${DATA.intervals.map(r=>`${r.metric}: bootstrap mean ${r.difference_mean.toFixed(4)}, interval ${r.ci95_lower.toFixed(4)} to ${r.ci95_upper.toFixed(4)}`).join('; ')}</desc><line x1="${X(0)}" x2="${X(0)}" y1="10" y2="225" stroke="#8c9eab" stroke-dasharray="4 4"/>`;
 DATA.intervals.forEach((r,i)=>{const y=45+i*72,label=r.metric.replace('_pr_auc',''),color={adverse:'#637887',fail:'#b74e59',withdrawn:'#7756aa'}[label];svg+=`<text x="0" y="${y+5}" fill="#183342" font-size="15">${outcomes[label]}</text><line x1="${X(r.ci95_lower)}" x2="${X(r.ci95_upper)}" y1="${y}" y2="${y}" stroke="${color}" stroke-width="4"/><circle cx="${X(r.difference_mean)}" cy="${y}" r="5" fill="${color}"/><text x="${X(r.ci95_lower)}" y="${y+25}" font-size="12" fill="#526878">${r.ci95_lower.toFixed(4)} to ${r.ci95_upper.toFixed(4)}</text>`;});
 [-.05,0,.05].forEach(v=>svg+=`<text x="${X(v)}" y="250" text-anchor="middle" font-size="13" fill="#526878">${v.toFixed(2)}</text>`);
 svg+='<text x="445" y="279" text-anchor="middle" font-size="12" fill="#526878">PR-AUC difference · forest minus boosting</text>';$('intervalPlot').innerHTML=svg;
}
function renderResearch(){
 const ref=DATA.policies.find(r=>r.policy==='classifier_only').adverse_coverage;
 const mixed=DATA.layers.filter(r=>r.classifier_first_share<1).map(r=>r.adverse_coverage);
 $('layerFinding').textContent=`Tested mixed-quota pooled coverage: ${pct(Math.min(...mixed))}–${pct(Math.max(...mixed))}; classifier-only ${pct(ref)}. These results concern these quota designs, not layered detection generally.`;
 const scores=DATA.profiles.filter(r=>r.flagged&&r.feature==='score_mean');
 $('profileSummary').innerHTML=table(['Outcome','Observed scores','Median score'],scores.map(r=>[r.outcome,`${r.observed_n} / ${r.n}`,Number(r.median).toFixed(1)]),'Early scores within historical flagged groups');
 const specialist=DATA.models.find(r=>r.model==='module_logistic_hybrid'),global=DATA.models.find(r=>r.model==='logistic');
 $('specialistSummary').textContent=`Pooled PR-AUC: global logistic ${global.adverse_pr_auc.toFixed(4)}, module hybrid ${specialist.adverse_pr_auc.toFixed(4)}. Best flexible global ensemble ${Math.max(...DATA.models.filter(r=>['forest','hgb_15_10'].includes(r.model)).map(r=>r.adverse_pr_auc)).toFixed(4)}. These are exploratory validation comparisons.`;
 const grouped={};DATA.jaccard.forEach(r=>(grouped[r.layer_a+' / '+r.layer_b]??=[]).push(r.jaccard));
 $('overlapTable').innerHTML=table(['Warning pair','Jaccard range'],Object.entries(grouped).map(([k,v])=>[k,Math.min(...v).toFixed(3)+'–'+Math.max(...v).toFixed(3)]),'Selected-set overlap at equal quotas · diagnostic only');
 $('debugSummary').innerHTML=table(['Model','Split','Adverse PR-AUC','Log loss'],DATA.ladder.map(r=>[names[r.model],r.split,r.adverse_pr_auc.toFixed(4),r.log_loss.toFixed(4)]),'Training fit versus validation-selected performance')+`<p>Ten shuffled-training-label controls: validation ROC-AUC ${Math.min(...DATA.shuffled.map(r=>r.adverse_roc_auc)).toFixed(3)}–${Math.max(...DATA.shuffled.map(r=>r.adverse_roc_auc)).toFixed(3)}; random-ranking reference 0.5. A limited negative control cannot certify absence of leakage.</p>`;
 const perms={};DATA.permutation.forEach(r=>(perms[r.feature_group]??=[]).push(r.decrease));
 $('permutationTable').innerHTML=table(['Feature family','Mean decrease','Repeated range'],Object.entries(perms).map(([k,v])=>[k,(v.reduce((a,b)=>a+b,0)/v.length).toFixed(4),Math.min(...v).toFixed(4)+' to '+Math.max(...v).toFixed(4)]),'Predictive reliance · ROC-AUC decrease, not a causal effect');
}
function renderQuality(){
 const q=DATA.quality,a=q.audit;
 const answers=[['01','What does one row mean?','One student × module × presentation enrolment. A student may have more than one enrolment; those are not automatically duplicates.'],['02','Are there duplicates?',`${integer(q.duplicate_keys)} duplicate enrolment keys in ${integer(q.development_rows)} development rows. Earlier repeated-student records are purged across temporal partitions to prevent identity overlap.`],['03','What is missing, and why?',`${integer(q.missing_early_score_n)} development enrolments lack an observable early score. No score is not zero. The seven-day marking delay is an assumption, not an observed grading timestamp.`],['04','What was excluded?',`${integer(a.raw_enrolments)} raw → ${integer(a.eligible_enrolments)} eligible → ${integer(a.purged_earlier_repeat_enrolments)} earlier repeats removed. Retained: ${integer(a.eligible_enrolments-a.purged_earlier_repeat_enrolments)} = ${integer(a.split_counts.train)} train + ${integer(a.split_counts.validation)} validation + ${integer(a.split_counts.test)} reserved test. Counts are not test performance.`],['05','Has the process changed?','Module mix and assessment availability differ across presentations. These differences motivate sensitivity checks; they do not identify a process-change cause. Unseen modules and one validation period limit generalisation.']];
 $('qualityAnswers').innerHTML=answers.map(([n,h,p])=>`<article class="q"><span class="mini-label">DATA CHECK ${n}</span><h3>${h}</h3><p>${p}</p></article>`).join('');
 const figures=[['eda_01_outcomes','How do development outcome counts differ?'],['eda_02_missingness','Which features are missing at day 28?'],['eda_03_engagement','How does activity vary by later outcome?'],['eda_04_scores','How do observable early scores vary?'],['eda_05_change','First versus second fortnight activity'],['eda_06_modules','How does outcome mix vary across modules?'],['eda_07_observability','Which modules lack early assessment signals?'],['eda_08_inactivity','How does inactivity differ by later outcome?'],['eda_09_detector','Where do classifier risk and detector warnings disagree?'],['decision_frontier','What changes when staff capacity changes?']];
 $('figureGallery').innerHTML=figures.map(([f,title])=>`<figure><img loading="lazy" src="../outputs/${f}.png" alt="${title}"><figcaption>${title} · development evidence</figcaption></figure>`).join('');
}
const sources={baseline:['diagnostics/classifier_minus_rule.json','Classifier-only minus historical model-free rule. Same validation cohort and staff effort. Paired student-cluster interval is exploratory and conditional on validation selection.'],budget:['validation_sensitivity.csv','Computed budgets 150/300/600. No interpolation. Costs: review 30 minutes, alert two minutes. Review/alert mix and alert cap are assumptions.'],models:['revision/forest_minus_hgb_intervals.csv','2,000 paired student-cluster draws; unadjusted exploratory comparisons conditional on fitted models and validation selection.'],layers:['revision/layer_quota_sensitivity.csv','All 24 orders and three tie seeds at five classifier-first shares. Equal total flag quota; no claim about optimal action choice.'],scenario:['revision/action_break_even.csv','Observed adverse counts are weighted by a hypothetical relative effectiveness. Both candidate and reference use the same multiplier and seeded ordering. Changing the cap changes the constraint. No ROI or causal benefit is estimated.']};
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>showView(b.dataset.view));
document.querySelectorAll('[data-go]').forEach(b=>b.onclick=()=>showView(b.dataset.go));
document.querySelector('.brand').onclick=e=>{e.preventDefault();showView('overview');};
document.querySelectorAll('[data-outcome]').forEach(b=>b.onclick=()=>{outcome=b.dataset.outcome;document.querySelectorAll('[data-outcome]').forEach(x=>{x.classList.toggle('active',x.dataset.outcome===outcome);x.setAttribute('aria-pressed',String(x.dataset.outcome===outcome));});renderDecision();renderLayers();renderModels();});
document.querySelectorAll('[data-budget]').forEach(b=>b.onclick=()=>{budget=Number(b.dataset.budget);document.querySelectorAll('[data-budget]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',String(x===b));});renderDecision();});
document.querySelectorAll('[data-source]').forEach(b=>b.onclick=()=>{opener=b;const [file,explanation]=sources[b.dataset.source];$('evidenceBody').innerHTML=`<p class="source-name">outputs/${esc(file)}</p><p>${esc(explanation)}</p><p class="muted">Development evidence. Separate final evaluation already recorded; no final-test tuning in these investigations.</p>`;$('evidence').showModal();});
$('closeEvidence').onclick=()=>$('evidence').close();$('evidence').addEventListener('close',()=>opener?.focus());
$('share').onchange=renderLayers;$('multiplier').onchange=renderScenario;$('alertCap').onchange=renderScenario;
document.querySelectorAll('[data-outcome]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.outcome===outcome)));
document.querySelectorAll('[data-budget]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.budget)===budget)));
renderHome();renderDecision();renderModels();renderLayers();renderResearch();renderQuality();renderScenario();
