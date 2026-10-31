# Exploratory experiment register

All entries below were introduced after the original validation evidence was visible. None is confirmatory; final-test metrics remain unused. No best subgroup, layer order or seed may be selectively reported.

- Original reference: logistic and three hgb configurations; weights 0/.1/.2/.35/.5. Preserved.
- Revision: fixed-depth Decision Tree, fixed Random Forest, module logistic hybrid with training-only eligibility 300 rows / 30 per class.
- Corrected: observed-outcome action_break_even.csv; five relative-effectiveness multipliers, six target alert fractions, four alert caps; near-full-budget filter and original mix. Values are hypothetical weighted targeting units, not benefits.
- Historical layer diagnostic: one fixed round-robin order, stable ties.
- Corrected layer sensitivity: all 24 orders, three fixed seeds, shares 0/.5/.75/.9/1; same total flag quota, outcome-specific escape.
- Tie sensitivity: five seeds across six score definitions, including original business rule and tree.
- Segments: n>=50/adverse>=10; each outcome PR-AUC suppressed when positives or negatives <10.

Current model reference remains original hgb; no claim of winning an expanded search. Paired model intervals are complete. Mac and Ubuntu VM execution are verified; final-test settings freeze is future work.

- Labs 9/10 diagnostics: training/validation ladder, ten shuffled-training-label controls, five grouped permutations per feature family, baseline paired interval and an evidence fingerprint. Added after original validation; no labels are corrected and no new candidate is selected from these diagnostics.
