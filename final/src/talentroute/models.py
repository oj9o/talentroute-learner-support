"""Train-only transformations and fixed development model comparisons."""

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, f1_score, log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

from .data import ROOT, split_frames

NUM = ['score_mean', 'score_min', 'submitted_count', 'late_rate',
       'no_early_assessment', 'studied_credits', 'num_of_prev_attempts']
ENG = ['log_clicks', 'log_early_clicks', 'log_late_clicks',
       'inactive_days', 'engagement_change']
FEATURES = NUM + ENG + ['code_module']
CANDIDATES = ['logistic', 'logistic_c01', 'logistic_c10', 'tree', 'hgb_7_2', 'hgb_15_10']
REFERENCE = 'hgb_15_10'


def numeric_transform(scale=True):
    steps = [('impute', SimpleImputer(strategy='median', add_indicator=True, keep_empty_features=True))]
    if scale:
        steps.append(('scale', StandardScaler()))
    return Pipeline(steps)


def classifier(name, seed, numeric_features=None):
    """Return an unfitted candidate; settings come from the submitted comparisons."""
    if name.startswith('logistic'):
        strength = {'logistic': 1.0, 'logistic_c01': 0.1, 'logistic_c10': 10.0}[name]
        estimator = LogisticRegression(C=strength, max_iter=1500, random_state=seed)
    elif name == 'tree':
        estimator = DecisionTreeClassifier(max_depth=5, min_samples_leaf=40, random_state=seed)
    elif name in {'hgb_7_2', 'hgb_15_10'}:
        _, leaves, penalty = name.split('_')
        estimator = HistGradientBoostingClassifier(
            max_iter=140, learning_rate=0.07, max_leaf_nodes=int(leaves),
            l2_regularization=float(penalty), early_stopping=False, random_state=seed,
        )
    else:
        raise ValueError('Unknown classifier')
    preprocessing = ColumnTransformer([
        ('numeric', numeric_transform(scale=name.startswith('logistic')),
         NUM + ENG if numeric_features is None else list(numeric_features)),
        ('module', OneHotEncoder(handle_unknown='ignore', sparse_output=False), ['code_module']),
    ])
    return Pipeline([('preprocess', preprocessing), ('model', estimator)])


def risk_from(model, frame):
    probabilities = model.predict_proba(frame[list(model.feature_names_in_)])
    classes = list(model.classes_)
    risk = 1 - probabilities[:, classes.index('Success')]
    return risk, probabilities


def ml_metrics(target, probabilities, classes):
    labels = list(classes)
    target = np.asarray(target)
    risk = 1 - probabilities[:, labels.index('Success')]
    adverse = target != 'Success'
    metrics = {
        'adverse_average_precision': average_precision_score(adverse, risk),
        'adverse_prevalence': adverse.mean(),
        'adverse_brier': np.mean((adverse - risk) ** 2),
        'log_loss': log_loss(target, probabilities, labels=labels),
        'macro_f1': f1_score(target, np.asarray(labels)[probabilities.argmax(axis=1)], average='macro'),
    }
    for name in ['Fail', 'Withdrawn']:
        metrics[name.lower() + '_average_precision'] = average_precision_score(
            target == name, probabilities[:, labels.index(name)]
        )
        metrics[name.lower() + '_prevalence'] = (target == name).mean()
    return metrics


def fit_development():
    """Fit the bounded development grid; never score the historical final cohort."""
    frame = pd.read_csv(ROOT / 'data/processed/development.csv')
    if set(frame.code_presentation) != {'2013B', '2014B'}:
        raise ValueError('Unexpected period in development-only file')
    rows = []
    detector_rows = []
    for protocol in ['identity_disjoint', 'operational']:
        train, validation = split_frames(frame, protocol)
        for seed in [7101, 7102, 7103]:
            fitted = {}
            predictions = validation.copy()
            for name in CANDIDATES:
                model = classifier(name, seed).fit(train[FEATURES], train.target)
                risk, probabilities = risk_from(model, validation)
                predictions[name] = risk
                fitted[name] = model
                rows.append({'protocol': protocol, 'seed': seed, 'model': name,
                             **ml_metrics(validation.target, probabilities, model.classes_)})
            # Engagement only: course identifiers are not treated as anomalous behavior.
            detector = Pipeline([
                ('preprocess', numeric_transform()),
                ('model', IsolationForest(n_estimators=150, max_samples=min(512, len(train)),
                                          random_state=seed, n_jobs=1)),
            ]).fit(train[ENG])
            reference_scores = np.sort(-detector.score_samples(train[ENG]))
            rarity = np.searchsorted(reference_scores, -detector.score_samples(validation[ENG]),
                                     side='right') / len(reference_scores)
            predictions['rarity'] = rarity
            predictions['unseen_module'] = ~validation.code_module.isin(train.code_module.unique())
            predictions['heuristic'] = -validation.score_mean.fillna(50) / 100 + validation.inactive_days / 29
            for name, values in [('isolation_forest', rarity), ('inactivity', validation.inactive_days)]:
                detector_rows.append({
                    'protocol': protocol, 'seed': seed, 'detector': name,
                    'outcome_relevance_average_precision': average_precision_score(validation.target.ne('Success'), values),
                    'anomaly_accuracy_measurable': False,
                })
            predictions.to_csv(ROOT / f'data/processed/predictions_{protocol}_{seed}.csv', index=False)
            if seed == 7101:
                input_columns = ['early_clicks', 'late_clicks', 'inactive_days', 'score_mean',
                                 'score_min', 'submitted_count', 'late_rate', 'studied_credits',
                                 'num_of_prev_attempts']
                ranges = {key: (float(train[key].min()), float(train[key].max())) for key in input_columns}
                joblib.dump({'models': fitted, 'detector': detector, 'reference': reference_scores,
                             'training_modules': sorted(train.code_module.unique()), 'training_ranges': ranges},
                            ROOT / f'outputs/models_{protocol}.joblib')
            print(f'Fitted {protocol}, seed {seed}: train={len(train)}, validation={len(validation)}', flush=True)
    pd.DataFrame(rows).to_csv(ROOT / 'outputs/model_comparison.csv', index=False)
    pd.DataFrame(detector_rows).to_csv(ROOT / 'outputs/detector_comparison.csv', index=False)


if __name__ == '__main__':
    fit_development()
