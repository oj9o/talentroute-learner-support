# TalentRoute — Intermediate learner-support triage

Mouza Al Darmaki · MAAI7101. Real OULAD data; classification and engagement outlier detection feed a staff-time-constrained queue for educational consulting teams.

## Reproduce

Install `uv` and `just`, then:

```sh
just install
just pipeline
just app 150
just app 600
```

Python 3.14 is pinned. No GPU, credentials or LLM API is required. `just pipeline` prepares data, runs baselines and model comparisons, EDA, deeper analyses, diagnostics, reports and tests. Exact runtime, environment and test count: outputs/current_pipeline_verification.json. Installation/network time is separate.

Open review/index.html offline; review/report.html displays the canonical docs/baseline_report.md. The Week 10 workspace is review/investigations.html; regenerate with `just investigations`. Keep sibling docs/outputs files with the interface. `just clean` removes generated data/outputs/interface; raw data remain. Evidence-dependent tests require generated outputs.

## Evidence and data

Read docs/project_definition.md for scope, commitments and acceptance; docs/data_dictionary.md for feature meaning. Costs, timing and seeds are configurable in configs/policy.json. Current development diagnostics follow a separate, already-recorded final evaluation; they do not reopen the test or select a replacement model.

OULAD: Kuzilek, Hlosta & Zdrahal (2015), https://doi.org/10.24432/C5KK69, CC BY 4.0. The Full ZIP includes seven public CSVs. `just download-data` verifies pinned checksums or downloads the official archive when absent. Network download can exceed 30 minutes. The Main_Code ZIP needs this data step; generated figures appear after the pipeline.

Only aggregate results are published. Historical platform records apply to their named snapshots. Current local verification is recorded separately; it does not certify an updated Linux run. Reported targeting coverage is not intervention effectiveness.
