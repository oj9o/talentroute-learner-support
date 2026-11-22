const $ = (id) => document.getElementById(id);
const pct = (n) => (n == null ? "Not available" : `${(n * 100).toFixed(1)}%`);
const number = (n) =>
  n == null
    ? "—"
    : Number(n).toLocaleString(undefined, { maximumFractionDigits: 1 });
let revision = 0;
let savedSettings = null;
let currentSettings = null;
let editableCases = [];
function payload() {
  return {
    protocol: $("protocol").value,
    model: $("model").value,
    route: $("route").value,
    policy: {
      minutes_per_100: +$("budget").value,
      risk_threshold: +$("threshold").value,
      reserve_fraction: +$("reserve").value,
      alert_budget_fraction: +$("share").value,
      review_minutes: +$("reviewMinutes").value,
      alert_minutes: +$("alertMinutes").value,
    },
    values: {
      fail_value: +$("failValue").value,
      withdrawn_value: +$("withdrawnValue").value,
      review_weight: +$("reviewWeight").value,
      alert_weight: +$("alertWeight").value,
      review_success_burden: +$("reviewBurden").value,
      alert_success_burden: +$("alertBurden").value,
      effort_units_per_minute: +$("effortValue").value,
    },
  };
}
async function post(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) throw Error(data.error || "Unable to calculate");
  return data;
}
function labels() {
  $("budgetValue").textContent = number(+$("budget").value);
  $("thresholdValue").textContent = pct(+$("threshold").value);
  $("reserveValue").textContent = pct(+$("reserve").value);
  $("shareValue").textContent = pct(+$("share").value);
  $("reserve").disabled = $("route").value === "classifier";
}
function countTable(m) {
  return `<table><thead><tr><th>Action</th><th>Cases</th><th>Later Fail</th><th>Later Withdrawn</th><th>Later Success</th></tr></thead><tbody>${[
    ["review", "Human review"],
    ["alert", "Alert"],
    ["no_action", "No action"],
  ]
    .map(
      ([key, label]) =>
        `<tr><td>${label}</td><td>${number(m[key + "_n"])}</td><td>${number(m[key + "_fail_n"])}</td><td>${number(m[key + "_withdrawn_n"])}</td><td>${number(m[key + "_success_n"])}</td></tr>`,
    )
    .join(
      "",
    )}</tbody></table><p class="note">Historical outcome counts are used to evaluate targeting after allocation. They are never inputs to the queue.</p>`;
}
async function update() {
  const request = ++revision;
  labels();
  $("status").textContent = "Calculating…";
  ["saveComparison", "checkPlan", "export"].forEach(id => $(id).disabled = true);
  $("error").textContent = "";
  try {
    const activeSettings = payload();
    const d = await post("/scenario", { ...activeSettings, previous: savedSettings });
    if (request !== revision) return;
    currentSettings = activeSettings;
    editableCases = d.editable_cases;
    renderDecisionTools(d);
    const m = d.metrics,
      t = d.transitions;
    $("metrics").innerHTML =
      `<div><strong>${number(m.review_n)}</strong><span>Human reviews</span></div><div><strong>${number(m.alert_n)}</strong><span>Alerts</span></div><div><strong>${pct(m.coverage)}</strong><span>Observed adverse outcomes reached</span></div>`;
    $("population").textContent =
      `${number(m.contact_n)} enrolment cases · ${number(t.unique_students_contacted)} distinct people · ${number(t.multiple_contact_students)} people selected in more than one course. ${number(m.staff_minutes)} of ${number(d.budget_minutes)} staff minutes used.`;
    $("actionCounts").innerHTML = countTable(m);
    $("composition").innerHTML = d.composition
      .map(
        (c) =>
          `<div class="bar-row"><b>${c.module}${c.unseen ? "*" : ""}</b><div class="bar" aria-label="${c.module}: ${c.review_n} reviews, ${c.alert_n} alerts, ${c.no_action_n} no action"><span class="review" style="width:${(100 * c.review_n) / c.n}%" title="${c.review_n} reviews"></span><span class="alert" style="width:${(100 * c.alert_n) / c.n}%" title="${c.alert_n} alerts"></span></div><span class="bar-total">${number(c.contact_n)} / ${number(c.n)}</span></div>`,
      )
      .join("");
    $("changes").textContent =
      `Against risk-only routing with the same model and constraints: ${t.changed_action_n} actions changed; ${t.new_contact_n} new cases entered and ${t.lost_contact_n} left the contact list. ${t.alert_to_review_n} alerts became reviews. ${t.reserved_outside_original_contacts_n} reserved reviews were outside the original contact list.`;
    $("valueResult").textContent =
      `Conditional preference score: ${number(d.assumed_preference_units)} units. This is not a measured benefit.`;
    $("workloadStress").innerHTML =
      `<table><thead><tr><th>Review / alert minutes</th><th>Fixed list</th><th>Extra minutes needed</th><th>Cases deferred</th><th>Coverage after deferral</th><th>Coverage if replanned</th></tr></thead><tbody>${d.workload_stress.map((s) =>
        `<tr><td>${number(s.review_minutes)} / ${number(s.alert_minutes)}</td><td>${s.frozen_feasible ? "Fits" : "Exceeds time"}</td><td>${number(s.shortfall_minutes)}</td><td>${number(s.deferred_n)}</td><td>${pct(s.retained_coverage)}</td><td>${pct(s.replanned_coverage)}</td></tr>`
      ).join("")}</tbody></table>`;
    $("queue").querySelector("tbody").innerHTML = d.queue
      .map(
        (r) =>
          `<tr><td>${r.case}</td><td>${r.module}</td><td>${pct(r.model_risk)}</td><td>${r.action}</td><td>${r.reason.replaceAll("_", " ")}</td></tr>`,
      )
      .join("");
    $("status").textContent = "Updated · development cohort";
    ["saveComparison", "checkPlan", "export"].forEach(id => $(id).disabled = false);
  } catch (error) {
    if (request === revision) {
      $("error").textContent = error.message;
      $("status").textContent = "Check settings";
    }
  }
}
let timer;
function schedule() {
  labels();
  clearTimeout(timer);
  timer = setTimeout(update, 200);
}
$("controls").addEventListener("submit", (e) => {
  e.preventDefault();
  update();
});
$("controls").addEventListener("change", schedule);
["budget", "threshold", "reserve", "share"].forEach((id) =>
  $(id).addEventListener("input", schedule),
);
$("valueUpdate").onclick = update;
$("export").onclick = async () => {
  const response = await fetch("/export", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload()),
  });
  if (!response.ok) {
    $("error").textContent = (await response.json()).error;
    return;
  }
  const url = URL.createObjectURL(await response.blob());
  const a = document.createElement("a");
  a.href = url;
  a.download = "talentroute_case_queue.csv";
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
};
const fieldLabels = {
  code_module: "Course",
  early_clicks: "Clicks · days 0–14",
  late_clicks: "Clicks · days 15–28",
  inactive_days: "Days since last activity",
  score_mean: "Mean early assessment score",
  score_min: "Minimum early score",
  submitted_count: "Early submitted assessments",
  late_rate: "Fraction submitted late",
  studied_credits: "Credits studied",
  num_of_prev_attempts: "Previous attempts",
};
async function loadCase() {
  const response = await fetch(
    `/case?index=${+$("caseNumber").value - 1}&protocol=${$("protocol").value}`,
  );
  const d = await response.json();
  if (!response.ok) {
    $("caseError").textContent = d.error;
    return;
  }
  $("caseFields").innerHTML = Object.entries(d)
    .map(
      ([key, value]) =>
        `<label>${fieldLabels[key]}${key === "code_module" ? `<select data-feature="${key}">${["AAA", "BBB", "CCC", "DDD", "EEE", "FFF", "GGG"].map((x) => `<option ${x === value ? "selected" : ""}>${x}</option>`).join("")}</select>` : `<input data-feature="${key}" type="number" min="0" step="${["score_mean", "score_min", "late_rate"].includes(key) ? "any" : "1"}" value="${value ?? ""}">`}</label>`,
    )
    .join("");
  $("caseError").textContent = "";
  await predict();
}
let predictionRevision = 0;
async function predict() {
  const request = ++predictionRevision;
  $("caseError").textContent = "";
  try {
    const inputs = {};
    document
      .querySelectorAll("[data-feature]")
      .forEach(
        (el) =>
          (inputs[el.dataset.feature] =
            el.dataset.feature === "code_module"
              ? el.value
              : el.value === ""
                ? null
                : +el.value),
      );
    const d = await post("/predict", { ...payload(), inputs });
    if (request !== predictionRevision) return;
    $("prediction").innerHTML =
      Object.entries(d.probabilities)
        .map(
          ([label, value]) =>
            `<div><strong>${pct(value)}</strong><span>Model estimate · ${label}</span></div>`,
        )
        .join("") +
      `<div><strong>${pct(d.anomaly_percentile)}</strong><span>Training-reference anomaly percentile</span></div><p class="note">${d.model} · ${d.protocol}. ${d.unseen_module ? "This course was absent from training. " : ""}Percentiles are not outcome probabilities. These estimates are not a guarantee or a validated causal what-if forecast.</p>`;
    $("caseError").textContent = d.warnings.join(" ");
  } catch (e) {
    if (request !== predictionRevision) return;
    $("caseError").textContent = e.message;
    $("prediction").innerHTML = "";
  }
}
$("caseForm").onsubmit = (e) => {
  e.preventDefault();
  predict();
};
$("loadCase").onclick = loadCase;
$("model").addEventListener("change", predict);
$("protocol").addEventListener("change", () => { savedSettings = null; predict(); });
function renderChecks(result) {
  return `<p class="plan-verdict ${result.feasible ? 'fits' : 'violates'}">${result.feasible ? 'Fits the declared constraints' : 'Does not fit — revise the plan'}</p><ul class="rule-list">${result.checks.map(c => `<li><strong>${c.passed ? 'Pass' : 'Fix'} · ${c.rule}</strong><span>${c.detail}</span></li>`).join('')}</ul>`;
}
function renderPlanCases() {
  $('planCases').querySelector('tbody').innerHTML = editableCases.map(r =>
    `<tr><td>${r.case}<br><small>${r.module}</small></td><td>${pct(r.risk)}</td><td>${r.explanation}</td><td><select aria-label="Action for ${r.case}" data-plan-index="${r.index}">${['No action','Alert','Review'].map((a,i) => `<option value="${i}" ${i === r.action ? 'selected' : ''}>${a}</option>`).join('')}</select></td></tr>`).join('');
  $('planResult').textContent = 'Ready to check. Other cases keep their current actions.';
}
function settingsDescription(p, route) {
  return `${p.minutes_per_100} minutes per 100 cases; score ≥ ${pct(p.risk_threshold)}; review ${p.review_minutes} min; alert ${p.alert_minutes} min; ${route === 'classifier' ? 'review reserve off' : `review reserve ${pct(p.reserve_fraction)}`}; initial alert share ${pct(p.alert_budget_fraction)}`;
}
function renderDecisionTools(d) {
  $('ruleChecks').innerHTML = renderChecks(d.decision_rules);
  $('reserveExplanation').textContent = `Initially ${number(d.decision_rules.initial_alert_reserve_minutes)} minutes are reserved for alerts. Whole review places are then filled; leftover time can fund alerts up to their case cap. The initial alert share is not a final spending ceiling. Unused minutes are allowed. Costs are per enrolment case.`;
  renderPlanCases();
  const c = d.comparison;
  $('comparisonLabel').textContent = c ? 'Saved comparison point retained. Change another setting or save a new Before.' : 'Save a starting point, then change a setting.';
  $('comparisonResult').innerHTML = c ? `<p><strong>Before:</strong> ${c.before_model} / ${c.before_route}. ${settingsDescription(c.before_policy, c.before_route)}</p><p><strong>After:</strong> ${c.after_model} / ${c.after_route}. ${settingsDescription(c.after_policy, c.after_route)}</p><div class="metrics"><div><strong>${c.changed}</strong><span>Changed actions</span></div><div><strong>${c.entered} / ${c.left}</strong><span>Entered / left contact list</span></div><div><strong>${number(c.after_minutes-c.before_minutes)}</strong><span>Change in staff minutes</span></div></div><p>${c.alert_to_review} alerts became reviews; ${c.review_to_alert} reviews became alerts. Staff time: ${number(c.before_minutes)} → ${number(c.after_minutes)} minutes.</p><table><thead><tr><th>Course</th><th>Before: selected</th><th>After: selected</th><th>Change</th></tr></thead><tbody>${c.courses.map(r => `<tr><td>${r.module}</td><td>${r.before}</td><td>${r.after}</td><td>${r.after-r.before}</td></tr>`).join('')}</tbody></table>` : '';
}
$('saveComparison').onclick = async () => {
  if (!currentSettings) return;
  savedSettings = structuredClone(currentSettings);
  await update();
};
$('resetPlan').onclick = renderPlanCases;
$('overloadPlan').onclick = () => {
  document.querySelectorAll('[data-plan-index]').forEach(el => { el.value = '2'; });
  $('planResult').textContent = 'Example: request reviews for every displayed case. Check whether the full plan fits.';
};
$('checkPlan').onclick = async () => {
  if (!currentSettings) return;
  const version = revision;
  const edits = [...document.querySelectorAll('[data-plan-index]')].map(el => ({index: +el.dataset.planIndex, action: +el.value}));
  try {
    const result = await post('/check-plan', {...currentSettings, edits});
    if (version !== revision) return;
    $('planResult').innerHTML = renderChecks(result) + `<p>${result.changes.changed} proposed actions differ from the current queue. No changes have been applied.</p>`;
  } catch (e) {
    $('planResult').textContent = e.message;
  }
};
async function initialize() {
  try {
    const response = await fetch('/configuration');
    const configuration = await response.json();
    if (!response.ok) throw Error(configuration.error || 'Unable to load the selected model');
    $('model').value = configuration.selected_model;
    $('protocol').value = configuration.default_protocol;
    await update();
    await loadCase();
  } catch (error) {
    $('error').textContent = error.message;
  }
}
initialize();
