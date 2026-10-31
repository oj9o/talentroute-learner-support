# Mouza Al Darmaki · MAAI7101

# TalentRoute — Final evaluation release

An educational consulting team serving universities or learning providers uses this experiment to prioritise learner-support reviews and alerts within staff time. OULAD supplies actual learner outcomes; this is not a full learning-plan platform or evidence that contacting a learner prevents failure.

## Run

Requirements: `uv`, `just`, Python 3.14, Mac/Linux CPU. No GPU, account, API key or external model-service call is needed. Initial dependency installation requires network unless cached. Bundled raw data support offline subsequent execution.

```sh
just install
just pipeline
just app 150
just app 600
```

`just pipeline` verifies/downloads data, prepares features, runs Intermediate baselines, EDA and committed development analyses, trains the fixed final candidate, freezes hashes before held-out scoring, evaluates, produces ablation/sensitivity evidence, generates the final report and tests. Runtime is recorded in `outputs/final/runtime.json`; installation and first network download are separate. Target: under 30 minutes excluding network transfer.

Final report: `docs/final_report.md`, ten required sections. `just final-report` regenerates it from saved outputs. `just deep-dives` runs the three committed development analyses; `just ablation` produces held-out component comparisons and plots; `just sensitivity` includes the frozen candidate's validation scenarios and seed checks plus data-availability assumptions. `just evaluate` reuses completed frozen test results. `just run-model` trains before evaluation and deliberately refuses retraining after test scoring. This refusal protects the release from silent retuning. Do not delete a completed freeze to search for a better test result.

The offline artifact is a CLI ranked list. `just app <budget>` changes staff minutes per 100 learners, shows reviews/alerts/no action and actual effort, and saves `outputs/final/demo_worklist.csv` with synthetic references. Its cohort is validation, clearly labelled. It demonstrates the frozen experimental candidate, not an approved production policy. Acceptance is recorded separately in `outputs/final/acceptance.json`.

## Reproduction and limits

The final candidate averages forest and boosting probabilities and blends an Isolation Forest percentile into the ranking. Both technique families feed one constrained policy. All weights and acceptance criteria are recorded before test scoring in `outputs/final/freeze.json`. Frozen code, model and processed-data hashes are verified before evaluation. Later contextual-detector checks were exploratory development experiments, not independent anomaly truth.

An unsuccessful acceptance result is retained. The held-out comparison cannot be used to tune another candidate in this release. Validation sensitivity and deeper analyses are labelled development evidence. A cluster bootstrap reflects sampling uncertainty, not causal effectiveness or external validity.

Current-host verification is recorded separately from historical platform evidence. Linux-container execution must not be claimed without a current run. `just test` may skip evidence-dependent checks before the pipeline produces their inputs; the full run should supply those inputs. `just clean` removes generated data, reports' underlying outputs and review pages; it is for technical reproduction of the fixed release, not restarting scientific selection after seeing the test.

## Data and packaging

Kuzilek, Hlosta and Zdrahal, OULAD, UCI DOI [10.24432/C5KK69](https://doi.org/10.24432/C5KK69), CC BY 4.0. Source CSV/archive hashes are pinned in `configs/policy.json`. Raw data can be bundled under that licence; absent files are retrieved by `just download-data`. A slow first upstream transfer may exceed the analytical runtime target.

The release should include code, dataset access, aggregate results and the Markdown report. Exclude `.venv`, caches, private feedback, real-ID worklists and row-level predictions. Keep a main-code ZIP as requested for audit. No upload, public repository availability or LMS submission is implied by local packaging.

`docs/project_definition.md` preserves Intermediate commitments; `docs/EVIDENCE_BOUNDARIES.md` separates observed facts, assumptions and unsupported claims. The separate Arabic viva guide is a study aid rather than added report body.

## Submission versions

The repository root is the Final evaluation release. `submission/` contains the preserved Intermediate main-code ZIP. The Final report is separate from the Intermediate baseline report; validation findings and held-out results are labelled separately.
