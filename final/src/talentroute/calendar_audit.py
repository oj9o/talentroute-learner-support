"""Bound calendar availability without inventing exact course or release dates."""

import calendar
import csv
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    "https://archive.ics.uci.edu/dataset/349/open+university+learning+analytics+dataset"
)


def presentation_bounds(code, length, cutoff=28):
    """Use the full known start month; allow both duration-count conventions.

    UCI identifies B as February and J as October. The CSV has no exact start
    date or final-result release timestamp. These are bounds, not observed dates.
    """
    year = int(code[:4])
    month = {"B": 2, "J": 10}[code[4:]]
    first = date(year, month, 1)
    last = date(year, month, calendar.monthrange(year, month)[1])
    return {
        "start_earliest": first,
        "start_latest": last,
        "end_earliest": first + timedelta(days=int(length) - 1),
        "end_latest": last + timedelta(days=int(length)),
        "decision_earliest": first + timedelta(days=cutoff),
        "decision_latest": last + timedelta(days=cutoff),
    }


def availability_status(training, decision, assumed_release_delay):
    """Classify date bounds; even the favorable case depends on an assumed lag."""
    if training["end_earliest"] > decision["decision_latest"]:
        return "course_not_finished_by_decision"
    release_latest = training["end_latest"] + timedelta(days=assumed_release_delay)
    if release_latest < decision["decision_earliest"]:
        return "end_plus_assumed_delay_before_decision"
    return "availability_unresolved_within_bounds"


def write_csv(path, records):
    """Save calendar assumptions and audit results in the output directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def run():
    """Audit course metadata only. Never load student outcomes or fit a model."""
    with (ROOT / "data/raw/courses.csv").open(newline="", encoding="utf-8") as stream:
        courses = list(csv.DictReader(stream))
    calendar_rows = []
    for course in courses:
        bounds = presentation_bounds(
            course["code_presentation"], course["module_presentation_length"]
        )
        calendar_rows.append({**course, **bounds})
    write_csv(ROOT / "outputs/calendar_bounds.csv", calendar_rows)

    audit = []
    # The 2014J pair audits metadata relevant to prior validation availability;
    # it neither reads 2014J student data nor evaluates the observed final cohort.
    for training_period, decision_period in [
        ("2013B", "2014B"),
        ("2013J", "2014B"),
        ("2014B", "2014J"),
    ]:
        training_rows = [
            r for r in calendar_rows if r["code_presentation"] == training_period
        ]
        decision_rows = [
            r for r in calendar_rows if r["code_presentation"] == decision_period
        ]
        decision = {
            "decision_earliest": min(r["decision_earliest"] for r in decision_rows),
            "decision_latest": max(r["decision_latest"] for r in decision_rows),
        }
        for course in training_rows:
            for delay in [0, 30, 60]:
                audit.append(
                    {
                        "training_presentation": training_period,
                        "training_module": course["code_module"],
                        "decision_presentation": decision_period,
                        "course_end_earliest": course["end_earliest"],
                        "course_end_latest": course["end_latest"],
                        **decision,
                        "release_delay_days_assumed": delay,
                        "status": availability_status(course, decision, delay),
                        "actual_release_date_observed": False,
                    }
                )
    write_csv(ROOT / "outputs/label_availability.csv", audit)
    print(
        "Calendar audit written from courses.csv only; exact label release dates remain unknown."
    )
    return audit


if __name__ == "__main__":
    run()
