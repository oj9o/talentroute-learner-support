# Presentation narration

TALENTROUTE — FINAL ASSESSMENT-FREE RECORDING SCRIPT
Target duration: 09:44. 966 spoken words including transitions.
Timing estimate uses the reported 120 words in 65 seconds; no audio recording was measured.
Record a full rehearsal. Slides 1–12 are spoken; slides 13–15 are Q&A only.

## Slide 1: TalentRoute (00:00–00:26)

Hello everyone. I'm Mouza Aldarmaki, and this is my final project for MAAI 7101: TalentRoute. It helps a support coordinator prioritize learner reviews when staff time is limited. I'll explain the system, the experiments, and my recommendation.

Let me start with the decision.

## Slide 2: The decision belongs to the support coordinator (00:26–01:15)

The coordinator chooses which course cases receive a review, a shorter alert, or no action. OULAD does not record the university's actual support workflow, so the comparator is a transparent inactivity ranking. The scenario provides three hundred staff minutes per hundred cases. Reviews take thirty minutes and alerts two, as assumptions. Success means reaching later Fail or Withdrawn cases within this budget. I report action types and flags among successful cases separately. Contacting someone does not mean preventing failure.

Next, the data and timing.

## Slide 3: Early information, with explicit availability checks (01:15–02:04)

OULAD records real learning activity and final outcomes. Evaluation covers six thousand five hundred and eight course cases. The final model uses activity through day twenty-eight and enrolment context, but conservatively excludes assessment inputs because score timing is unknown. Submission-only features were not tested. I select candidates using learner-grouped folds within 2013B. The main evaluation removes shared training identities; an operational companion keeps mature past enrolments. Previously examined 2014B provides retrospective evidence. Previously examined 2014J stays excluded; it is not a fresh test.

Here is how the techniques connect.

## Slide 4: Two techniques feed one constrained queue (02:04–02:52)

Classification estimates Success, Fail and Withdrawn scores. I compare logistic regression, a constrained tree and boosting using training-only folds. Isolation Forest is the second technique: it ranks unusual engagement without invented anomaly labels. Its experimental route reserves existing review places; the classifier fills the remaining capacity. I keep anomaly percentiles separate from outcome scores. The default has no anomaly reserve because its added value is uncertain. Preprocessing fits training data only. Identities and demographics are excluded from prediction.

Did this improve the decision?

## Slide 5: A small observed gain, with uncertainty (02:52–03:38)

The final assessment-free classifier reaches thirty-nine point nine percent of adverse cases, compared with thirty-eight point six percent for inactivity. That is forty-two additional cases at the same workload. Average precision is point six six one; contact precision is sixty-seven point five percent. The paired coverage-difference interval crosses zero, so I cannot claim established superiority. These conditional intervals hold predictions and actions fixed. They do not include earlier search or prove future performance.

What did the second technique add?

## Slide 6: The anomaly reserve adds two adverse contacts (03:38–04:26)

The anomaly reserve changes eighty-three assignments. Five cases enter the contact list and five leave; four entering cases have adverse outcomes, while two adverse cases leave. The net gain is only two. Its paired interval crosses zero. Thirty-four alerts become reviews, which changes action type without necessarily reaching someone new. Isolation Forest also ranks adverse outcomes less well than inactivity. That is outcome relevance, not anomaly accuracy. I keep the failed acceptance result and recommend no reserve.

I also investigated three deeper questions.

## Slide 7: Three analyses sharpen the recommendation (04:26–05:14)

Three deeper investigations test the recommendation. Interleaving three rankings reaches fewer adverse cases than risk ranking alone. Among flagged cases, about one in three later succeeded; most flagged failures had no early score. A flag starts an investigation, not a diagnosis. Course specialists reach fourteen more adverse cases, but this exploratory finding does not justify deployment. GGG receives thirty-six point two percent of staff time for twelve point two percent of cases. Review this concentration before outreach.

Next, I tested the assumptions.

## Slide 8: Targeting changes with staffing assumptions (05:14–06:02)

I vary five assumptions: available time, review effort, reserve share, score cutoff and alert share. Across the budget sweep, the classifier's observed advantage over inactivity ranges from about zero point one to two point eight percentage points. These sweep estimates do not have confidence intervals. The classifier is deterministic, so unchanged seed-check coverage is expected; the anomaly result varies slightly. This is numerical stability on exposed data, not independent confirmation. Cutoff comparisons use the same eligibility gate for both queues.

What if reviews take longer?

## Slide 9: A feasible plan can fail when effort changes (06:02–06:52)

I freeze the final queue and increase review effort from thirty to forty-five minutes. Keeping every action would exceed capacity by eight thousand four hundred and fifty-eight minutes. An explicit contingency keeps original alerts first, then affordable high-risk reviews. It defers one hundred and eighty-eight cases and retains thirty-five point three percent coverage. Replanning gives thirty-seven percent. Both fit the budget. The contingency may defer a higher-risk review before a lower-risk alert, so it is an example, not an optimal workflow.

Now, the working assessment-free version.

## Slide 10: Explain, check and compare a support plan (06:52–08:16)

I select Assessment-free and the operational population. This model ignores all assessment fields. Staff costs remain assumptions.

The separate checker assesses a proposed plan. The original plan fits. Extra reviews exceed time and review places. It checks actions and scores, not outcomes.

I restore the original plan, save these settings, and raise the budget from three hundred to six hundred. Thirteen hundred actions change; six hundred and fifty additional cases enter the list. Budget changes affect actions, not predictions.

This is a feasible queue, not proof that support prevents failure.

What did the repairs change?

## Slide 11: Repairs apply to the entire final system (08:16–09:09)

Two repairs now apply throughout the report, app and analyses. Removing assessment features avoids uncertain score timing; removing submission features is a conservative choice. Selecting inside 2013B avoids directly choosing with evaluation outcomes. The matched audit reaches twelve hundred and fifty-eight adverse cases without assessments, versus thirteen hundred and fifty-seven with them. I accept this loss for availability, not better accuracy. Among contacted cases, predicted risk averages eighty-four percent, but observed adverse outcomes are sixty-seven point five percent. Scores support ranking, not verified individual probabilities. Earlier data exposure still prevents independent confirmation.

This leads to my recommendation.

## Slide 12: Use verifiable inputs and report the cost (09:09–09:44)

TalentRoute makes staffing trade-offs visible and produces a checkable queue. I recommend the assessment-free, risk-only version as a research demonstration. Its modest targeting gain is uncertain, so a simple inactivity comparator remains important. Before real outreach, agree actual effort, review course concentration, coordinate repeated learners and record support delivery. New independent outcomes and intervention evidence are still needed. Thank you.



Evidence: outputs/final_*.csv and outputs/availability_audit.csv. Presentation figures use the identity-disjoint comparison; the app demo uses the operational companion.
