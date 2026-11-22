# Final protocol and experiment history

The final system is assessment-free. Candidate selection uses three learner-grouped folds within 2013B; preprocessing is refitted inside every fold. Model selection does not use 2014B labels. The grid reflects earlier project work, and 2014B has previously been examined, so evaluation is retrospective. The app defaults to this model. All `final_*.csv` analyses use it, including the specialists, route ablations, five sensitivity sweeps and seed checks. The policy is unchanged; no new sweep winner is adopted. The earlier procedure below is retained as a labeled experiment history, not the current selection procedure.

## Historical development procedure (superseded for final recommendation)

# Development revision after Intermediate feedback

This revision builds on TalentRoute's submitted data processing, three-class
classification, engagement outlier detection and constrained support allocation.
The submitted Intermediate and its existing numbers are historical records.
New results use development data and are exploratory. The previously evaluated
2014J cohort is not an unseen test; this revision will not score it.

## Calendar availability before modeling

OULAD identifies presentation start months, not exact calendar start days or
final-result publication dates. The calendar audit uses the entire month as a
date interval and both possible duration-count conventions. Release delays of
0, 30 and 60 days are assumptions. Course completion is not proof of result
publication. Early withdrawal labels do not make all final outcomes available.

Source: [UCI OULAD](https://archive.ics.uci.edu/dataset/349/open+university+learning+analytics+dataset),
with durations from the pinned courses.csv. Reproduce with `just calendar-audit`.

The new development experiment uses 2013B training and 2014B evaluation under
the stated availability assumption. An identity-disjoint companion removes
overlapping 2014B identities from training. An operational companion retains
past training enrolments and reports returning learners separately. Returning
means an earlier enrolment is recorded, not a failed course. Neither population
is chosen using future 2014J membership. All preprocessing and the detector fit
training records only. Future outcomes and identity/demographic columns remain
excluded from model inputs. Explanations will disclose unseen courses and any
population differences from the submitted benchmark.

## Fixed development comparisons

Classifier candidates retain logistic regression, a constrained decision tree
and histogram boosting with the submitted settings. The bounded follow-up rule below chooses a provisional development candidate;
independent final confirmation remains unresolved. Isolation Forest remains the second
technique family. Its ranking is not interpreted as an outcome probability.

At each common budget, using the selected classifier, compare classifier-only routing with a separately
reserved review quota ranked by the detector, inactivity, course round-robin
or seeded random order. Review and alert counts stay matched for these route
comparisons. The quota comes out of the existing human-review capacity. Alerts
use the classifier order among remaining uncontacted cases. There is no sum of
probability and anomaly percentile. Quotas 0%, 10%, 20% and 30% are scenarios,
not independent confirmation of the best selected value.

Keep the three promised investigations: equal-quota model reconciliation,
warning-positive outcome profiles, and course/learner segments. Add operational
returning-learner results, queue composition by course, within-course gender
audits with denominators, and action-specific workload/targeting outcomes.

Action-value scenarios use declared preference units, separate review/alert
burdens and Fail/Withdrawn values. They are conditional assumptions, not measured
intervention effects, prevented failures or ROI. A historical Success flagged
by a model is not evidence that assistance would be unnecessary or harmful.

Independent final confirmation of a revised system remains unresolved. A new
freeze does not erase earlier exposure to 2014J; any instructor-approved reuse
must still be labeled non-independent. No instructor message or LMS action is
part of this development pipeline.

## Implementation clarifications

### Bounded follow-up selection recorded on 9 November 2026

After reviewing the existing development results, extend logistic regularization
to C = 0.1, 1 and 10. Keep the existing tree and two boosting capacities. This
is an explicitly post-feedback development search, not a preregistration or an
independent validation claim. Do not extend the grid in response to its result.
Fit on 2013B only. Select the provisional risk-queue candidate by highest 2014B
identity-disjoint coverage at the unchanged default staffing policy, then adverse
average precision, then the listed candidate order. Report the operational
companion and seen/unseen courses without selecting a separate subgroup model.
No decision costs, thresholds or reserve sizes are optimized. Evaluate the
detector reserve against this candidate as well as the fixed boosting reference;
retain the original positive paired-difference and precision-loss gates. A
failed gate means no evidence to recommend the reserve, not permission to change
the gate. All decisions remain provisional pending independent confirmation.

The Linux check exposed differences in fitted boosting predictions across CPU
platforms while linear/tree predictions and data checks matched. Remove
unnecessary scaling from tree-based classifiers and check again; retain an
explicit platform-stability result if differences remain. This is a numerical
robustness change, not a search for a higher validation score.

The initial design was written before these development fits, but was not committed as a public preregistration. It must not be described as one. The original routing reference was hgb_15_10. The historical follow-up selection supplied the model used by the earlier unprefixed route, subgroup, sensitivity and deeper analyses; hgb_15_10 remains a comparator. The detector is fitted on numeric engagement features. Boosting uses explicitly disabled early stopping and imputation without unnecessary scaling; empty numeric columns are retained by the imputer. Course specialists are an exploratory execution of the existing commitment.

The identity-disjoint companion is an evaluation design using evaluation identity membership. The operational companion is the deployment-relevant population comparison. Earlier registration must be known by the earliest possible decision date; unknown registration dates do not establish history. Evaluation is on enrolments, not unique people. Student-cluster resampling accounts for repeated identities in intervals, but contact costs remain per case, so operational outreach requires coordination.

The single-case experiment changes only model inputs and displays fitted-model responses. It neither estimates a causal effect nor assigns a fabricated outcome to edited inputs. The historical evaluation remains unchanged by these experiments.

### Follow-up diagnostics recorded on 18 November 2026

These bounded checks were written locally before their first run, after earlier
development findings were known. This is not a public preregistration. Neither
check changes the chosen model, feature definitions or recommended route.

1. Separate selection from assessment within the already examined 2014B cohort.
   Keep the six 2013B model fits fixed. Use 50 repeated random 50/50 partitions
   of distinct students, seed 7104, retaining every student's course cases in
   one half. Select on one half with the existing coverage/AP/order rule and
   assess that winner on the other, against the constructed rule, fixed C=1
   logistic and the same winner with an anomaly reserve. Allocate the unchanged
   per-100 budget separately in each half. Audit course composition and unseen
   course shares rather than treating a multi-course student as separate groups.
   Report model/family selection frequencies and empirical spread, not confidence
   intervals. The overlapping partitions are not independent; they do not undo
   earlier development exposure or measure future-cohort generalization. The
   contrast with fixed logistic is a comparator difference, not an estimate of
   selection optimism. No revised 2014J scoring is permitted.
2. Stress an already allocated queue with review effort multipliers 1, 1.5 and
   2, and alert effort multipliers 1 and 1.5. Freeze membership before applying
   each cost scenario. Report required minutes, shortfall and feasibility. For
   an explicit contingency, retain the highest-risk original alerts first,
   then highest-risk original reviews within the remaining time; defer all
   remaining cases without converting their action types. Compare observed
   targeting with a newly allocated queue under the same stressed costs. This
   contingency is a declared example, not an optimal or approved workflow.
   Costs remain assumed, not observed. No treatment benefit is inferred.

The final temporal evaluation requirement remains unresolved. These diagnostics
are additions to development evidence, not substitutes for independent final
confirmation.
