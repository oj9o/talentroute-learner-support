"""Training-only temperature-calibration experiment; never replaces the default model.

Three learner-grouped outer folds assess the correction. Each outer training
partition is split again: two thirds for model selection/fitting, one third
for temperature fitting. Outer outcomes are used only for scoring. This remains
retrospective evidence, not recovery of an unseen historical test.
"""
import json
import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.special import softmax
from sklearn.metrics import log_loss
from .data import ROOT
from .nested_audit import training_cases, outer_partitions
from .availability_audit import SAFE_NUM, select_on_training, predict, actions_for
from .models import classifier, ml_metrics
from .decision import observed_metrics


def correct(probabilities, temperature):
    """Rescale three-class log probabilities; preserve class order and sum to one."""
    if not np.isfinite(temperature) or temperature <= 0:
        raise ValueError('Temperature must be positive and finite')
    return softmax(np.log(np.clip(probabilities, 1e-12, 1)) / temperature, axis=1)


def fit_temperature(probabilities, target, classes):
    """Fit one parameter on calibration labels only; fixed bounds, no method search."""
    result = minimize_scalar(
        lambda t: log_loss(target, correct(probabilities, t), labels=classes),
        bounds=(0.25, 4.0), method='bounded',
    )
    if not result.success:
        raise RuntimeError('Temperature fit did not converge')
    return float(result.x)


def partitions(frame):
    """Yield disjoint model-fit, calibrator-fit and assessment learner groups."""
    for outer_fit, assessment in outer_partitions(frame):
        fit = frame.iloc[outer_fit]
        model_fit, calibration = next(outer_partitions(fit, seed=7105))
        indices = (outer_fit[model_fit], outer_fit[calibration], assessment)
        groups = [set(frame.iloc[idx].id_student) for idx in indices]
        if any(groups[i] & groups[j] for i in range(3) for j in range(i)):
            raise ValueError('Learner overlap in calibration audit')
        yield indices


def run():
    """Compare raw and corrected versions of the exact same fitted classifier."""
    spec = json.loads((ROOT / 'configs/availability_audit.json').read_text())
    chunks = pd.read_csv(ROOT / 'data/processed/development.csv', chunksize=1000)
    frame = pd.concat([training_cases(c) for c in chunks], ignore_index=True)
    features = SAFE_NUM + ['code_module']
    rows = []
    for fold, (fit_idx, cal_idx, check_idx) in enumerate(partitions(frame), 1):
        fit, cal, check = [frame.iloc[idx] for idx in (fit_idx, cal_idx, check_idx)]
        chosen, _ = select_on_training(fit, SAFE_NUM, spec)
        model = classifier(chosen, spec['seed'], SAFE_NUM).fit(fit[features], fit.target)
        _, cal_prob = predict(model, cal[features], features)
        temperature = fit_temperature(cal_prob, cal.target, model.classes_)
        _, raw = predict(model, check[features], features)
        for method, prob in [('raw', raw), ('temperature', correct(raw, temperature))]:
            risk = 1 - prob[:, list(model.classes_).index('Success')]
            actions = actions_for(check[features], risk)
            rows.append({
                'fold': fold, 'method': method, 'selected_model': chosen,
                'temperature': temperature if method == 'temperature' else 1.0,
                'model_fit_n': len(fit), 'calibration_n': len(cal),
                'mean_score': risk.mean(),
                **ml_metrics(check.target, prob, model.classes_),
                **observed_metrics(check.target, actions),
            })
        print('Calibration fold', fold, 'completed', flush=True)
    pd.DataFrame(rows).to_csv(ROOT / 'outputs/probability_audit.csv', index=False)


if __name__ == '__main__':
    run()
