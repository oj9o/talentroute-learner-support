# A 90-second decision demonstration

Use the existing app within the ten-minute presentation; replace the previous app segment rather than extending the presentation.

1. **0:00–0:20 — Explain.** Select the operational population, Assessment-free model (selected within 2013B), risk-only route, 300 minutes per 100 cases and 0% model score cutoff. Open “Why does this plan fit?” Read the actual used/available minutes and review/alert limits. Say: “The coordinator sets the available staff time. The model ranks risk; this policy turns rankings into course-case actions. The costs are scenario assumptions.”
2. **0:20–0:45 — Check.** Open “Try your own plan.” Check the unchanged plan, then choose “Try extra reviews” and check again. Point to the failed time and review-place rules. Say: “A separate checker tests the proposed actions directly, without using the later outcomes. A plan can look reasonable and still exceed capacity.” Restore the plan.
3. **0:45–1:15 — Compare.** Save current settings as Before, change minutes per 100 cases from 300 to 600 and update. Open the comparison. Read its actual changed-action, entry and workload counts and inspect course composition. Say: “More time changes who receives review or an alert. It does not change their model probabilities or prove that a failure is prevented.”
4. **1:15–1:30 — State limits.** Say: “This is a development demonstration on 2014B. The already examined 2014J cohort is not a new independent test. We need prospective workflow and outcome evidence before deployment.”

Optional Q&A: raise the model score cutoff to 95%, then request extra reviews for the displayed examples. The checker rejects below-threshold cases even when spare minutes remain. At zero budget, every action must be No action. Returning to the original settings restores the original deterministic queue.

## What the checker means

It separately calculates the declared caps from the number of course cases, time budget, initial alert reservation and action costs. It verifies whole, mutually exclusive actions, total minutes, review/alert counts and risk eligibility. It does not verify that a manual plan follows the recommender's risk ordering or reserve route, and does not claim that a feasible plan is best. Small arithmetic fixtures include an exactly full budget, an extra action and below-threshold selection; integration checks also cover the generated queue.

The two ML families remain classification and anomaly detection. These decision tools are not a third ML family. The detector's incremental gain remains unproven; its reserve is experimental. The comparison shows selected course cases, not deduplicated person-level outreach or monetary benefits. Manual edits stay separate from exports and historical targeting metrics.
