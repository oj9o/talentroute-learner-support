"""Saved, labelled development-only plots tied to model and decision questions."""
import os
import tempfile
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR',str(Path(tempfile.gettempdir())/'talentroute-matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from .data import ROOT

def eda():
    out=ROOT/'outputs';df=pd.read_csv(ROOT/'data/processed/enrolments.csv');df=df[df.split!='test'];sns.set_theme(style='whitegrid')
    # Development-only overview; no identifiers or reserved-test samples exported.
    df.dtypes.astype(str).rename('dtype').to_csv(out/'eda_feature_types.csv')
    df.select_dtypes(include='number').drop(columns=['id_student'],errors='ignore').describe().T.to_csv(out/'eda_numeric_summary.csv')
    df.isna().sum().rename('missing_n').to_csv(out/'eda_missing_counts.csv')
    columns=['split','code_module','target','score_mean','submitted_count','log_clicks','inactive_days']
    df[columns].head(5).to_csv(out/'eda_sample_records.csv',index=False)
    outcomes={'Success':'#24856d','Fail':'#b74e59','Withdrawn':'#7756aa'}
    order=['Success','Fail','Withdrawn']
    def save(name,title,x,y):
        plt.title(title);plt.xlabel(x);plt.ylabel(y);plt.tight_layout();plt.savefig(out/(name+'.png'),dpi=140);plt.close()
    sns.countplot(data=df,x='target',hue='split',order=order,palette={'train':'#34445d','validation':'#a5b2c3'});save('eda_01_outcomes','Development outcomes by temporal partition','Outcome','Enrolments (count)')
    missing=df[['score_mean','score_min','late_rate','last_day']].isna().mean().sort_values();missing.plot.barh();save('eda_02_missingness','Observable feature missingness at day 28','Missing fraction','Feature')
    sns.boxplot(data=df,x='target',y='log_clicks',order=order,hue='target',palette=outcomes,legend=False,showfliers=False);save('eda_03_engagement','Early engagement by later outcome','Outcome','log(1 + clicks), days 0–28')
    sns.boxplot(data=df,x='target',y='score_mean',order=order,hue='target',palette=outcomes,legend=False,showfliers=False);save('eda_04_scores','Observed early scores by later outcome','Outcome','Mean score (0–100), assumed 7-day availability lag')
    sns.scatterplot(data=df.sample(min(2000,len(df)),random_state=7101),x='log_early_clicks',y='log_late_clicks',hue='target',hue_order=order,palette=outcomes,alpha=.35);save('eda_05_change','Engagement change: first versus second fortnight','log(1 + clicks), days 0–14','log(1 + clicks), days 15–28')
    pd.crosstab(df.code_module,df.target,normalize='index')[order].plot.bar(stacked=True,color=[outcomes[k] for k in order]);save('eda_06_modules','Outcome composition differs across modules','Module','Within-module fraction')
    df.groupby('code_module').no_early_assessment.mean().plot.bar();save('eda_07_observability','Assessment availability constrains early decisions','Module','Fraction without observable early assessment')
    sns.boxplot(data=df,x='target',y='inactive_days',order=order,hue='target',palette=outcomes,legend=False,showfliers=False);save('eda_08_inactivity','Inactivity is a warning signal, not a treatment effect','Outcome','Days since last observed VLE activity')
    if (out/'validation_sensitivity.csv').exists():
        s=pd.read_csv(out/'validation_sensitivity.csv');s=s[(s.assumption=='staff_minutes_per_100')&s.policy.isin(['business_rule','classifier_only','coupled_fixed_020'])]
        sns.lineplot(data=s,x='value',y='adverse_coverage',hue='policy',palette={'business_rule':'#738092','classifier_only':'#126c72','coupled_fixed_020':'#a66b20'},marker='o');save('decision_frontier','Validation frontier: coverage under staff constraints','Staff minutes per 100 enrolments','Later adverse outcomes flagged (fraction)')

    # Development-only model diagnostic; no student keys or presumed anomaly truth.
    if (out/'validation_predictions.csv').exists():
        pred=pd.read_csv(out/'validation_predictions.csv')
        pred['warning']=pred.action_anomaly_only.gt(0).map({True:'Detector-only flag',False:'Not flagged'})
        sample=pred.sample(min(2000,len(pred)),random_state=7101)
        sns.scatterplot(data=sample,x='risk',y='anomaly',hue='warning',palette={'Detector-only flag':'#a66b20','Not flagged':'#738092'},alpha=.4,s=18)
        save('eda_09_detector','Risk and unusual engagement need not identify the same cases','Classifier adverse-outcome probability','Training-reference anomaly percentile (not probability)')
