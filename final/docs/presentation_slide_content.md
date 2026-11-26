# Presentation slide content

Slides 1–12 accompany the narration; slides 13–15 are backup evidence.


## Slide 1

TalentRoute

Learner support under limited staff time

Mouza Aldarmaki

MAAI7101 · Final project demonstration


## Slide 2

The decision belongs to the support coordinator

Educational consulting for university learner support

Who decides?

The coordinator sets
capacity and approves
real-world contact.

What changes?

Review, shorter alert,
or no action for each
course-enrolment case.

What limits the plan?

300 minutes
per 100 cases

30 min / review

2 min / alert

20% alert case cap

Measure adverse cases reached, action mix and flags among later-successful learners

Proposed workflow and effort assumptions. The baseline is a constructed inactivity ranking, not measured university practice.


## Slide 3

Early information, with explicit availability checks

OULAD records real final outcomes. Adverse means Fail or Withdrawn.

2013B

Earlier mature outcomes
3,901 training cases
Identity-disjoint comparison

2014B

Day-28 development cohort
6,508 cases · 6,215 people
3,151 adverse outcomes

2014J

Prior use disclosed in archive
Excluded from this revision
No independent confirmation

Final inputs: day-28 activity and enrolment context.
Conservatively exclude assessments; submission-only variant untested.

Preserve the archived test boundary; disclosure does not waive evaluation requirements

Calendar bounds and result-release delays are audited. Actual score and final-result publication timestamps are not available.


## Slide 4

Two techniques feed one constrained queue

Classification and outlier detection share a real capacity constraint

Inputs

Day-28 activity
Enrolment context
No assessment inputs

Classifier

Outcome probabilities
Logistic / tree / boosting

Isolation Forest

Unusual engagement rank
Experimental review reserve

Capacity

Separate routes
No score blending
No extra reserve budget

Case queue

Review
Alert
No action

Test the second technique against the same classifier alone, at equal capacity

All transformations fit training data only. Anomaly percentiles are not outcome probabilities. Human approval remains outside the model.


## Slide 5

A small observed gain, with uncertainty

Final assessment-free comparison · 564 reviews and 1,301 alerts

+42

additional adverse cases
reached versus inactivity

AP 0.661
Contact precision 67.5%

Gain +1.33 points [−0.19, +2.78]. The original improvement gate is not met.

Previously examined 2014B; identity-disjoint comparison. Operational companion: 1,257 adverse cases. Conditional intervals omit fitting and search uncertainty.


## Slide 6

The anomaly reserve adds two adverse contacts

Final assessment-free experiment · later-successful reviews: 108 risk-only, 112 anomaly

83

action assignments changed

5 in / 5 out

cases enter and leave
the contact set

34

alerts become reviews

Adverse cases reviewed: 456 risk-only, 452 anomaly

Gain interval [−0.10, +0.22] crosses zero: improvement gate fails. Keep reserve off.

Gate: positive paired gain and precision loss ≤2 points. Precision passes; gain does not. Outcome AP: IF 0.595, inactivity 0.627; not anomaly accuracy.


## Slide 7

Three analyses sharpen the recommendation

The three intermediate commitments are executed; findings guide the choice

Investigation	Finding on examined 2014B	Decision implication
Cross-model reconciliation	1,244 adverse cases
Risk queue: 1,258	Keep one risk queue
Warning-positive profiles	607 / 1,865 later succeeded
Early score: 165 / 835 Fail cases	A flag starts investigation,
not diagnosis
Course specialists / segments	1,272 vs 1,258 adverse cases
Exploratory, not pre-selected	Keep global model;
seek new evidence

GGG receives 36.2% of staff time for 12.2% of cases. Review course concentration.

Assessment scores describe observed subsets only; they never enter the final model.


## Slide 8

Targeting changes with staffing assumptions

Final assessment-free classifier versus inactivity at matched staffing assumptions

3 outer folds

2013B nested selection
+81 adverse cases reached

Same cohort and courses.
Logistic chosen in every fold.
No independent confirmation.

Budget-sweep gains: +0.10 to +2.82 points. Sweep uncertainty was not estimated.

Score-cutoff comparisons share the classifier eligibility gate. Some controls do not bind.


## Slide 9

A feasible plan can fail when effort changes

Final assessment-free queue · review effort rises from 30 to 45 minutes

8,458 min

shortfall if the original
list is kept in full

188 cases deferred

Both feasible alternatives stay within 19,524 minutes. Neither is an optimal intervention policy.

The example contingency keeps original alerts first, then reviews. It can retain lower-risk alerts while deferring higher-risk reviews.


## Slide 10

Explain, check and compare a support plan

Live demo: Assessment-free · operational population · classifier-only route

1   Explain the rules

Assessment-free is the default
Confirm the operational population and costs

2   Check a proposed plan

Extra reviews can exceed time and places
Separate policy checker; no outcomes

3   Compare before and after

300 to 600 minutes per 100 cases
1,300 changed actions; 650 new contacts


## Slide 11

What failed, what changed, and why

Implemented experiments and established benefits are reported separately

Experiment / concern	Result and chosen alternative
Unknown score-release dates	Remove assessments; accept lower targeting
Matched audit: free / enabled	1,258 / 1,357 adverse contacts at equal capacity
Anomaly blend and reserve	Separate ranks; no default reserve: gain unestablished
Model selection after development	Select within 2013B; prior exposure remains
Temperature scaling within 2013B	Useful gain not established; not adopted

Keep the promised investigations. Explain negative results and the alternative chosen.

Appendices B/C link commitments and experiments to evidence. Later-cohort calibration remains unresolved.


## Slide 12

Use verifiable inputs and report the cost

Unverified score timing?
Keep assessment-free inputs

When the decision needs review

Effort changes → recheck the plan
Course concentration → inspect allocation
Before outreach → coordinate learners

New, unseen outcomes
are still required

No proven reserve benefit → keep it off.
No action can mean capacity ran out, not safety.


## Slide 13

Feature choices follow the learning context

Supporting detail for questions

A1

Feature group	Why it makes sense	Limit to explain
Activity and recency	Captures recorded engagement	Clicks do not prove learning
Early assessment summaries	Reflects available performance	Original only; omitted in assessment-free mode
Missingness and lateness	Keeps unavailable evidence visible	Assessment-derived fields omitted in assessment-free mode
Course and previous attempts	Adds learning context	New courses can behave differently
Excluded predictor fields	IDs, outcomes and protected fields	Gender is audit-only

Assessment-free mode drops all five assessment-derived features. Activity and enrolment context remain; fit transformations on training only.


## Slide 14

Nested selection check within 2013B

One retrospective partition of the same cohort and courses: BBB, DDD and FFF

A2

Outer fold	Selected model and coverage	Inactivity coverage
1 (1,373 cases)	Logistic C=1: 44.0%	39.0%
2 (1,372 cases)	Logistic C=10: 42.8%	40.6%
3 (1,373 cases)	Logistic C=10: 43.0%	38.2%
Procedure	3 inner grouped folds choose model	3 outer grouped folds assess

Pooled: 876 / 2,025 versus 795 / 2,025 adverse cases. Equal contact capacity.

4,118 cases / 4,116 learners. Designed after 2014B review. No temporal or new-course test.


## Slide 15

Action values and subgroup questions

Supporting detail for questions

A3

−7.70

anomaly preference-unit difference

Conditional interval [−31.77, +19.00]
Declared weights, not treatment effects or ROI.

48.1% / 34.5%

female / male adverse coverage

Contact precision: 60.1% / 76.1%
Course mix and denominators matter.

CCC coverage: 50/164 female versus 211/671 male adverse cases. Intervals overlap.

Within-course gender counts and intervals are descriptive audits, not proof of a causal demographic effect or a fairness guarantee.
