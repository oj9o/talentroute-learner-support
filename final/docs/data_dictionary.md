# Inputs and decision-time meaning

One row is one student–module–presentation enrolment. Raw OULAD data are downloaded from the pinned public UCI archive under CC BY 4.0. IDs are used only to join records, audit overlap and cluster uncertainty estimates. They are not model features or exported queue fields.

| Field | Why it makes sense for these data | Limit |
| --- | --- | --- |
| Early and late clicks, transformed with log(1+x) | Counts describe observed engagement; transformation reduces domination by very large counts | Different activity types need different effort; clicks are not learning |
| Total log clicks | Overall early activity | Correlated with early/late counts; no independent causal interpretation |
| Days since last observed activity | Flags prolonged absence from the platform | No activity maps to the complete observed window plus one; offline study is invisible |
| Late minus early log clicks | Describes a shift in activity between windows | Unequal windows: not a normalized daily trend |
| Mean/minimum available assessment score | Early demonstrated performance | Actual marking-release dates are absent; assumed delay only |
| Submitted assessment count and missing indicator | Distinguishes evidence availability from low scores | Course schedules differ; absence can be normal |
| Late-submission fraction | Describes timeliness among available submissions with known deadlines | Unknown deadlines are excluded from this fraction; it is missing if none are known |
| Credits studied and previous attempts | Known study load and prior course attempts | Associations do not establish causes |
| Module | Accounts for course-specific context | Unknown evaluation modules receive no learned module category |
| Success / Fail / Withdrawn | Observed final_result; Pass and Distinction map to Success | Evaluation label, excluded from input features |
| Gender, prior enrolment, unseen module | Group audits and comparison of generalization settings | Excluded from predictions; no causal demographic inference |

Imputation and categorical encoding fit training only. Logistic and detector preprocessing includes scaling; tree classifiers retain the imputed numeric scales. Isolation Forest receives engagement features only. No PCA, t-SNE, clustering, feature selection on evaluation data, or artificial outcome generation is used. The app's edits are synthetic *inputs* for model-response inspection; they never create labels or join the observed evaluation cohort.
