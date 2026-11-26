# Probability-correction experiment

Written before this experiment's first execution on 26 November 2026, after
previous development findings. This is not a preregistration or independent test.

Use only 2013B and the existing assessment-free features and six candidates.
Keep the three-class outcome and existing staffing policy. Within each of the
existing three learner-grouped outer folds, reserve one third of outer-training
learners for calibration (fixed seed 7105). Select and fit the classifier using
only the remaining learners, with the existing grouped inner selection. Fit a
single temperature on calibration labels by multiclass log loss, bounded to
[0.25, 4]. Compare raw and corrected probabilities on the same outer-assessment
learners, with the identical fitted base model and budget. Report all folds,
multiclass log loss, adverse Brier score, ranking and decision coverage. Check
calibration plots before any later operational probability claim.

Do not choose a new temperature method, bounds, threshold or split after seeing
results. Do not refit on calibration data after fitting the correction. Do not
score 2014B or 2014J. No fitted application model is overwritten. Even improved
outer-fold performance here does not justify claiming independent confirmation
or validated probabilities on a later cohort. Multiclass temperature scaling
preserves the most likely class, but can change ranking of combined Fail plus
Withdrawn risk; decision outcomes must therefore also be reported.

## Interpretation added after execution

The protocol fixed the experiment and reporting metrics, but did not set a numerical adoption threshold. The decision to retain the default is a post hoc conservative interpretation. Tiny opposing changes in log loss and adverse Brier do not demonstrate useful benefit or harm. This development-only diagnostic within 2013B cannot establish correction of later course-specific calibration gaps.
