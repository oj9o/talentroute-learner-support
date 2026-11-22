"""OULAD access and day-28 features, derived from the Intermediate pipeline."""
from pathlib import Path
from datetime import date, timedelta
import hashlib
import json
import zipfile
import urllib.request
import shutil
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[2]
KEY = ['code_module', 'code_presentation', 'id_student']


def prior_registration_ids(registration, cutoff=28):
    """Use registrations certainly known by the earliest 2014B decision date.

    OULAD supplies start months, not days. Use the latest possible historical
    start day plus the recorded registration offset; no historical outcome is
    needed to establish that an enrolment already existed.
    """
    decision_earliest = date(2014, 2, 1) + timedelta(days=cutoff)
    known = set()
    for period, latest_start in [('2013B', date(2013, 2, 28)),
                                 ('2013J', date(2013, 10, 31))]:
        max_offset = (decision_earliest - latest_start).days
        rows = registration.loc[registration.code_presentation.eq(period)]
        known.update(rows.loc[rows.date_registration.le(max_offset), 'id_student'])
    return known

def config():
    """Load the policy and data-source settings as a dictionary."""
    return json.loads((ROOT / 'configs/policy.json').read_text(encoding='utf-8'))

def file_sha256(path):
    """Return the hexadecimal SHA-256 of a file without loading it all into memory."""
    checksum = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while (chunk := stream.read(1024 * 1024)):
            checksum.update(chunk)
    return checksum.hexdigest()

def download_archive(url, target, expected_sha256):
    """Publish an archive only after a complete, checksum-verified transfer."""
    target = Path(target)
    partial = target.with_suffix(target.suffix + '.partial')
    request = urllib.request.Request(url, headers={'User-Agent': 'TalentRoute/0.1 educational reproduction'})
    try:
        with urllib.request.urlopen(request, timeout=60) as response, partial.open('wb') as output:
            shutil.copyfileobj(response, output, length=1024 * 1024)
        if file_sha256(partial) != expected_sha256:
            raise ValueError('Downloaded archive checksum does not match the configured source')
        partial.replace(target)
    finally:
        partial.unlink(missing_ok=True)

def download():
    """Verify bundled CSVs or fetch the pinned public archive; return its manifest path."""
    cfg = config()
    raw = ROOT / 'data/raw'
    supplied = cfg.get('raw_csv_sha256', {})
    if supplied and all(((raw / name).is_file() for name in supplied)):
        for (name, expected) in supplied.items():
            checksum = hashlib.sha256()
            with (raw / name).open('rb') as stream:
                while (chunk := stream.read(1024 * 1024)):
                    checksum.update(chunk)
            if checksum.hexdigest() != expected:
                raise ValueError(f'Bundled raw CSV changed: {name}')
        manifest = raw / 'manifest.json'
        manifest.write_text(json.dumps({'url': cfg['data_url'], 'sha256': cfg['archive_sha256'], 'csv_sha256': supplied, 'access': 'bundled CSVs; hashes pinned from verified official archive', 'license': 'CC BY 4.0', 'citation': 'Kuzilek, Hlosta, Zdrahal (2015), doi:10.24432/C5KK69'}, indent=2), encoding='utf-8')
        return manifest
    target = ROOT / 'data/raw/oulad.zip'
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        download_archive(config()['data_url'], target, config()['archive_sha256'])
    sha = file_sha256(target)
    if sha != config()['archive_sha256']:
        raise ValueError('Archive differs from the reviewed UCI checksum')
    manifest = ROOT / 'data/raw/manifest.json'
    if manifest.exists() and json.loads(manifest.read_text(encoding='utf-8'))['sha256'] != sha:
        raise ValueError('Dataset checksum changed; review upstream version explicitly')
    with zipfile.ZipFile(target) as z:
        required = ['studentInfo.csv', 'studentRegistration.csv', 'studentAssessment.csv', 'assessments.csv', 'studentVle.csv', 'courses.csv', 'vle.csv']
        names = {Path(n).name: n for n in z.namelist()}
        for name in required:
            if not (target.parent / name).exists():
                destination = target.parent / name
                partial = destination.with_suffix('.csv.partial')
                try:
                    with z.open(names[name]) as source, partial.open('wb') as output:
                        shutil.copyfileobj(source, output, length=1024 * 1024)
                    if name in supplied and file_sha256(partial) != supplied[name]:
                        raise ValueError(f'Extracted CSV checksum differs: {name}')
                    partial.replace(destination)
                finally:
                    partial.unlink(missing_ok=True)
            elif name in supplied and file_sha256(target.parent / name) != supplied[name]:
                raise ValueError(f'Existing CSV checksum differs: {name}')
    manifest.write_text(json.dumps({'url': config()['data_url'], 'sha256': sha, 'license': 'CC BY 4.0', 'citation': 'Kuzilek, Hlosta, Zdrahal (2015), doi:10.24432/C5KK69'}, indent=2), encoding='utf-8')
    return manifest


def prepare():
    """Construct development features; discard 2014J before joins or aggregation.

    This retains Intermediate feature definitions. Both population protocols use
    the same evaluation rows; only the identity-overlap training purge differs.
    """
    cfg = config()
    raw = ROOT / 'data/raw'
    cutoff = cfg['cutoff_day']
    periods = ['2013B', '2013J', '2014B']
    info = pd.read_csv(raw / 'studentInfo.csv', na_values=['?'])
    info = info.loc[info.code_presentation.isin(periods)].copy()
    registration = pd.read_csv(raw / 'studentRegistration.csv', na_values=['?'])
    registration = registration.loc[registration.code_presentation.isin(periods)]
    if info.duplicated(KEY).any() or registration.duplicated(KEY).any():
        raise ValueError('Duplicate enrolment identity')
    earlier_ids = prior_registration_ids(registration, cutoff)
    frame = info.merge(registration, on=KEY, validate='one_to_one')
    eligible = (frame.date_registration <= cutoff) & (
        frame.date_unregistration.isna() | (frame.date_unregistration > cutoff)
    )
    frame = frame.loc[eligible & frame.code_presentation.isin(['2013B', '2014B'])].copy()
    pieces = []
    for chunk in pd.read_csv(raw / 'studentVle.csv', chunksize=750000):
        events = chunk.loc[
            chunk.code_presentation.isin(['2013B', '2014B']) & chunk.date.between(0, cutoff)
        ].copy()
        events['early_clicks'] = np.where(events.date <= 14, events.sum_click, 0)
        events['late_clicks'] = np.where(events.date > 14, events.sum_click, 0)
        pieces.append(events.groupby(KEY).agg(
            clicks=('sum_click', 'sum'), early_clicks=('early_clicks', 'sum'),
            late_clicks=('late_clicks', 'sum'), last_day=('date', 'max'),
        ))
    engagement = pd.concat(pieces).groupby(KEY).agg({
        'clicks': 'sum', 'early_clicks': 'sum', 'late_clicks': 'sum', 'last_day': 'max'
    }).reset_index()
    frame = frame.merge(engagement, on=KEY, how='left', validate='one_to_one')
    for column in ['clicks', 'early_clicks', 'late_clicks']:
        frame[column] = frame[column].fillna(0)
        frame['log_' + column] = np.log1p(frame[column])
    frame['inactive_days'] = cutoff - frame.last_day.fillna(-1)
    # Preserve the submitted definition for this availability experiment.
    # These are 15- and 14-day totals, not a normalized daily trend.
    frame['engagement_change'] = frame.log_late_clicks - frame.log_early_clicks
    assessments = pd.read_csv(raw / 'assessments.csv', na_values=['?'])
    assessments = assessments.loc[assessments.code_presentation.isin(['2013B', '2014B'])]
    submissions = pd.read_csv(raw / 'studentAssessment.csv', na_values=['?'])
    submissions = submissions.loc[submissions.id_assessment.isin(assessments.id_assessment)]
    submissions = submissions.merge(assessments, on='id_assessment', validate='many_to_one')
    submitted = submissions.loc[
        (submissions.date_submitted <= cutoff - cfg['score_delay_days']) &
        (submissions.is_banked == 0) & (submissions.assessment_type != 'Exam')
    ].copy()
    submitted['late_submission'] = (submitted.date_submitted > submitted.date).astype(float).where(
        submitted.date.notna())
    scores = submitted.groupby(KEY).agg(
        score_mean=('score', 'mean'), score_min=('score', 'min'),
        submitted_count=('id_assessment', 'nunique'), late_rate=('late_submission', 'mean'),
    ).reset_index()
    frame = frame.merge(scores, on=KEY, how='left', validate='one_to_one')
    frame['submitted_count'] = frame.submitted_count.fillna(0)
    frame['no_early_assessment'] = (frame.submitted_count == 0).astype(int)
    frame['target'] = frame.final_result.replace({'Pass': 'Success', 'Distinction': 'Success'})
    frame['split'] = frame.code_presentation.map({'2013B': 'train', '2014B': 'validation'})
    frame['prior_enrolment'] = frame.id_student.isin(earlier_ids) & (frame.split == 'validation')
    validation_ids = set(frame.loc[frame.split == 'validation', 'id_student'])
    frame['identity_disjoint_train'] = (frame.split == 'train') & ~frame.id_student.isin(validation_ids)
    if not set(frame.target) <= {'Success', 'Fail', 'Withdrawn'}:
        raise ValueError('Unexpected observed outcome')
    if frame.duplicated(KEY).any():
        raise ValueError('Duplicate prepared enrolment')
    processed = ROOT / 'data/processed'
    processed.mkdir(exist_ok=True)
    frame.to_csv(processed / 'development.csv', index=False)
    summaries = []
    for protocol in ['identity_disjoint', 'operational']:
        train, validation = split_frames(frame, protocol)
        for split, data in [('train', train), ('validation', validation)]:
            summaries.append({
                'protocol': protocol, 'split': split, 'n': len(data),
                'students': data.id_student.nunique(),
                'multi_enrolment_students': int(data.id_student.value_counts().gt(1).sum()),
                'adverse_n': data.target.ne('Success').sum(),
                'prior_enrolment_n': int(data.prior_enrolment.sum()) if split == 'validation' else 0,
                'modules': ','.join(sorted(data.code_module.unique())),
                'train_validation_identity_overlap': len(set(train.id_student) & set(validation.id_student)),
            })
    pd.DataFrame(summaries).to_csv(ROOT / 'outputs/populations.csv', index=False)
    print(f'Prepared {len(frame)} development enrolments; no 2014J rows retained.')
    return frame


def split_frames(frame, protocol):
    """Keep evaluation population fixed; vary only training identity-overlap removal."""
    if protocol not in {'identity_disjoint', 'operational'}:
        raise ValueError('Unknown population protocol')
    training = frame.split.eq('train')
    if protocol == 'identity_disjoint':
        training &= frame.identity_disjoint_train
    train = frame.loc[training].copy().reset_index(drop=True)
    validation = frame.loc[frame.split.eq('validation')].copy().reset_index(drop=True)
    if protocol == 'identity_disjoint' and set(train.id_student) & set(validation.id_student):
        raise ValueError('Identity overlap in identity-disjoint protocol')
    return train, validation
