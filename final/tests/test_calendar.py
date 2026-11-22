from talentroute.calendar_audit import availability_status, presentation_bounds


def test_later_start_year_does_not_establish_training_label_availability():
    training = presentation_bounds("2013J", 261)
    decision = presentation_bounds("2014B", 241)
    assert availability_status(training, decision, 0) == "course_not_finished_by_decision"


def test_earlier_year_same_season_leaves_time_even_with_assumed_delay():
    training = presentation_bounds("2013B", 240)
    decision = presentation_bounds("2014B", 241)
    assert availability_status(training, decision, 60) == "end_plus_assumed_delay_before_decision"


def test_overlapping_bounds_do_not_invent_an_exact_release_date():
    training = presentation_bounds("2014B", 241)
    decision = presentation_bounds("2014J", 269)
    assert availability_status(training, decision, 30) == "availability_unresolved_within_bounds"
