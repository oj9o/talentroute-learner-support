# Development investigations

The offline evidence workspace (`review/investigations.html`) applies the Week 10 investigation pattern to actual OULAD development data: question, expected pattern, observed evidence, and interpretation limit. It supplements the canonical final report; it does not change its model or acceptance decision.

Run `just investigations` after preparing the data. This executes three seeded diagnostic studies and rebuilds the offline page. It needs no browser network dependencies. `just pipeline` also includes this step.

## Evaluation scope

These diagnostics were added after the recorded final evaluation. They use 10,412 training and 5,934 validation enrolments; final-test rows are filtered out before computing diagnostic statistics. They are exploratory, not independent confirmation or retrospective pre-registration. Final test metrics, source freeze and fitted final model remain unchanged.

## Questions and evidence

1. Learning curves compare logistic regression and the existing HGB configuration at 20%, 50% and 100% training size over three seeds. Subsamples are stratified by the real three-class outcome. For these learning curves, HGB early stopping is disabled at every sample size so the iteration budget is fixed; this diagnostic refit does not alter the final model. Preprocessing is fitted on each training subsample; the validation cohort is fixed. Training results are resubstitution results. Seed ranges are not confidence intervals. HGB validation adverse AP rises from 0.7308 to 0.7447 across the endpoints, suggesting some development benefit from the larger observed training cohort, without establishing future gains.
2. Single-feature HGB models are fitted on training rows and evaluated on validation rows. Inactivity is strongest at AP 0.6266, against validation adverse prevalence 0.4843. Strength motivates source/timestamp inspection; it neither proves nor excludes leakage. Timestamp allowlists and cutoff checks remain the primary safeguards.
3. A domain classifier distinguishes original training versus validation periods using predictor features only. Each of three evaluation splits groups by student identity. Mean ROC-AUC 0.7912 indicates detectable covariate differences, potentially including module composition. This does not establish concept drift or the cause of model error. The domain label is an observed split indicator, not a fabricated learner outcome.
4. The decision card links the previously recorded paired final comparisons. The detector's incremental coverage interval versus the ensemble alone crosses zero. The acceptance gate remains unmet.

The exact aggregate results, sample counts, seeds, protocol and source/data fingerprints are in `outputs/investigations/`. No individual learner records are exposed by this workspace. No label-noise correction is attempted: disagreement with a model is not evidence that an observed Fail or Withdrawn label is wrong.

## Inspiration

Saravanan Thirumuruganathan, MAAI7101 Week 10, *Debugging ML Models*: evidence-led diagnosis, rival explanations, fair comparisons and explicit deployment trade-offs. The workspace is an independent implementation rather than a copy of the teaching lab or its synthetic cases.
