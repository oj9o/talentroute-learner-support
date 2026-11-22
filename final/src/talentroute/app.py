"""One offline decision workbench. Loads fitted artifacts; never trains a model."""

import argparse
import csv
from dataclasses import fields
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from urllib.parse import parse_qs, urlparse

import joblib
import numpy as np
import pandas as pd

from .analyses import Values, assumed_value, route_changes, workload_stress
from .data import ROOT
from .decision import Policy, capacity, observed_metrics
from .evaluation import ROUTES, frame_actions
from .plan import apply_edits, check_plan, compare_actions
from .models import CANDIDATES, ENG, risk_from

PROTOCOLS = ['identity_disjoint', 'operational']
ACTIONS = {0: 'No action', 1: 'Alert', 2: 'Review'}


@lru_cache(maxsize=2)
def selected_model():
    if not (ROOT / 'outputs/assessment_free_operational.joblib').exists():
        raise FileNotFoundError('Run just pipeline to fit the final model')
    return 'assessment_free'


def artifacts(protocol):
    if protocol not in PROTOCOLS:
        raise ValueError('Unknown population protocol')
    frame = pd.read_csv(ROOT / f'data/processed/predictions_{protocol}_7101.csv')
    bundle = joblib.load(ROOT / f'outputs/models_{protocol}.joblib')
    if not len(bundle['reference']) or np.any(np.diff(bundle['reference']) < 0):
        raise ValueError('Training anomaly reference must be nonempty and sorted')
    safe_path = ROOT / f'outputs/assessment_free_{protocol}.joblib'
    if safe_path.exists():
        safe = joblib.load(safe_path)
        bundle['models']['assessment_free'] = safe['model']
        frame['assessment_free'] = risk_from(safe['model'], frame)[0]
    return frame, bundle


def settings(payload):
    protocol = payload.get('protocol', 'operational')
    model = payload.get('model', selected_model())
    route = payload.get('route', 'classifier')
    if model not in [*CANDIDATES, 'assessment_free'] or route not in ROUTES:
        raise ValueError('Unknown model or route')
    parameters = payload.get('policy', {})
    allowed = {f.name for f in fields(Policy)}
    if not isinstance(parameters, dict) or set(parameters) - allowed:
        raise ValueError('Unknown policy setting')
    policy = Policy(**{name: float(value) for name, value in parameters.items()})
    policy.validate()
    frame, bundle = artifacts(protocol)
    return frame, bundle, protocol, model, route, policy


def scenario(payload):
    """Reallocate observed cases. Outcomes are consulted only after allocation."""
    frame, _, protocol, model, route, policy = settings(payload)
    actions, reasons = frame_actions(frame, route, policy, model=model)
    reference, _ = frame_actions(frame, 'classifier', policy, model=model)
    metrics = observed_metrics(frame.target, actions, policy)
    changes = route_changes(frame, reference, actions, reasons)
    composition = []
    for module, group in frame.groupby('code_module'):
        composition.append({'module': module, 'unseen': bool(group.unseen_module.iloc[0]),
                            **observed_metrics(group.target, actions[group.index], policy)})
    preference = Values(**{name: float(value) for name, value in payload.get('values', {}).items()})
    queue = pd.DataFrame({
        'case': [f'Case {index+1:04d}' for index in range(len(frame))],
        'module': frame.code_module, 'model_risk': frame[model],
        'anomaly_percentile': frame.rarity, 'action': [ACTIONS[x] for x in actions],
        'reason': reasons,
    }).loc[actions > 0].sort_values(['action', 'model_risk'], ascending=[False, False])
    return {'protocol': protocol, 'model': model, 'route': route, 'policy': vars(policy),
            'budget_minutes': capacity(len(frame), policy)[2], 'metrics': metrics,
            'transitions': changes, 'composition': composition,
            'decision_rules': check_plan(frame[model], actions, policy),
            'editable_cases': explain_cases(frame, model, actions, reasons, policy),
            'comparison': compare_scenarios(payload, frame, actions, policy),
            'assumed_preference_units': assumed_value(metrics, preference),
            'workload_stress': workload_stress(frame, actions, model, policy, route),
            'preference_assumptions': vars(preference), 'queue': queue.to_dict('records')}


def explain_cases(frame, model, actions, reasons, policy):
    """Small, deterministic examples spanning selected and unselected cases."""
    risk = frame[model].to_numpy()
    indices = []
    for action in (2, 1, 0):
        group = np.flatnonzero(actions == action)
        order = group[np.argsort(-risk[group], kind='stable')]
        indices.extend(order[:2].tolist())
        if len(order) > 2:
            indices.append(int(order[-1]))
    rows = []
    for index in indices:
        reason = reasons[index]
        if risk[index] < policy.risk_threshold:
            why = 'Below the minimum risk threshold; no action is eligible.'
        elif actions[index] == 0:
            why = 'Meets the threshold, but no place remains for this case under the budget and route ordering.'
        elif reason == 'risk_review':
            why = 'Selected by risk rank for a remaining review place after any reserved places.'
        elif reason == 'risk_alert':
            why = 'Not assigned a review; selected by risk rank for an alert place.'
        else:
            why = f'Selected through the {reason.removesuffix("_review")} reserve within existing review places.'
        rows.append({'index': index, 'case': f'Case {index+1:04d}',
                     'module': str(frame.iloc[index].code_module),
                     'risk': float(risk[index]), 'action': int(actions[index]),
                     'explanation': why})
    return rows


def compare_scenarios(payload, frame, actions, policy):
    previous = payload.get('previous')
    if previous is None:
        return None
    old_frame, _, old_protocol, old_model, old_route, old_policy = settings(previous)
    if old_protocol != payload.get('protocol', 'operational'):
        raise ValueError('Save a new comparison point after changing population protocol')
    if not old_frame.index.equals(frame.index):
        raise ValueError('Comparison requires the same course cases')
    old_actions, _ = frame_actions(old_frame, old_route, old_policy, model=old_model)
    return {**compare_actions(old_actions, actions, frame.code_module),
            'before_minutes': check_plan(old_frame[old_model], old_actions, old_policy)['used_minutes'],
            'after_minutes': check_plan(frame[payload.get('model', selected_model())], actions, policy)['used_minutes'],
            'before_model': old_model, 'after_model': payload.get('model', selected_model()),
            'before_policy': vars(old_policy), 'after_policy': vars(policy),
            'before_route': old_route, 'after_route': payload.get('route', 'classifier')}


def check_edited_plan(payload):
    frame, _, _, model, route, policy = settings(payload)
    original, _ = frame_actions(frame, route, policy, model=model)
    proposed = apply_edits(original, payload.get('edits', []))
    return {**check_plan(frame[model], proposed, policy),
            'changes': compare_actions(original, proposed, frame.code_module)}


def case_inputs(index, protocol='operational'):
    """Expose observed predictors for one anonymous enrolment; no ID or outcome."""
    frame, _ = artifacts(protocol)
    if not 0 <= index < len(frame):
        raise ValueError('Case outside cohort')
    row = frame.iloc[index]
    keys = ['code_module', 'early_clicks', 'late_clicks', 'inactive_days',
            'score_mean', 'score_min', 'submitted_count', 'late_rate',
            'studied_credits', 'num_of_prev_attempts']
    return {name: None if pd.isna(row[name]) else row[name] for name in keys}


def validate_inputs(raw, protocol):
    """Check ranges and consistency against the day-0..28 feature definitions."""
    inputs = dict(raw)
    required = set(case_inputs(0, protocol))
    if set(inputs) != required:
        raise ValueError('Provide exactly the displayed predictor fields')
    if inputs['code_module'] not in ['AAA', 'BBB', 'CCC', 'DDD', 'EEE', 'FFF', 'GGG']:
        raise ValueError('Unknown OULAD module')
    ranges = {'early_clicks': (0, 100000), 'late_clicks': (0, 100000),
              'inactive_days': (0, 29), 'submitted_count': (0, 100),
              'late_rate': (0, 1), 'studied_credits': (0, 1000),
              'num_of_prev_attempts': (0, 30)}
    for name, (lower, upper) in ranges.items():
        if name == 'late_rate' and (float(inputs['submitted_count']) == 0 or inputs[name] is None):
            inputs[name] = np.nan
            continue
        value = float(inputs[name])
        if not np.isfinite(value) or not lower <= value <= upper:
            raise ValueError(f'{name} must be between {lower} and {upper}')
        inputs[name] = value
    for name in ['early_clicks', 'late_clicks', 'inactive_days', 'submitted_count', 'num_of_prev_attempts']:
        if inputs[name] != int(inputs[name]):
            raise ValueError(f'{name} must be a whole number')
    early, late = inputs['early_clicks'], inputs['late_clicks']
    inactive = inputs['inactive_days']
    if (early + late == 0) != (inactive == 29):
        raise ValueError('No day-0..28 clicks requires 29 inactive days, and conversely')
    if late > 0 and inactive > 13:
        raise ValueError('Clicks during days 15..28 require inactivity of at most 13 days')
    if late == 0 and early > 0 and inactive < 14:
        raise ValueError('Clicks only during days 0..14 require at least 14 inactive days')
    if inputs['submitted_count'] == 0:
        inputs.update(score_mean=np.nan, score_min=np.nan, late_rate=np.nan)
    else:
        missing_scores = [inputs[name] is None for name in ['score_mean', 'score_min']]
        if any(missing_scores) and not all(missing_scores):
            raise ValueError('Provide both score summaries, or leave both blank when unavailable')
        for name in ['score_mean', 'score_min']:
            if inputs[name] is None:
                inputs[name] = np.nan
                continue
            value = float(inputs[name])
            if not np.isfinite(value) or not 0 <= value <= 100:
                raise ValueError('Observed assessment scores must be between 0 and 100')
            inputs[name] = value
        if inputs['score_min'] > inputs['score_mean']:
            raise ValueError('Minimum score cannot exceed mean score')
        if inputs['submitted_count'] == 1 and np.isfinite(inputs['score_mean']) and inputs['score_min'] != inputs['score_mean']:
            raise ValueError('One assessment must have the same mean and minimum score')
        late_count = inputs['late_rate'] * inputs['submitted_count']
        if np.isfinite(late_count) and not np.isclose(late_count, round(late_count)):
            raise ValueError('Late-submission fraction must correspond to a whole number of assessments')
    return inputs


def derive_features(inputs):
    """Apply the same deterministic formulas as cohort preparation."""
    inputs = dict(inputs)
    early, late = inputs['early_clicks'], inputs['late_clicks']
    inputs['log_clicks'] = np.log1p(early + late)
    inputs['log_early_clicks'] = np.log1p(early)
    inputs['log_late_clicks'] = np.log1p(late)
    inputs['engagement_change'] = np.log1p(late) - np.log1p(early)
    inputs['no_early_assessment'] = int(inputs['submitted_count'] == 0)
    return pd.DataFrame([inputs])


def predict_case(payload):
    """Score edited inputs, reporting extrapolation without fabricating outcomes."""
    _, bundle, protocol, model, _, _ = settings(payload)
    inputs = validate_inputs(payload['inputs'], protocol)
    warnings = []
    if model != 'assessment_free' and inputs['submitted_count'] > 0 and not np.isfinite(inputs['score_mean']):
        warnings.append('Submitted assessments have no available score; training-fitted imputation is used.')
    if model == 'assessment_free':
        warnings.append('Assessment-free mode ignores all assessment fields. Selection used 2013B only; 2014B remains retrospective evaluation.')
    for name, (lower, upper) in bundle['training_ranges'].items():
        if model == 'assessment_free' and name in {'score_mean', 'score_min', 'submitted_count', 'late_rate'}:
            continue
        value = inputs[name]
        if np.isfinite(value) and not lower <= value <= upper:
            warnings.append(f'{name}: outside the training range [{lower:g}, {upper:g}].')
    frame = derive_features(inputs)
    estimator = bundle['models'][model]
    risk, probabilities = risk_from(estimator, frame)
    unusual = -bundle['detector'].score_samples(frame[ENG])[0]
    percentile = np.searchsorted(bundle['reference'], unusual, side='right') / len(bundle['reference'])
    return {'risk': float(risk[0]), 'probabilities': dict(zip(estimator.classes_, probabilities[0])),
            'anomaly_percentile': float(percentile),
            'unseen_module': inputs['code_module'] not in bundle['training_modules'],
            'model': model, 'protocol': protocol, 'warnings': warnings}


def clean_json(value):
    if isinstance(value, dict):
        return {str(k): clean_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean_json(v) for v in value]
    if isinstance(value, (np.integer, np.bool_)):
        return value.item()
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    return value


class Handler(BaseHTTPRequestHandler):
    def reply(self, value, status=200):
        encoded = json.dumps(clean_json(value), allow_nan=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == '/configuration':
            try:
                self.reply({'selected_model': selected_model(), 'default_protocol': 'operational'})
            except FileNotFoundError:
                self.reply({'error': 'Model outputs are missing. Run just pipeline before opening the app.'}, 503)
            except (ValueError, KeyError) as error:
                self.reply({'error': str(error)}, 503)
            return
        if url.path == '/case':
            try:
                params = parse_qs(url.query)
                self.reply(case_inputs(int(params.get('index', [0])[0]), params.get('protocol', ['operational'])[0]))
            except (ValueError, TypeError, KeyError) as error:
                self.reply({'error': str(error)}, 400)
            except FileNotFoundError:
                self.reply({'error': 'Model outputs are missing. Run just pipeline first.'}, 503)
            return
        files = {'/': ('app/index.html', 'text/html'), '/app.js': ('app/app.js', 'text/javascript'),
                 '/style.css': ('app/style.css', 'text/css'),
                 '/report': ('docs/final_report.md', 'text/plain; charset=utf-8')}
        if url.path not in files:
            self.send_error(404)
            return
        path, mime = files[url.path]
        if not (ROOT / path).exists():
            self.send_error(503, 'Generated file is missing. Run just pipeline first.')
            return
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.end_headers()
        self.wfile.write((ROOT / path).read_bytes())

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            if length <= 0 or length > 50000:
                raise ValueError('Request size is invalid')
            payload = json.loads(self.rfile.read(length))
            if self.path == '/check-plan':
                self.reply(check_edited_plan(payload))
            elif self.path == '/predict':
                self.reply(predict_case(payload))
            elif self.path in {'/scenario', '/export'}:
                result = scenario(payload)
                if self.path == '/scenario':
                    result['queue'] = result['queue'][:100]
                    self.reply(result)
                else:
                    stream = io.StringIO()
                    columns = ['case', 'module', 'model_risk', 'anomaly_percentile', 'action', 'reason']
                    writer = csv.DictWriter(stream, fieldnames=columns)
                    writer.writeheader()
                    writer.writerows(result['queue'])
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/csv')
                    self.end_headers()
                    self.wfile.write(stream.getvalue().encode())
            else:
                self.send_error(404)
        except (ValueError, TypeError, KeyError) as error:
            self.reply({'error': str(error)}, 400)
        except FileNotFoundError:
            self.reply({'error': 'Model outputs are missing. Run just pipeline first.'}, 503)


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8800)
    args = parser.parse_args()
    print(f'TalentRoute development workbench: http://127.0.0.1:{args.port}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', args.port), Handler).serve_forever()


if __name__ == '__main__':
    run()
