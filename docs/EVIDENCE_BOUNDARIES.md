# Evidence boundaries

## What the system answers
At day 28, which eligible OULAD enrolments should enter a limited-staff-time review or alert queue? Predictions concern observed final outcomes, not the effect of contacting a student.

## Real outcomes and derived targets
`final_result` is observed in OULAD. Pass and Distinction are grouped as Success; Fail and Withdrawn remain distinct. No synthetic outcome, anomaly label, intervention response or employee outcome is created. Synthetic case references and test fixtures are identifiers/testing devices, not research outcomes.

## What an anomaly score means
Isolation Forest estimates unusual engagement relative to training observations. Its training-reference percentile is neither a failure probability nor proof that a student needs support. High engagement can also be unusual. Evaluation against Fail/Withdrawn is explicitly outcome-relevance evaluation, not verified anomaly-detection accuracy. The classifier and detector share engagement inputs; statistical independence is not asserted.

## Costs, timing and actions
Staff minutes, alert effort and review effort are configurable planning assumptions. The grading-availability lag is an assumption because actual grading timestamps are unavailable. Sensitivity analysis tests consequences; it does not validate that these assumptions are true. Equal counting of alerts and reviews measures targeting coverage, not equivalent effectiveness. Capacity is allocated by declared ranking and effort rules; this is not optimal treatment allocation.

## Why the population changed
The project studies university students directly. It does not equate students with employees. Corporate learning is only a possible future application requiring company-specific data, validation and outcome evidence. There are no causal prevention, retention, uplift or ROI claims.

## Why an unsuccessful component stays visible
The detector is an implemented candidate and an ablation subject. A zero-crossing improvement interval is inconclusive. A negative result must not be converted into a success claim, and the component must not be forced into deployment merely to satisfy a technique count. If the accepted final recommendation excludes it, explicitly discuss the rubric's connected-techniques requirement with the instructor rather than claim an unimplemented second operational role.

## Validation versus final evidence
All current development comparisons are validation explorations, including later contextual-detector comparisons. Their intervals condition on fitted scores and do not eliminate selection or multiple-comparison bias. Test results may only follow a recorded candidate/parameter/metric freeze. No post-test retuning is permitted. The current development files do not certify a completed final submission.
