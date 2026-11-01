'use strict';
const evidence=JSON.parse(document.getElementById('room-evidence').textContent);
const $=id=>document.getElementById(id);
const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const percent=x=>(x*100).toFixed(2)+'%';
const number=x=>Math.round(x).toLocaleString('en-US');
const labels={logistic:'Logistic regression',tree:'Decision Tree',forest:'Random Forest',hgb_15_10:'Histogram boosting',module_logistic_hybrid:'Module logistic hybrid',business_rule:'Model-free rule',classifier_only:'Classifier-only reference',coupled_selected:'Classifier + detector',coupled_fixed_020:'Classifier + detector'};
const cases={
 model:{label:'01 · CHOOSE A MODEL',title:'Would you switch to the highest-scoring model?',complaint:'“Random Forest has the highest pooled PR-AUC. Should we replace our classifier?”',context:'The comparison uses the same validation cohort. The reference was selected before the later model comparisons; all expanded comparisons are exploratory.',predictions:['The highest pooled PR-AUC is sufficient to switch.','I need outcome-specific results, uncertainty and workload results.'],tools:[['ranking','Compare model rankings'],['tradeoffs','Inspect uncertainty & outcome tradeoffs']],decisions:['Replace the reference because the point estimate is highest.','Keep the reference provisionally; investigate the outcome tradeoffs before a switch.'],supported:1,feedback:'The small pooled difference does not establish superiority. The exploratory intervals show a tradeoff between Fail and Withdrawn ranking, and the same-budget decision comparison also matters. Keep the current reference provisionally rather than selecting a new final model from these results.'},
 detector:{label:'02 · CHALLENGE THE ADDED LAYER',title:'Does unusual engagement improve support targeting?',complaint:'“The engagement detector finds unusual activity. Does that mean the combined system deserves to be deployed?”',context:'Classification and outlier detection are both implemented and connected to the ranking policy. The question here is whether the added detector earns its complexity.',predictions:['A separate detector must improve the decision.','The coupled policy needs to beat classifier-only at the same effort, with uncertainty considered.'],tools:[['targeting','Compare same-budget targeting'],['tradeoffs','Inspect interval & outcome tradeoffs']],decisions:['Deploy the blend because it flags a few more adverse cases.','Retain classifier-only as the provisional reference while the added benefit is unresolved.'],supported:1,feedback:'The added coverage is small and the paired interval includes zero. Detection of unusual engagement is not verified evidence of need or treatment benefit. Both components remain implemented and evaluated; deployment superiority is unconfirmed.'},
 capacity:{label:'03 · PLAN THE TEAM’S WORKLOAD',title:'What changes when support capacity grows?',complaint:'“We could allocate more staff time. How many reviews and alerts would that require, and what proportion of later adverse cases would be reached?”',context:'Choose one of three computed budget scenarios. Review and alert effort are planning assumptions. The same validation cohort is used throughout.',predictions:['More staff time should reach more later cases, with a workload and relevance tradeoff.','Doubling staff time should double coverage and guarantee improved outcomes.'],tools:[['coverage','Explore targeting & precision'],['workload','Inspect staff effort & action counts']],decisions:['Choose the largest budget and promise fewer failures.','Choose a feasible staffing scenario after checking coverage, precision and workload; evaluate real intervention effects separately.'],supported:1,feedback:'Capacity changes who can be contacted, but targeting coverage is not prevented failure. The decision needs an affordable workload and an acceptable contact burden. OULAD does not measure the causal effect of reviews or alerts.'}
};
let active='model',budget=300,selectedTool='',session={};
function state(){return session[active]||(session[active]={prediction:null,reason:'',tools:[],recommendation:null});}
function options(items,name){return items.map((text,i)=>`<label class="option"><input type="radio" name="${name}" value="${i}" required><span>${escape(text)}</span></label>`).join('');}
function source(key){return `<p class="source">Source: <a href="${evidence.sources[key]}" download>${escape(evidence.sources[key].replace('../',''))} ↓</a></p>`;}
function bar(label,value,color,detail,unit='coverage'){
 const display=unit==='ap'?value.toFixed(4):percent(value);
 return `<div class="bar tip" tabindex="0" title="${escape(label+': '+display+'. '+detail)}"><span>${escape(label)}</span><strong>${display}</strong><div class="track" aria-hidden="true"><div class="fill" style="width:${Math.max(0,Math.min(100,value*100))}%;background:${color}"></div></div></div>`;
}
function table(headers,rows){return '<div class="scroll"><table><thead><tr>'+headers.map(h=>'<th scope="col">'+escape(h)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+r.map(x=>'<td>'+escape(x)+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';}
function timeline(){
 const events=[];let completed=0;
 Object.entries(cases).forEach(([key,c])=>{const s=session[key];if(!s||s.prediction===null)return;events.push(`${c.label}: expectation recorded.`);s.tools.forEach(t=>events.push('Inspected: '+c.tools.find(x=>x[0]===t)[1]+'.'));if(s.recommendation!==null){events.push('Recommendation compared with the evidence.');completed++;}});
 $('trail').innerHTML=events.length?events.map(e=>'<li>'+escape(e)+'</li>').join(''):'<li>Choose a case and record an expectation to begin.</li>';
 $('progress').textContent=`${completed} of ${Object.keys(cases).length} recommendations reviewed. This tracks exploration, not model quality.`;
}
function showCase(key){
 active=key;selectedTool='';const c=cases[key],s=state();
 document.querySelectorAll('[data-case]').forEach(b=>{b.classList.toggle('active',b.dataset.case===key);b.setAttribute('aria-pressed',String(b.dataset.case===key));});
 $('caseLabel').textContent=c.label;$('caseTitle').textContent=c.title;$('complaint').textContent=c.complaint;$('context').textContent=c.context;
 $('predictionOptions').innerHTML=options(c.predictions,'prediction');$('reason').value=s.reason;$('predictionForm').hidden=s.prediction!==null;$('recorded').hidden=s.prediction===null;
 if(s.prediction!==null)$('recorded').textContent='Initial expectation: '+c.predictions[s.prediction]+(s.reason?' Your note: '+s.reason:'');
 $('predictionError').textContent='';$('evidenceStage').hidden=s.prediction===null;$('decisionStage').hidden=true;$('decisionFeedback').innerHTML='';
 $('toolChoices').innerHTML=c.tools.map(([id,label])=>`<button data-tool="${id}" aria-pressed="false">${escape(label)}</button>`).join('');
 $('evidenceView').innerHTML='<p class="muted">Choose the evidence that would best test your expectation.</p>';
 $('decisionOptions').innerHTML='<legend class="sr-only">Recommendation</legend>'+options(c.decisions,'recommendation');
 $('stepPredict').className=s.prediction===null?'current':'done';$('stepEvidence').className=s.prediction===null?'':'current';$('stepDecision').className='';
 document.querySelectorAll('[data-tool]').forEach(b=>b.addEventListener('click',()=>inspect(b.dataset.tool)));
 if(s.tools.length)inspect(s.tools[s.tools.length-1]);
 if(s.recommendation!==null){const saved=document.querySelector('input[name="recommendation"][value="'+s.recommendation+'"]');if(saved)saved.checked=true;showFeedback();}timeline();
}
function budgetControls(){return '<div class="budget"><label>Staff minutes per 100 learners</label>'+[150,300,600].map(b=>`<button data-budget="${b}" aria-pressed="${b===budget}">${b} minutes</button>`).join('')+'</div>';}
function inspect(tool){
 selectedTool=tool;const s=state();if(!s.tools.includes(tool))s.tools.push(tool);
 document.querySelectorAll('[data-tool]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.tool===tool)));
 let content='';
 if(active==='model'){
  if(tool==='ranking'){
   content='<h3>Adverse-outcome PR-AUC on validation</h3><p class="muted">Full axis: 0–1. PR-AUC summarizes ranking of later Fail/Withdrawn cases. Hover or focus a bar for its meaning.</p><div class="chart">'+evidence.models.map(r=>bar(labels[r.model],r.adverse_pr_auc,r.model==='hgb_15_10'?'var(--ref)':'#8295b8','Validation ranking; higher AP is better, but uncertainty and selection still matter.','ap')).join('')+'</div>'+source('models')+'<div class="note">A higher point estimate alone does not show that switching will improve the decision.</div>';
  }else{
   content='<h3>Random Forest minus histogram boosting</h3>'+table(['Outcome AP','Mean difference','95% lower','95% upper'],evidence.model_intervals.map(r=>[r.metric,r.difference_mean.toFixed(4),r.ci95_lower.toFixed(4),r.ci95_upper.toFixed(4)]))+source('intervals')+'<p class="muted">Student-cluster bootstrap; unadjusted exploratory intervals conditional on fitted models and validation selection. Crossing zero means inconclusive, not equivalent.</p><h3>Decision coverage at the same staff effort</h3>'+evidence.models.filter(r=>['forest','hgb_15_10'].includes(r.model)).map(r=>bar(labels[r.model],r.adverse_coverage,'var(--ref)','Later adverse cases reached, not prevented outcomes.')).join('')+source('models');
  }
 }else if(active==='detector'){
  const a=evidence.policies.find(r=>r.policy==='classifier_only'),b=evidence.policies.find(r=>r.policy==='coupled_selected');
  if(tool==='targeting'){
   content='<h3>Same cohort, actions and staff effort</h3>'+[a,b].map(r=>bar(labels[r.policy],r.adverse_coverage,r.policy==='classifier_only'?'var(--ref)':'var(--alt)',`${number(r.flagged_n)} contacts; ${number(r.staff_minutes)} staff minutes; pooled adverse coverage.`)).join('')+`<div class="metric-grid"><div class="metric"><b>${number((b.adverse_coverage-a.adverse_coverage)*evidence.adverse_n)}</b><span>additional later adverse cases flagged by the blend</span></div><div class="metric"><b>${number(a.staff_minutes)}</b><span>staff minutes for either policy</span></div><div class="metric"><b>${number(a.flagged_n)}</b><span>contacts for either policy</span></div></div><div class="note">The blend weight was selected on this validation cohort. Inspect its paired interval before treating a small gain as established.</div>`+source('policies');
  }else{
   const ci=evidence.blend_interval.ci95;
   content=`<h3>Coupled minus classifier-only coverage</h3><div class="metric-grid"><div class="metric"><b>${((b.adverse_coverage-a.adverse_coverage)*100).toFixed(2)} pp</b><span>observed coverage difference</span></div><div class="metric"><b>${(ci[0]*100).toFixed(2)} pp</b><span>95% lower bound</span></div><div class="metric"><b>${(ci[1]*100).toFixed(2)} pp</b><span>95% upper bound</span></div></div>`+table(['Policy','Fail coverage','Withdrawn coverage','Contact precision'],[a,b].map(r=>[labels[r.policy],percent(r.fail_coverage),percent(r.withdrawn_coverage),percent(r.flag_precision)]))+source('blend')+source('policies')+'<div class="note">The interval crosses zero. Outcome-specific movements differ. This does not establish added deployment value or intervention effectiveness.</div>';
  }
 }else{
  const rows=evidence.budgets.filter(r=>r.value===budget),a=rows.find(r=>r.policy==='classifier_only');
  content=budgetControls();
  if(tool==='coverage')content+='<h3>Later adverse cases reached</h3>'+rows.map(r=>bar(labels[r.policy],r.adverse_coverage,r.policy==='classifier_only'?'var(--ref)':r.policy==='business_rule'?'#8295b8':'var(--alt)',`${number(r.adverse_coverage*evidence.adverse_n)} of ${number(evidence.adverse_n)} later adverse cases.`)).join('')+`<div class="note">Classifier-only contact precision: <strong>${percent(a.flag_precision)}</strong>. Precision is the share of contacted learners with a later adverse outcome, not contact effectiveness.</div>`;
  else content+=`<div class="metric-grid"><div class="metric"><b>${number(a.human_n)}</b><span>human reviews</span></div><div class="metric"><b>${number(a.alert_n)}</b><span>alerts</span></div><div class="metric"><b>${number(a.n-a.flagged_n)}</b><span>no action</span></div></div><h3>Effort used under this scenario</h3><p><strong>${number(a.staff_minutes)} / ${number(a.n*budget/100)} minutes available.</strong></p><p>Human review and alert effort follow the configured assumptions, with the alert cap enforced. These are computed actions, not recorded interventions.</p>`;
  content+=source('budgets')+'<p class="muted">Same validation cohort; the selected blend weight stays fixed across budgets. No live learner data are entered or transmitted.</p>';
 }
 $('evidenceView').innerHTML=content;$('decisionStage').hidden=false;$('stepEvidence').className='done';$('stepDecision').className='current';
 $('evidenceView').querySelectorAll('[data-budget]').forEach(b=>b.addEventListener('click',()=>{budget=Number(b.dataset.budget);inspect(selectedTool);}));timeline();
}
$('predictionForm').addEventListener('submit',e=>{e.preventDefault();const input=document.querySelector('input[name="prediction"]:checked');if(!input){$('predictionError').textContent='Choose an expectation before opening the evidence.';return;}state().prediction=Number(input.value);state().reason=$('reason').value.trim();showCase(active);});
function showFeedback(){const c=cases[active];$('decisionFeedback').innerHTML=`<div class="feedback"><strong>${state().recommendation===c.supported?'Your recommendation matches the supported interpretation.':'Consider the uncertainty and tradeoffs before acting.'}</strong><p>${escape(c.feedback)}</p></div>`;$('stepDecision').className='done';}
$('checkDecision').addEventListener('click',()=>{const picked=document.querySelector('input[name="recommendation"]:checked');if(!picked){$('decisionFeedback').textContent='Choose a recommendation to compare with the evidence.';return;}state().recommendation=Number(picked.value);showFeedback();timeline();});
document.querySelectorAll('[data-case]').forEach(b=>b.addEventListener('click',()=>showCase(b.dataset.case)));
$('reset').addEventListener('click',()=>{session={};budget=300;showCase('model');});
$('export').addEventListener('click',()=>{const lines=['TalentRoute — personal session reflection','Development evidence only. Illustrative prompts; not a deployment approval.',''];Object.entries(session).forEach(([key,s])=>{if(s.prediction===null)return;const c=cases[key];lines.push(c.title,'Initial expectation: '+c.predictions[s.prediction],'Evidence that could change my mind: '+s.reason,'Evidence inspected: '+s.tools.map(t=>c.tools.find(x=>x[0]===t)[1]).join('; '),'Recommendation: '+(s.recommendation===null?'Not recorded':c.decisions[s.recommendation]),'');});const url=URL.createObjectURL(new Blob([lines.join('\n')],{type:'text/plain;charset=utf-8'}));const link=document.createElement('a');link.href=url;link.download='TalentRoute_personal_reflection.txt';link.click();URL.revokeObjectURL(url);});
showCase('model');
