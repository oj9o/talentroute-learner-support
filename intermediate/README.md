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

Python 3.14 is pinned. No GPU, credentials or LLM API is required. `just pipeline` prepares data, runs baselines and model comparisons, EDA, deeper analyses, diagnostics, reports and tests. Analytical runtime: 41.91s in the prior Mac run; 84.66s in the current Linux run. Earlier local execution: outputs/current_pipeline_verification.json. Installation/network time is separate. Execution and archive checks accompany the submission packages. Historical source hashes apply only to their recorded versions.

Open review/decision_room.html or review/index.html offline; review/report.html displays docs/baseline_report.md. Investigations: review/investigations.html (`just investigations`). Keep sibling docs/outputs folders. `just clean` removes generated data/outputs/interface but retains raw data. Evidence tests require generated outputs.

## Evidence and data

Read docs/project_definition.md for scope, commitments and acceptance; docs/data_dictionary.md for feature meaning. Costs, timing and seeds are configurable in configs/policy.json. Current development diagnostics follow a separate, already-recorded final evaluation; they do not reopen the test or select a replacement model.

OULAD: Kuzilek, Hlosta & Zdrahal (2015), https://doi.org/10.24432/C5KK69, CC BY 4.0. The Full ZIP includes seven public CSVs and saved evidence; Main_Code contains source, configuration and documentation only. `just download-data` verifies pinned checksums or downloads the official archive when absent. A fresh official download and all CSV hashes were verified: outputs/official_download_verification.json. Network time varies. The Main_Code ZIP needs this data step; generated figures appear after the pipeline.

Only aggregate results are published. The checked-in report uses Mac outputs; Linux HGB coverage differs slightly. Per-run reports regenerate from their own outputs; platform_reproduction.csv quantifies the difference. Historical records apply only to their named snapshots. Reported targeting coverage is not intervention effectiveness.
