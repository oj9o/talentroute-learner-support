# Exploratory experiment register

Original development selection used logistic/three HGB configurations and blend weights 0/.1/.2/.35/.5. Later comparisons are exploratory, not independent confirmation. A separate final candidate was subsequently frozen and evaluated on 2014J; the new diagnostics do not reset that history.

- Classification alternatives: constrained tree, forest and module-logistic hybrid; training-only specialist eligibility requires 300 rows and 30 observations per class.
- Layer experiment: all 24 orders, three seeds and classifier-first shares 0/.5/.75/.9/1 under equal total quota.
- Segments: minimum 50 observations/10 adverse cases; outcome PR-AUC also needs 10 positive and negative cases.
- Diagnostics: train/validation ladder, ten shuffled-label controls, grouped permutation, three-fraction/three-seed learning curves, individual-feature probes and student-grouped period discrimination.
- HGB learning curves disable early stopping for a fixed iteration budget. No labels are corrected.
- Action-effectiveness multipliers are hypothetical sensitivity assumptions, not measured treatment benefits.

All tested settings and negative findings remain visible. Historical platform evidence verifies its named snapshot; current-run evidence is separate.
