> Intermediate development record. Final held-out evidence and conclusions are in `final_report.md`.

# Connected system

```mermaid
flowchart LR
  A[Official OULAD CSVs] --> B[Eligibility and day-28 cutoff]
  B --> C[ID-disjoint temporal partitions]
  C --> D[Training-only preprocessing]
  D --> E[Three-outcome classifier]
  D --> F[Engagement outlier detector]
  E --> G[Validation-selected score blend]
  F --> G
  G --> H[Staff-time constrained triage]
  H --> I[No action / alert / human review]
  I --> J[Held-out outcome coverage and workload]
  J --> K[Ablation, uncertainty, frontier, challenges]
```

Validation selects models/settings. Reserved final-test labels do not select any setting. The diagram describes risk targeting, not a causal chain of prevented failures.
