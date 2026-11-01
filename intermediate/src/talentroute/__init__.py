"""TalentRoute development pipeline."""
import os
# Bound CPU use for deterministic laptop execution, without system-core discovery.
os.environ.setdefault('LOKY_MAX_CPU_COUNT','2')
os.environ.setdefault('OMP_NUM_THREADS','2')
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
