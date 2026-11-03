# Connected system

```mermaid
flowchart LR
  A[OULAD: eligibility and day-28 cutoff] --> B[ID-disjoint temporal partitions]
  B --> C[Training-only preprocessing]
  C --> D[Three-outcome classifier]
  C --> E[Engagement outlier detector]
  D --> F[Classifier-only provisional reference]
  D --> G[Blend: equal-effort ablation only]
  E --> G
  F --> H[Staff-minute triage: review / alert / no action]
  G --> I[Compare actual later outcome labels and workload]
  H --> I
  I --> J[Ablation, intervals, budget sensitivity, warning profiles, course segments]
```

The detector's incremental-benefit gate is not met. No treatment effect is established. Validation selection is exploratory; 2014J was already observed for a separate frozen candidate and is not rescored here.
