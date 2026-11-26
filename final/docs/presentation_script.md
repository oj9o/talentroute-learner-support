# Presentation narration

TALENTROUTE — FINAL RECORDING SCRIPT
Planned duration: 09:44. 957 spoken words including transitions.
This is a pacing plan, not a measured recording. Full rehearsal required.
Slides 1–12 are spoken; slides 13–15 are backup only.

## Slide 1: TalentRoute (00:00–00:26)

Hello everyone. I'm Mouza Aldarmaki, and this is my final project for MAAI 7101: TalentRoute. It helps a support coordinator prioritize learner reviews when staff time is limited. I'll explain the system, the experiments, and my recommendation.

Let me start with the decision.

## Slide 2: The decision belongs to the support coordinator (00:26–01:15)

The coordinator cannot review everyone. The decision is who receives a review, a shorter alert, or no action. Adverse means later Fail or Withdrawn; coverage is the proportion of these cases selected. I compare against inactivity ranking, a simple alternative, not an observed university workflow. The scenario allows three hundred staff minutes per hundred cases, assuming thirty minutes per review and two per alert. Better targeting means reaching more adverse cases within the same budget, not proving prevented failures.

Next, the data and timing.

## Slide 3: Early information, with explicit availability checks (01:15–02:04)

OULAD is the Open University Learning Analytics Dataset. The main comparison uses three thousand nine hundred and one training cases and six thousand five hundred and eight evaluation cases. A case is one course enrolment. Inputs stop at day twenty-eight; assessment scores are excluded because release timing is unverified. Selection stays within learner-grouped 2013B folds. Previously examined 2014B provides retrospective evidence. The archive disclosed prior 2014J use; this revision excludes it and cannot claim an untouched test.

Here is how the techniques connect.

## Slide 4: Two techniques feed one constrained queue (02:04–02:52)

Classification fits the recorded outcomes: Success, Fail and Withdrawn. Logistic regression provides a simple model; trees and boosting test nonlinear patterns. Isolation Forest looks for unusual engagement that outcome ranking might miss, without invented anomaly labels. Its experimental route takes existing review places; classification fills the remaining capacity. Anomaly ranks and outcome scores stay separate. Both techniques affect one queue, but the default reserve is off because benefit is unestablished. Preprocessing fits training data only; identities and demographics are excluded.

Did this improve the decision?

## Slide 5: A small observed gain, with uncertainty (02:52–03:38)

The classifier selects thirty-nine point nine percent of adverse cases, versus thirty-eight point six percent for inactivity: forty-two additional cases at the same workload. Average precision measures ranking quality and is point six six one. Contact precision is sixty-seven point five percent: the proportion of selected cases with adverse outcomes. The paired interval crosses zero, so improvement is unconfirmed. These intervals hold predictions fixed; they exclude earlier search and do not prove future performance.

What did the second technique add?

## Slide 6: The anomaly reserve adds two adverse contacts (03:38–04:26)

The anomaly reserve changes eighty-three assignments. Five cases enter the contact list and five leave; four entering cases have adverse outcomes, while two adverse cases leave. The net gain is only two. Its paired interval crosses zero. Thirty-four alerts become reviews, which changes action type without necessarily reaching someone new. Isolation Forest also ranks adverse outcomes less well than inactivity. That is outcome relevance, not anomaly accuracy. The two-point precision margin passes, but the improvement gate fails. I recommend no reserve.

I also investigated three deeper questions.

## Slide 7: Three analyses sharpen the recommendation (04:26–05:14)

First, cross-model reconciliation alternates between three rankings under one quota. It reaches fourteen fewer adverse cases, so I keep risk ranking. Second, challenge-set analysis examines flagged cases by actual outcome. About one in three later succeeded: a flag requires investigation, not a diagnosis. Third, segment analysis tests course-specific models and workloads. Specialists add fourteen adverse cases, but this exploratory gain does not justify replacement. GGG receives disproportionate staff time, so course concentration needs review before outreach.

Next, I tested the assumptions.

## Slide 8: Targeting changes with staffing assumptions (05:14–06:02)

I vary five staffing and eligibility assumptions. Budget-sweep gains range from zero point one to two point eight percentage points, without sweep intervals. A supplementary nested check repeats selection within 2013B. Every fold chose logistic regression, with different penalties. Together, the queues reached eighty-one more adverse course cases than inactivity at equal capacity. This uses the same cohort and courses. It does not replace the weaker later-cohort result or provide independent confirmation. Full results are in the appendix.

What if reviews take longer?

## Slide 9: A feasible plan can fail when effort changes (06:02–06:52)

I freeze the final queue and increase review effort from thirty to forty-five minutes. Keeping every action would exceed capacity by eight thousand four hundred and fifty-eight minutes. An explicit contingency keeps original alerts first, then affordable high-risk reviews. It defers one hundred and eighty-eight cases and retains thirty-five point three percent coverage. Replanning gives thirty-seven percent. Both fit the budget. The contingency may defer a higher-risk review before a lower-risk alert, so it is an example, not an optimal workflow.

Now, the working assessment-free version.

## Slide 10: Explain, check and compare a support plan (06:52–08:16)

I select Assessment-free and the operational population. This model ignores all assessment fields. Staff costs remain assumptions.

The separate checker assesses a proposed plan. The original plan fits. Extra reviews exceed time and review places. It checks actions and scores, not outcomes.

I restore the original plan, save these settings, and raise the budget from three hundred to six hundred. Thirteen hundred actions change; six hundred and fifty additional cases enter the list. Budget changes affect actions, not predictions.

No action can mean no capacity. Human review is still needed before outreach.

What did the repairs change?

## Slide 11: What failed, what changed, and why (08:16–09:09)

I removed assessment inputs because score timing is unverified, accepting lower targeting. Model selection now stays inside training folds. I also tested temperature scaling within 2013B, separating model training, calibration and assessment learners. The probability metrics barely changed, with two fewer adverse cases contacted. I kept the original model. This does not fix later course-level calibration gaps, so scores support ranking, not verified personal probabilities. The promised investigations remain, including unsuccessful alternatives. These changes do not restore an untouched test.

This leads to my recommendation.

## Slide 12: Use verifiable inputs and report the cost (09:09–09:44)

My recommendation is an assessment-free queue for inspection, with no default anomaly reserve. Keep inactivity as a comparator. If effort changes, recheck and replan. Review course concentration and coordinate repeated learners before outreach. The promised experiments are documented, including unsuccessful alternatives and their reasons. Historical targeting does not prove prevented failures. Independent confirmation and measured intervention outcomes remain necessary before adoption. Thank you.


