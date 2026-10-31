> Intermediate development record. Final held-out evidence and conclusions are in `final_report.md`.

# Development findings — not final-test claims

- business_rule: adverse coverage 0.4137; flag precision 0.6994. Source: validation_decision_metrics.csv.
- classifier_only: adverse coverage 0.4579; flag precision 0.7741. Source: validation_decision_metrics.csv.
- coupled_selected: adverse coverage 0.4624; flag precision 0.7818. Source: validation_decision_metrics.csv.
- coupled_fixed_020: adverse coverage 0.4624; flag precision 0.7818. Source: validation_decision_metrics.csv.

## Frontier
```csv
value,adverse_coverage,flag_precision,staff_minutes
150.0000,0.3288,0.8348,8900.0000
300.0000,0.4624,0.7818,17792.0000
600.0000,0.5755,0.7213,35582.0000
```
Recommendation: increasing capacity increases the number flagged; select an operating point only if added workload and marginal relevance are acceptable. This is not an estimate of prevented outcomes.

## Uncertainty
```csv
policy,adverse_coverage,flag_precision
coupled_selected,0.4624,0.7818
uncertainty_priority_exploratory,0.4576,0.7735
```
Recommendation: retain uncertainty prioritization only if it earns a validation benefit and survives final confirmation; entropy is not calibrated epistemic uncertainty.

## Challenge set
```csv
group,n,adverse_coverage,fail_coverage,withdrawn_coverage,flag_precision
0,2737,0.3358,0.2868,0.4072,0.7546
1,3197,0.5408,0.5702,0.4863,0.7927
```
Recommendation: audit the no-assessment pathway before deploying an assessment-led policy. Differences are descriptive and do not establish discrimination or causality.

## Added-layer recommendation
The validation search retained a nonzero outlier contribution, but the paired interval must exclude zero before asserting evidence of improvement. Prefer the simpler policy operationally while this remains unconfirmed. Check the separate Fail/Withdrawn tradeoff, not just the pooled coverage.

Outcome-specific coverage changes from adding the selected anomaly blend: {'fail_coverage': 0.018826135105204922, 'withdrawn_coverage': -0.0196629213483146}. Source: validation_decision_metrics.csv. An aggregate improvement can conceal deterioration for one outcome; stakeholder priorities must be declared before final testing.

## Availability assumptions
```csv
cutoff_day,score_delay_days_assumed,model,n,no_assessment_rate,adverse_coverage
21,7,logistic,5983,0.7968,0.4160
21,7,hgb_15_10,5983,0.7968,0.4297
28,0,logistic,5934,0.3241,0.4715
28,0,hgb_15_10,5934,0.3241,0.4732
28,7,logistic,5934,0.5388,0.4283
28,7,hgb_15_10,5934,0.5388,0.4579
28,14,logistic,5934,0.7952,0.4335
28,14,hgb_15_10,5934,0.7952,0.4391
35,7,logistic,5864,0.3223,0.4748
35,7,hgb_15_10,5864,0.3223,0.4783
```
Compare policies within each scenario: changing the cutoff changes both information and eligibility. No raw cross-scenario gain is treated as causal or pure model improvement.

## Strong detector baseline
```csv
detector,proxy_adverse_pr_auc,adverse_coverage,flag_precision
isolation_forest,0.5899,0.3553,0.6006
inactivity_rule,0.6300,0.3876,0.6553
```
In this run: Proxy adverse PR-AUC: inactivity 0.6300, Isolation Forest 0.5899. Do not deploy the complex detector merely because it is more sophisticated. Investigate score direction and module/observability shift before a final candidate is frozen. Outcome relevance is not verified anomaly ground truth.

## Swiss Cheese escape diagnostic
```csv
outcome,n,both_flag,classifier_only_flag,anomaly_only_flag,escape_both
Success,3060,81,303,598,2078
Fail,1806,375,436,355,640
Withdrawn,1068,179,326,112,451
```
Each layer has its own warning quota. The diagnostic union exceeds the original policy quota, so it must not be reported as a feasible policy improvement. The coupled policy comparison remains the valid same-budget result.
