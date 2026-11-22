"""Small controlled fixtures test availability rules, not model performance."""
import numpy as np
import pandas as pd
from talentroute import data


def test_future_events_and_excluded_cohort_cannot_change_prepared_features(tmp_path, monkeypatch):
    info = pd.DataFrame({'code_module': ['A'] * 5,
                         'code_presentation': ['2013B', '2013B', '2014B', '2014B', '2014J'],
                         'id_student': [1, 2, 3, 4, 5],
                         'final_result': ['Pass', 'Fail', 'Withdrawn', 'Pass', 'Fail']})
    registration = info[data.KEY].assign(date_registration=0, date_unregistration=np.nan)
    events = pd.DataFrame({'code_module': ['A'] * 6,
                           'code_presentation': ['2013B'] * 4 + ['2014B', '2014J'],
                           'id_student': [1, 1, 1, 1, 3, 5],
                           'date': [14, 15, 28, 29, 10, 1],
                           'sum_click': [2, 3, 4, 500, 2, 800]})
    assessments = pd.DataFrame({'id_assessment': [10, 11, 12], 'code_module': ['A'] * 3,
                                'code_presentation': ['2013B', '2014B', '2014J'],
                                'date': [np.nan, 20, 10], 'assessment_type': ['TMA'] * 3})
    submissions = pd.DataFrame({'id_assessment': [10, 10, 11, 12],
                                'id_student': [1, 2, 3, 5], 'date_submitted': [21, 22, 21, 5],
                                'is_banked': [0] * 4, 'score': [60, 99, 70, 100]})
    files = {'studentInfo.csv': info, 'studentRegistration.csv': registration,
             'studentVle.csv': events, 'assessments.csv': assessments,
             'studentAssessment.csv': submissions}
    def fixture_read(path, **options):
        result = files[path.name].copy(deep=True)
        return iter([result.iloc[:2], result.iloc[2:]]) if 'chunksize' in options else result
    monkeypatch.setattr(data, 'ROOT', tmp_path)
    monkeypatch.setattr(data, 'config', lambda: {'cutoff_day': 28, 'score_delay_days': 7})
    monkeypatch.setattr(data.pd, 'read_csv', fixture_read)
    (tmp_path / 'data').mkdir()
    (tmp_path / 'outputs').mkdir()
    first = data.prepare()
    events.loc[(events.date > 28) | events.code_presentation.eq('2014J'), 'sum_click'] = 10**9
    submissions.loc[submissions.date_submitted.gt(21) | submissions.id_assessment.eq(12), 'score'] = -10**6
    info.loc[info.code_presentation.eq('2014J'), 'final_result'] = 'Withdrawn'
    second = data.prepare()
    pd.testing.assert_frame_equal(first, second)
    assert not first.code_presentation.eq('2014J').any()
    row = first.set_index('id_student').loc[1]
    assert row.clicks == 9 and row.early_clicks == 2 and row.late_clicks == 7
    assert row.score_mean == 60
    assert pd.isna(row.late_rate)  # Unknown deadline is not evidence of on-time submission.
    assert first.set_index('id_student').loc[2].submitted_count == 0
