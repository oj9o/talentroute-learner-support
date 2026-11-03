# Data dictionary and availability

Source: official OULAD CSV tables, cited in README. Keys are module, presentation, student; assessment IDs join submissions to module/presentation. Enrolment keys must be unique. No synthetic training observations are inserted.

- `target`: final_result maps Pass/Distinction to Success; Fail and Withdrawn stay distinct. Label only.
- `code_module`: course identifier, categorical model input. An unseen module is a domain-shift challenge, not an error to silently impute.
- `code_presentation`, `split`: temporal partition metadata, not model inputs.
- `id_student`: grouping/audit key only. Earlier records of later-partition students are purged.
- `date_registration`: eligibility at cutoff; unknown dates exclude the record.
- `date_unregistration`: excludes already withdrawn records at cutoff; later values never enter model features. Missing withdrawal dates are treated as still eligible; adverse-outcome records with unknown dates need an eligibility caveat.
- `score_mean`, `score_min`: observed non-banked/non-exam scores, submissions by cutoff minus assumed score lag. Missing scores remain missing for training-fitted median imputation with missing indicators. Submission date is not evidence of grading date.
- `submitted_count`: count of qualifying assessment IDs, zero if none. A submission can exist with a missing score; absence of submissions and absence of scores are distinct.
- `late_rate`: fraction submitted after assessment due date among qualifying submissions. Missing when no such submission.
- `no_early_assessment`: true when no qualifying early submission exists; used as a challenge segment and predictor.
- `studied_credits`, `num_of_prev_attempts`: recorded enrolment load/prior study history. Assumed known at enrolment; validate deployment availability.
- `clicks`, `early_clicks`, `late_clicks`: VLE sum_click counts over days 0–cutoff, 0–14, 15–cutoff respectively. No observed activity gives zero; this can also reflect incomplete logging.
- `log_clicks`, `log_early_clicks`, `log_late_clicks`: log1p of those counts for stable scales.
- `inactive_days`: cutoff minus last observed VLE day; no activity uses cutoff+1, explicitly representing inactivity rather than a future event.
- `engagement_change`: log1p late minus log1p early clicks. Even at day 28, inclusive windows contain 15 versus 14 days. When cutoff changes, the windows also differ in length; comparisons are within a scenario and not an equal-duration trend claim.
- `gender`, `disability`: audit-only aggregate slices; never model inputs. Small groups receive no inferential fairness conclusions.
- `region`, `highest_education`, `imd_band`, `age_band`: retained raw metadata, excluded by model predictor allowlist.
- `last_day`, `final_result`: engineering/audit metadata and source outcome, excluded from model inputs except the explicitly computed inactivity feature.

The CSV lists roles, dtypes and transformations, including detector output (not an observed anomaly label). '?' denotes source missingness. Checksums pin data; training-only preprocessing and identity purging prevent leakage.
