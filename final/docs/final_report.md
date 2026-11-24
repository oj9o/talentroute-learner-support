# TalentRoute: assessment-free learner-support decisions

Mouza Aldarmaki · MAAI7101 · Final project

## Executive summary

TalentRoute helps a learner-support coordinator decide which course cases to review or alert when staff time is limited. The final recommended demonstration uses an assessment-free classifier, selected using learner-grouped folds within 2013B, and a risk-ranked queue. It excludes assessment scores and submission-derived fields because their availability at the decision date cannot be fully established. Classification and a connected Isolation Forest review-reserve experiment implement two technique families; evidence does not justify activating that reserve by default.

On previously examined 2014B, the identity-disjoint evaluation contacts 1,258 of 3,151 later adverse-outcome cases (39.9%), against 38.6% for inactivity ranking at identical staffing capacity. The paired difference interval is [-0.19, 2.78] percentage points. It crosses zero: superiority is not established. These are retrospective targeting results, not prevented failures, measured intervention effects or independent final-test evidence.

The practical output is an adjustable queue with a separate feasibility checker. The strongest defensible conclusion is that staffing assumptions and course composition materially change who gets attention. The app makes these trade-offs inspectable. It is a research prototype, not a validated institutional policy.

## 1. Who decides what, and why?

An educational consulting team may support universities as well as other learning providers. Its coordinator receives a list of enrolled learners at day 28 and has a finite amount of staff time. A human review means a staff member investigates a course case; an alert is a lower-effort contact. The coordinator sets available minutes, assumed effort, eligible risk scores and the share reserved for alerts. TalentRoute ranks cases and proposes mutually exclusive review, alert or no-action assignments. A person checks feasibility and decides whether outreach is appropriate.

The business question is: **How should limited review and alert capacity be directed toward learners with later observed Fail or Withdrawn outcomes, and where does that allocation fail?** This makes the university population directly relevant to the consulting scenario. There is no assertion that university learners behave like corporate employees. Applying the system elsewhere would require local data, workflow agreement and validation.

Four questions structure the evidence: Does classification outperform a simple comparator? Does an anomaly review reserve add targeting value? How do staffing assumptions and course or learner segments change the queue? Which attractive alternatives fail or remain uncertain? A valuable result can be a rejected method or a capacity constraint, rather than a higher headline score.

## 2. Proposed system

```mermaid
flowchart LR
    A[Day-28 engagement and enrolment inputs] --> B[Assessment-free classifier]
    A --> C[Training-fitted Isolation Forest]
    B --> D[Risk-ranked review and alert queue]
    C --> E[Optional reserve inside existing review capacity]
    E --> D
    F[Staff time and action costs] --> D
    D --> G[Separate feasibility checker]
    G --> H[Coordinator inspects and decides]
```

The default uses no anomaly reserve; the connected reserve is an evaluated alternative. Later observed outcomes are used only to evaluate the frozen assignments, never by the allocator or checker.

## 3. Evaluation setup and results

OULAD is a public distance-learning dataset with registration, platform activity, assessments and observed outcomes. Each row in the modeling table is a course enrolment, not necessarily a unique person. Pass and Distinction map to Success; Fail and Withdrawn remain separate classifier classes. Their combined adverse indicator is used only for the declared targeting metric. The separate action/outcome counts prevent that combination from hiding different mechanisms. No outcome labels are simulated.

Features are restricted to information recorded by day 28: engagement counts in early and later windows, their change, inactivity, study credits, previous attempts and course. Log counts reduce extreme activity scale; inactivity represents the absence of recent recorded engagement. These are plausible warning signals, not measures of motivation or proof of causation. All numeric imputation and model-specific preprocessing fit training records only. IDs, gender, final outcomes and post-cutoff activity are not predictors. Gender is used only for audit. There is no clustering or dimensionality reduction added merely to display another technique.

OULAD does not establish exact assessment score-release dates. Restricting submission dates alone cannot prove a grade was visible. The final system conservatively removes **all five assessment-derived inputs**. The score-release issue directly concerns scores; removing submission counts, lateness and the no-early-assessment indicator is a broader simplification to avoid dependence on assessment schedules and recording assumptions. A submission-only variant was not tested, and these fields are not asserted to be inherently unavailable. Earlier 2014B diagnostics prompted this design decision; training-only candidate selection does not erase that exposure. Assessment fields retained in historical diagnostic tables are not accessed by its predictor. Mutation tests change assessments and outcomes while checking that final predictions stay identical.

Training uses 2013B; evaluation uses 2014B. Calendar interval checks account for uncertain start days and assumed result-release delays. Training on earlier completed courses is more defensible than using a possibly unfinished later presentation, but final-result publication remains an assumption. The identity-disjoint design removes overlapping evaluation identities from training. The operational companion retains mature prior enrolments and reports returning learners separately. Both evaluate the same cases; neither selects training rows using 2014J membership.

The final classifier and preprocessing are selected within three learner-grouped training folds, comparing six bounded candidates: logistic regularization levels, a constrained tree and two boosting capacities. The ranking rule is mean fold coverage, then average precision, then fixed candidate order. The selected candidate is logistic regression with C=1. Its mean fold coverage ties C=10, but its unrounded AP is slightly higher (0.730185675 versus 0.730183657); fixed candidate order did not decide this result. The chosen family is fitted on all allowed training rows before evaluation. The candidate grid reflects earlier project learning, so this separation repairs direct selection on evaluation labels but does not create a fresh experiment.

Both 2014B and 2014J were previously examined. Repeated splits, new seeds and a new freeze cannot restore independence. No fresh cohort is available. This revision does not score 2014J again and does not claim the independent final-evaluation requirement is fully satisfied. Its results are retrospective development evidence; an external future cohort remains necessary for confirmation.

### Models, metrics and comparators

The primary ML metric is adverse-outcome average precision (AP), appropriate for assessing ranking against the observed adverse prevalence. The final model has AP 0.661, with conditional learner-bootstrap interval [0.646, 0.678]. Brier score and class-specific metrics are also exported. The primary decision metric is the fraction of actual adverse cases contacted at a common workload. Contact precision, separate Fail/Withdrawn counts, review/alert counts and staff minutes qualify that measure. Coverage treats both contacts equally; it does not itself answer which intervention is worth its cost.

The default scenario allocates 300 staff minutes per 100 enrolments, assumes 30 minutes per review and two per alert, reserves an initial alert budget share of 20%, and caps alerts at 20% of cases. Whole-action rounding and the remaining time determine capacity. These are explicit constructed assumptions, not observed university practice. For this cohort the queue has 564 reviews and 1,301 alerts, consuming 19,522 minutes. Its contact precision is 67.5%. Reviews reach 456 adverse cases versus 444 for inactivity, while 108 versus 120 reviewed cases later succeed. These counts distinguish action tiers without claiming support was unnecessary.

Isolation Forest fits engagement features on training data only. Its training-reference anomaly percentile ranks a separately reserved portion of the existing review capacity. It is never added to the outcome probability: equal numeric ranges do not imply comparable meanings. Removing the reserve gives the default classifier-only queue. Inactivity, course round-robin and seeded-random reserves test whether the detector earns its complexity. A full inactivity-ranked queue is the transparent no-model comparator; it is distinct from reserving only some reviews for inactivity.

All route comparisons use the same capacity. Cutoff sweeps apply the classifier eligibility mask to the inactivity comparator too, so they compare ordering among the same eligible cases. Thresholds are model-score eligibility rules, not calibrated guarantees. No threshold or cost is selected for a favorable retrospective result.

### ML-level comparison

| adverse_average_precision | average_precision_low | average_precision_high | inactivity_outcome_ap | isolation_forest_outcome_ap |
| --- | --- | --- | --- | --- |
| 0.661 | 0.646 | 0.678 | 0.627 | 0.595 |

### Training-only candidate comparison

| model | coverage | adverse_average_precision |
| --- | --- | --- |
| hgb_15_10 | 0.420 | 0.704 |
| hgb_7_2 | 0.422 | 0.715 |
| logistic | 0.438 | 0.730 |
| logistic_c01 | 0.436 | 0.730 |
| logistic_c10 | 0.438 | 0.730 |
| tree | 0.422 | 0.698 |

### Final-system results and uncertainty

| route | adverse_contact_n | coverage | contact_precision | staff_minutes | difference_low | difference_high |
| --- | --- | --- | --- | --- | --- | --- |
| classifier | 1258 | 0.399 | 0.675 | 19522.000 | 0.000 | 0.000 |
| anomaly | 1260 | 0.400 | 0.676 | 19522.000 | -0.001 | 0.002 |
| inactivity | 1258 | 0.399 | 0.675 | 19522.000 | 0.000 | 0.000 |
| course | 1258 | 0.399 | 0.675 | 19522.000 | 0.000 | 0.000 |
| random | 1254 | 0.398 | 0.672 | 19522.000 | -0.007 | 0.004 |
| inactivity_baseline | 1216 | 0.386 | 0.652 | 19522.000 | -0.028 | 0.002 |

The difference interval columns compare each route with classifier-only. The separate inactivity comparison is reported in the executive summary and exported CSV. Intervals resample learners with all their enrolments together, holding predictions and assignments fixed. They describe conditional sampling uncertainty; they exclude refitting, earlier search and workflow uncertainty. They are not prospective confidence claims or treatment-effect intervals.

The operational companion contacts 1,257 adverse cases (39.9%). Similar aggregate results across these designs do not prove generalization. Three seed checks refit the fixed selected candidate and vary tie-breaking and detector seeds; their spread is reported separately. Logistic fitting is deterministic here, so unchanged classifier coverage is expected; detector variation is the meaningful stochastic check. Seeds are not independent test populations.

![Final route comparison](../outputs/figures/final_comparison.png)

## 4. Ablation

The anomaly reserve contacts 1,260 adverse cases, only 2 more than classifier-only. Its paired coverage-difference interval is [-0.10, 0.22] percentage points. It changes 83 actions, gains 4 adverse contacts and loses 2. This distinguishes changed action type from newly reached people. Detector outcome AP is 0.595, below inactivity's 0.627; outcome AP is only a relevance diagnostic because true anomaly labels do not exist. The default remains zero detector reserve.

## 5. Sensitivity, stability and concentrated failures

Five sweeps vary budget, review effort, reserve share, score cutoff and alert share, one at a time. Results and workload counts are generated for both populations using the final assessment-free predictions. The budget and effort curves show how staffing choices change the observed coverage; they do not show saved students. More resources can increase contact reach, while a higher cutoff may leave capacity unused.

| parameter | value | classifier_minus_inactivity | anomaly_minus_classifier |
| --- | --- | --- | --- |
| alert_budget_fraction | 0.000 | 10 | 1 |
| alert_budget_fraction | 0.100 | 24 | -1 |
| alert_budget_fraction | 0.200 | 42 | 2 |
| alert_budget_fraction | 0.400 | 42 | 2 |
| minutes_per_100 | 150.000 | 3 | 1 |
| minutes_per_100 | 300.000 | 42 | 2 |
| minutes_per_100 | 600.000 | 52 | 1 |
| minutes_per_100 | 900.000 | 89 | -2 |
| reserve_fraction | 0.000 | 42 | 0 |
| reserve_fraction | 0.100 | 42 | 0 |
| reserve_fraction | 0.200 | 42 | 2 |
| reserve_fraction | 0.300 | 42 | 2 |
| review_minutes | 15.000 | 55 | -1 |
| review_minutes | 30.000 | 42 | 2 |
| review_minutes | 45.000 | 44 | 1 |
| review_minutes | 60.000 | 26 | 1 |
| risk_threshold | 0.000 | 42 | 2 |
| risk_threshold | 0.250 | 42 | 2 |
| risk_threshold | 0.500 | 31 | 1 |
| risk_threshold | 0.750 | 0 | 0 |

The classifier point advantage remains positive across the tested budget and effort settings, but these sweep differences have no uncertainty intervals and the default interval crosses zero. At cutoff 0.75 the common eligibility gate leaves all queues contacting the same 966 adverse cases; this is not evidence of ranking robustness. Alert shares 0.2 and 0.4 coincide because the alert-count cap binds. Anomaly differences remain between minus two and plus two cases across these sweeps; no tested setting establishes a reason to activate the reserve.

![Budget and effort sensitivity](../outputs/figures/final_sensitivity.png)

Course GGG receives 36.2% of staff minutes while representing 12.2% of cases. It reaches 264 of 318 adverse cases (83.0%). This describes concentration in the current queue. Earlier course results used a different model and population and are not a matched before/after comparison. Course calibration and queue composition make this visible. A coordinator should review course-specific workload and score reliability before using the global queue.

Overall female adverse coverage is 48.1%, versus 34.5% for males. Contact precision is 60.1% for women and 76.1% for men. Women account for 75 of 108 later-successful reviewed cases. Within-course coverage gaps are smaller in CCC (30.5% versus 31.4%) and GGG (82.6% versus 84.6%). These patterns do not establish fairness or causally explain the aggregate gap through course mix. Within-course comparisons retain denominators and conditional intervals; groups below 50 cases or ten adverse outcomes are marked unsuitable for interpretation. No protected-attribute quota is silently introduced.

![Queue composition and resource concentration](../outputs/figures/final_queue_composition.png)

![Within-course gender comparisons](../outputs/figures/final_gender_by_course.png)

Among contacted cases, mean predicted adverse risk is 83.9%, while the observed adverse rate is 67.5%. The overstatement means displayed scores should support ranking, not be read as verified individual probabilities. Calibration would need training-only fitting followed by genuinely new evaluation; fitting a correction on this exposed evaluation cohort would not repair confirmation.

| group | n | mean_predicted | observed_rate | brier |
| --- | --- | --- | --- | --- |
| course_BBB | 1280 | 0.548 | 0.432 | 0.232 |
| course_CCC | 1498 | 0.535 | 0.557 | 0.216 |
| course_DDD | 1028 | 0.586 | 0.535 | 0.214 |
| course_EEE | 605 | 0.510 | 0.410 | 0.208 |
| course_FFF | 1301 | 0.478 | 0.497 | 0.214 |
| course_GGG | 796 | 0.770 | 0.399 | 0.354 |

The workload stress test freezes membership before changing effort. Raising reviews from 30 to 45 minutes creates a 8,458-minute shortfall. An explicit alerts-first contingency defers 188 original contacts and retains 35.3% adverse coverage. Replanning under the same stressed budget gives 37.0%. Both are feasible; neither is asserted to maximize real intervention benefit. This exposes failure and an actionable fallback instead of hiding overspend through automatic reallocation.

## 6. Three promised deeper investigations

**Equal-quota reconciliation.** Interleave classifier, anomaly and inactivity rankings at the same total quota, removing duplicate cases. The Swiss Cheese idea motivates looking for complementary misses, not assuming independent layers. The output below tests that idea directly. More layers do not guarantee better coverage, and the global risk queue remains the default.

| policy | adverse_contact_n | coverage | staff_minutes |
| --- | --- | --- | --- |
| round_robin_layers | 1244 | 0.395 | 19522.000 |
| classifier | 1258 | 0.399 | 19522.000 |

**Warning-positive profiles.** Compare later Success, Fail and Withdrawn among final flagged cases, reporting inactivity and the count with observed assessment scores. Scores here are descriptive only. A flagged learner who succeeds is neither proof of resilience nor proof of wasted support: no intervention history establishes either explanation. The analysis helps identify what staff would need to investigate rather than assigning a fabricated reason.

| outcome | n | inactivity_median | score_observed_n |
| --- | --- | --- | --- |
| Fail | 835 | 14.000 | 165 |
| Success | 607 | 10.000 | 187 |
| Withdrawn | 423 | 10.000 | 100 |

**Course specialization and learner segments.** Fit a local logistic model only where training has at least 300 cases and 30 examples per class; otherwise retain the selected global model. All models use assessment-free features. Eligibility is determined from training, never from evaluation success. The exploratory comparison below is reported without promoting the best-looking result after inspection. Returning-learner, unseen-course and within-course demographic audits accompany it.

| variant | average_precision | coverage | adverse_contact_n |
| --- | --- | --- | --- |
| global_selected | 0.661 | 0.399 | 1258 |
| module_logistic | 0.667 | 0.404 | 1272 |

These analyses sharpen the recommendation: keep the simple global queue as a transparent demonstration, review concentration explicitly, and require new evidence before adopting specialists or the detector reserve. They do not imply that the original two-family design was successful merely because both algorithms run.

## 7. Insights and recommendations

**Staffing dominates the practical decision.** Increasing available time changes reach more than adding an anomaly reserve. Agree actual effort and available staff time before model refinements. If effort rises, compare a replanned queue with the explicit contingency; neither is optimal without real action values.

**Model complexity has not established better outcomes.** Keep inactivity as a standing comparator. Treat classification as a provisional ranking and retain zero anomaly reserve. Specialists are exploratory rather than a selected deployment alternative.

**A feasible queue still needs scrutiny.** Review GGG's concentrated workload and score reliability with course staff before outreach. Do not present uncalibrated scores as verified personal probabilities. A flag initiates investigation, not a diagnosis; coordinate multiple course cases belonging to one learner.

The decision rules have explicit limits:

| Decision | Why this choice | When to reconsider |
|---|---|---|
| Assessment-free inputs | Avoid uncertain score availability | Verify input timestamps before adding assessment fields |
| No anomaly reserve | Added targeting value is not established | Require new evidence before reserving scarce review places |
| Review, alert or no action | Apply the declared ranking and staffing caps | Recheck costs and capacity when staffing changes |
| No action for an eligible case | Capacity can run out | Do not interpret it as evidence the learner is safe |
| Human approval before outreach | Feasibility does not establish intervention value | Review course concentration and repeated-learner contacts |

Coverage cannot identify the best intervention. As an additional analysis, conditional preference scenarios weight reviews and alerts separately, distinguish Fail and Withdrawn, penalize contacts to later Success cases, and subtract assumed effort. Weights are external scenario preferences applied to observed outcome counts, not to the score used for selection. This avoids the earlier circular evaluation. Break-even calculations show which assumed review value would favor a reserve, and paired fixed-action intervals show uncertainty. None estimates causal benefit, monetary ROI or the true cost of a false flag.

The action-value analysis is an additional decision-relevant deep dive. The table reports reserve-versus-risk-only preference differences under the declared default weights; intervals remain conditional and are not intervention-effect estimates.

| route | preference_difference | difference_low | difference_high |
| --- | --- | --- | --- |
| classifier | 0.000 | 0.000 | 0.000 |
| anomaly | -7.700 | -31.768 | 18.997 |
| inactivity | 0.000 | 0.000 | 0.000 |
| course | 0.000 | 0.000 | 0.000 |
| random | -53.200 | -95.643 | -9.150 |

## 8. Limitations, failed approaches and risks

The experiment history is explicit. In the matched training-only audit, assessment-enabled prediction reaches 1,357 adverse cases versus 1,258 assessment-free. The latter sacrifices targeting performance to remove that input dependence; it is not an accuracy improvement. Direct development-cohort model choice was replaced by training-only grouped selection, while acknowledging earlier exposure. Adding anomaly ranks did not establish incremental value; numerical probability/percentile blending was rejected. Equal-quota reconciliation and specialists were executed rather than advertised as guaranteed improvements. The package uses one workbench and one final report generator. Unused historical plot code was removed; current and historical model choices have distinct names. Historical numerical experiments remain labeled for reproducibility.

The app lets a user change capacity, effort, eligibility and route, then inspect actions and workload. A separate checker tests an edited plan without outcomes. Saved-setting comparison shows entering, leaving and changed-action cases. Individual input edits rescore a fitted model; they do not manufacture a future outcome or simulate the causal effect of changing behavior. Exports omit student IDs, protected attributes and outcomes. Multiple course cases for one learner still require coordination before real outreach.

## 9. Connection to the original problem, next steps and reproduction

The coordinator receives a feasible, inspectable allocation and evidence of where it concentrates attention. This answers who could be contacted under declared constraints; it does not establish which support action prevents failure. Real workflow agreement and new outcomes are prerequisites for operational adoption.

Use Python 3.14 with `uv` and `just`: `just install`, `just pipeline`, then `just app`. The CPU pipeline verifies pinned public data, fits models, generates all comparisons and this report, and runs meaningful tests for time eligibility, training-only selection, mutation invariance, budget arithmetic, deterministic allocation and app/output consistency. Runtime is measured in `outputs/runtime.csv`. Linux reproduction checks portability; no LLM or credentials are required to run the project.

All final-system evidence is named `outputs/final_*.csv`, with `routing_model=assessment_free` and the retrospective scope. `availability_selection.csv` records the training-fold selection; `availability_audit.csv` records the matched feature-removal comparison. Unprefixed model, route and sensitivity files are historical assessment-enabled experiments, not evidence for the final recommendation. Figure captions and the presentation use final-prefixed results.

Recommend the assessment-free, risk-only workbench for explaining constrained decisions and investigating errors. Do not describe it as a proven improvement over inactivity, a calibrated individual-risk service or a validated intervention policy. The final deliverable documents useful implementation and decision analyses while openly retaining the independent-evaluation gap. A future deployment would require a new cohort, real workflow costs, permissioned outreach, and measured outcomes under a defensible intervention design.

Data source: Kuzilek, Hlosta and Zdrahal, Open University Learning Analytics Dataset, UCI, DOI 10.24432/C5KK69, CC BY 4.0. Course concepts applied include classifier comparisons, leakage checks, error slicing, domain-grounded features, and the Beyond Predictions explain/check/compare pattern.
