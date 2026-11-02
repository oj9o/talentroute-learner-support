"""Small synthetic fixtures test boundaries only; they never enter training data."""
import pandas as pd
from talentroute import data


def test_prepare_excludes_future_vle_and_unavailable_assessments(tmp_path,monkeypatch):
    raw=tmp_path/'data/raw'; raw.mkdir(parents=True)
    key={'code_module':'BBB','code_presentation':'2013B','id_student':1}
    pd.DataFrame([{**key,'final_result':'Pass'}]).to_csv(raw/'studentInfo.csv',index=False)
    pd.DataFrame([{**key,'date_registration':-1,'date_unregistration':None}]).to_csv(raw/'studentRegistration.csv',index=False)
    pd.DataFrame([{**key,'date':day,'sum_click':clicks} for day,clicks in [(-1,1000),(0,2),(14,3),(28,5),(29,1000)]]).to_csv(raw/'studentVle.csv',index=False)
    pd.DataFrame([{'id_assessment':i,'code_module':'BBB','code_presentation':'2013B','assessment_type':'Exam' if i==4 else 'TMA','date':20} for i in range(1,5)]).to_csv(raw/'assessments.csv',index=False)
    pd.DataFrame([{'id_assessment':i,'id_student':1,'date_submitted':day,'is_banked':banked,'score':score} for i,day,banked,score in [(1,21,0,40),(2,22,0,100),(3,10,1,100),(4,10,0,100)]]).to_csv(raw/'studentAssessment.csv',index=False)
    monkeypatch.setattr(data,'ROOT',tmp_path)
    frame,_=data.prepare({'cutoff_day':28,'score_delay_days':7},write_outputs=False)
    row=frame.iloc[0]
    assert row.clicks==10 and row.early_clicks==5 and row.late_clicks==5
    assert row.last_day==28 and row.inactive_days==0
    assert row.score_mean==40 and row.submitted_count==1
