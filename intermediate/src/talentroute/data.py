"""Decision-time feature construction and grouped temporal partitioning."""
from pathlib import Path
import hashlib, json, zipfile, urllib.request, shutil
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
KEY = ['code_module', 'code_presentation', 'id_student']

def config():
    return json.loads((ROOT/'configs/policy.json').read_text(encoding='utf-8'))

def file_sha256(path):
    checksum=hashlib.sha256()
    with Path(path).open('rb') as stream:
        while chunk:=stream.read(1024*1024):checksum.update(chunk)
    return checksum.hexdigest()

def download_archive(url, target, expected_sha256):
    """Publish an archive only after a complete, checksum-verified transfer."""
    target=Path(target); partial=target.with_suffix(target.suffix+'.partial')
    request=urllib.request.Request(url,headers={'User-Agent':'TalentRoute/0.1 educational reproduction'})
    try:
        with urllib.request.urlopen(request,timeout=60) as response, partial.open('wb') as output:
            shutil.copyfileobj(response,output,length=1024*1024)
        if file_sha256(partial)!=expected_sha256:
            raise ValueError('Downloaded archive checksum does not match the configured source')
        partial.replace(target)
    finally:
        partial.unlink(missing_ok=True)

def download():
    cfg=config(); raw=ROOT/'data/raw'
    supplied=cfg.get('raw_csv_sha256',{})
    if supplied and all((raw/name).is_file() for name in supplied):
        for name, expected in supplied.items():
            checksum=hashlib.sha256()
            with (raw/name).open('rb') as stream:
                while chunk:=stream.read(1024*1024):checksum.update(chunk)
            if checksum.hexdigest()!=expected:
                raise ValueError(f'Bundled raw CSV changed: {name}')
        manifest=raw/'manifest.json'
        manifest.write_text(json.dumps({'url':cfg['data_url'],'sha256':cfg['archive_sha256'],
            'csv_sha256':supplied,'access':'bundled CSVs; hashes pinned from verified official archive',
            'license':'CC BY 4.0','citation':'Kuzilek, Hlosta, Zdrahal (2015), doi:10.24432/C5KK69'},indent=2),encoding='utf-8')
        return manifest
    target=ROOT/'data/raw/oulad.zip'; target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():
        download_archive(config()['data_url'], target, config()['archive_sha256'])
    sha=file_sha256(target)
    if sha != config()['archive_sha256']:
        raise ValueError('Archive differs from the reviewed UCI checksum')
    manifest=ROOT/'data/raw/manifest.json'
    if manifest.exists() and json.loads(manifest.read_text(encoding='utf-8'))['sha256'] != sha:
        raise ValueError('Dataset checksum changed; review upstream version explicitly')
    with zipfile.ZipFile(target) as z:
        required=['studentInfo.csv','studentRegistration.csv','studentAssessment.csv','assessments.csv','studentVle.csv','courses.csv','vle.csv']
        names={Path(n).name:n for n in z.namelist()}
        for name in required:
            if not (target.parent/name).exists():
                destination=target.parent/name
                partial=destination.with_suffix('.csv.partial')
                try:
                    with z.open(names[name]) as source, partial.open('wb') as output:
                        shutil.copyfileobj(source,output,length=1024*1024)
                    if name in supplied and file_sha256(partial)!=supplied[name]:
                        raise ValueError(f'Extracted CSV checksum differs: {name}')
                    partial.replace(destination)
                finally:partial.unlink(missing_ok=True)
            elif name in supplied and file_sha256(target.parent/name)!=supplied[name]:
                raise ValueError(f'Existing CSV checksum differs: {name}')
    manifest.write_text(json.dumps({'url':config()['data_url'],'sha256':sha,'license':'CC BY 4.0','citation':'Kuzilek, Hlosta, Zdrahal (2015), doi:10.24432/C5KK69'},indent=2), encoding='utf-8')
    return manifest

def prepare(override=None, write_outputs=True):
    """Use only events by day 28; score delay is a conservative assumption, not observed grading time."""
    cfg=override or config(); cutoff=cfg['cutoff_day']; raw=ROOT/'data/raw'; out=ROOT/'outputs'; out.mkdir(exist_ok=True)
    info=pd.read_csv(raw/'studentInfo.csv',na_values=['?']); reg=pd.read_csv(raw/'studentRegistration.csv',na_values=['?'])
    if info.duplicated(KEY).any() or reg.duplicated(KEY).any():
        raise ValueError('Nonunique enrolment keys')
    df=info.merge(reg,on=KEY,validate='one_to_one')
    eligible=(df.date_registration<=cutoff)&(df.date_unregistration.isna()|(df.date_unregistration>cutoff))
    audit={'raw_enrolments':len(df),'eligible_enrolments':int(eligible.sum()),'cutoff_day':cutoff,'score_delay_days_assumed':cfg['score_delay_days'],'missing_registration_excluded':int(df.date_registration.isna().sum())}
    df=df.loc[eligible].copy()
    pieces=[]
    for chunk in pd.read_csv(raw/'studentVle.csv',chunksize=750000):
        c=chunk.loc[chunk.date.between(0,cutoff)].copy()
        c['early_clicks']=np.where(c.date<=14,c.sum_click,0)
        c['late_clicks']=np.where(c.date>14,c.sum_click,0)
        pieces.append(c.groupby(KEY).agg(clicks=('sum_click','sum'),early_clicks=('early_clicks','sum'),late_clicks=('late_clicks','sum'),last_day=('date','max')))
    engagement=pd.concat(pieces).groupby(KEY).agg({'clicks':'sum','early_clicks':'sum','late_clicks':'sum','last_day':'max'}).reset_index()
    df=df.merge(engagement,on=KEY,how='left',validate='one_to_one')
    for col in ['clicks','early_clicks','late_clicks']: df[col]=df[col].fillna(0)
    df['inactive_days']=cutoff-df.last_day.fillna(-1)
    df['engagement_change']=np.log1p(df.late_clicks)-np.log1p(df.early_clicks)
    assess=pd.read_csv(raw/'assessments.csv',na_values=['?']); submissions=pd.read_csv(raw/'studentAssessment.csv',na_values=['?'])
    submissions=submissions.merge(assess,on='id_assessment',validate='many_to_one')
    valid=submissions.loc[(submissions.date_submitted<=cutoff-cfg['score_delay_days'])&(submissions.is_banked==0)&(submissions.assessment_type!='Exam')].copy()
    valid['late_submission']=(valid.date_submitted>valid.date).astype(int)
    scores=valid.groupby(KEY).agg(score_mean=('score','mean'),score_min=('score','min'),submitted_count=('id_assessment','nunique'),late_rate=('late_submission','mean')).reset_index()
    df=df.merge(scores,on=KEY,how='left',validate='one_to_one')
    df['submitted_count']=df.submitted_count.fillna(0)
    df['no_early_assessment']=(df.submitted_count==0).astype(int)
    df['log_clicks']=np.log1p(df.clicks); df['log_early_clicks']=np.log1p(df.early_clicks);df['log_late_clicks']=np.log1p(df.late_clicks)
    df['target']=df.final_result.replace({'Pass':'Success','Distinction':'Success'})
    if not set(df.target)<= {'Success','Fail','Withdrawn'}: raise ValueError('Unknown outcomes')
    # Whole later presentation is held out; purge earlier records for any future student.
    df['split']=df.code_presentation.map({'2013B':'train','2013J':'train','2014B':'validation','2014J':'test'})
    if df.split.isna().any(): raise ValueError('Unknown presentation; revisit temporal design')
    test_ids=set(df.loc[df.split=='test','id_student']); val_ids=set(df.loc[df.split=='validation','id_student'])-test_ids
    keep=((df.split=='test')|((df.split=='validation')&~df.id_student.isin(test_ids))|((df.split=='train')&~df.id_student.isin(test_ids|val_ids)))
    audit['purged_earlier_repeat_enrolments']=int((~keep).sum()); df=df.loc[keep].copy()
    for a,b in [('train','validation'),('train','test'),('validation','test')]:
        assert not set(df.loc[df.split==a,'id_student'])&set(df.loc[df.split==b,'id_student'])
    audit['split_counts']=df.groupby('split').size().to_dict()
    if not write_outputs:
        return df,audit
    validate_prepared(df,cfg)
    (ROOT/'data/processed').mkdir(parents=True, exist_ok=True)
    df.to_csv(ROOT/'data/processed/enrolments.csv',index=False)
    # Audit reports development data only. No test labels/metrics inspected here.
    dev=df.loc[df.split!='test']
    dev.groupby(['split','target']).size().rename('n').to_csv(out/'development_target_counts.csv')
    dev.groupby(['split','code_module']).agg(n=('id_student','size'),no_assessment_rate=('no_early_assessment','mean')).to_csv(out/'development_coverage.csv')
    (out/'data_audit.json').write_text(json.dumps(audit,indent=2), encoding='utf-8')
    pd.DataFrame({'column':df.columns,'role':['label' if c in ['target','final_result','date_unregistration'] else 'categorical predictor and enrolment key' if c=='code_module' else 'partition/key' if c in KEY+['split'] else 'raw/candidate; model allowlist controls access' for c in df.columns]}).to_csv(ROOT/'docs/data_dictionary.csv',index=False)
    return audit


def validate_prepared(df,cfg):
    """Reject invalid target/key/range records before any model is fitted."""
    if df.duplicated(KEY).any(): raise ValueError('Duplicate enrolment keys')
    if df.target.isna().any() or not set(df.target)<= {'Success','Fail','Withdrawn'}: raise ValueError('Invalid target')
    for column in ['score_mean','score_min']:
        if not df[column].dropna().between(0,100).all(): raise ValueError('Invalid score range')
    for column in ['clicks','early_clicks','late_clicks','submitted_count','studied_credits','num_of_prev_attempts']:
        if (df[column].dropna()<0).any(): raise ValueError('Negative count/load')
    if not df.inactive_days.between(0,cfg['cutoff_day']+1).all(): raise ValueError('Invalid inactivity')
    if not df.late_rate.dropna().between(0,1).all(): raise ValueError('Invalid late rate')
    if df.split.isna().any() or not set(df.split)<= {'train','validation','test'}: raise ValueError('Invalid partition')
