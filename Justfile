set shell := ["bash", "-e", "-o", "pipefail", "-c"]
install:
    uv sync --frozen

download-data:
    uv run python -m talentroute download

prepare-data:
    uv run python -m talentroute prepare

test:
    uv run pytest -q

eda:
    uv run python scripts/eda.py

run-baseline:
    uv run python -m talentroute fit
    uv run python -m talentroute evaluate

run-model:
    uv run python -c "from talentroute.final_workflow import fit_final; fit_final()"

evaluate:
    uv run python -c "from talentroute.final_workflow import final_evaluate; print(final_evaluate())"

ablation: evaluate
    uv run python -c "from talentroute.final_workflow import analysis_outputs; analysis_outputs()"

sensitivity: ablation
    uv run python -m talentroute data-sensitivity

deep-dives: run-baseline
    uv run python -m talentroute revision
    uv run python scripts/specialist_interval.py
    uv run python -m talentroute stability

app budget="300":
    uv run python -c "from talentroute.final_workflow import final_app; final_app({{budget}})"

report:
    uv run python -m talentroute report

pipeline:
    uv run python scripts/final_pipeline.py

clean:
    uv run python scripts/clean_generated.py

# Exploratory revision; original baseline results remain preserved.
revision:
    uv run python -m talentroute revision

review:
    uv run python scripts/build_review.py

diagnostics:
    uv run python -m talentroute diagnostics

# Reconcile declared claims with current data and saved decisions.
verify:
    uv run python scripts/verify_submission.py

final-report:
    uv run python scripts/final_report.py

final-review:
    uv run python scripts/build_final_review.py

verify-final:
    uv run python scripts/verify_final.py

platform-evidence archive repository:
    uv run python scripts/import_platform_evidence.py "{{archive}}" "{{repository}}"

# Post-freeze exploratory diagnostics; no final-test scoring.
investigations:
    uv run python scripts/debug_investigations.py
    uv run python scripts/build_investigations.py
