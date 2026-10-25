"""Explicabilidade global, hipótese exploratória e custos fictícios."""
import numpy as np
from scipy.stats import wilcoxon
from sklearn.inspection import permutation_importance
from sklearn.metrics import f1_score, make_scorer
from threadpoolctl import threadpool_limits

from .panel import FEATURES, LABELS


def explain(model, validation, plan):
    with threadpool_limits(limits=1):
        result = permutation_importance(model, validation[list(FEATURES)], validation['target'],
            scoring=make_scorer(f1_score, average='macro', labels=list(LABELS), zero_division=0),
            n_repeats=plan['permutation_repeats'], random_state=plan['seed'], n_jobs=1)
    return sorted([{'feature': name, 'mean_f1_decrease': float(mean), 'std': float(std)}
                   for name, mean, std in zip(FEATURES, result.importances_mean, result.importances_std)],
                  key=lambda x: x['mean_f1_decrease'], reverse=True)


def humidity_hypothesis(train, plan):
    if not train['split'].eq('train').all():
        raise ValueError('Hipótese utiliza somente treino.')
    frame = train.assign(high=train['target'].eq('alto'))
    grouped = frame.groupby(['id_municipio', 'high'])['umidade_d2'].agg(['median', 'count'])
    medians = grouped['median'].unstack('high')
    counts = grouped['count'].unstack('high')
    if True not in medians.columns or False not in medians.columns:
        return {'status': 'insufficient_pairs', 'municipalities': 0}
    eligible = (counts[True] >= plan['hypothesis']['minimum_days_per_condition']) & (
                counts[False] >= plan['hypothesis']['minimum_days_per_condition'])
    differences = (medians.loc[eligible, True] - medians.loc[eligible, False]).dropna().round(6)
    result = {'status': 'computed' if len(differences) >= 5 else 'insufficient_pairs',
              'municipalities': len(differences), 'alpha': plan['hypothesis']['alpha'],
              'null': plan['hypothesis']['null'], 'sample': 'training_only',
              'median_difference_original_scale': float(differences.median()) if len(differences) else None,
              'limitation': 'Exploratório; seleção por detecções, dependência espacial e relação do índice com meteorologia impedem inferência causal.'}
    if len(differences) >= 5:
        p = 1.0 if differences.eq(0).all() else float(wilcoxon(differences, alternative='two-sided').pvalue)
        result.update(p_value=p, reject_under_assumptions=p < result['alpha'])
    return result


def simulated_cost(actual, predicted, scenario, missed_high=1, overalert=1):
    labels = scenario['labels']
    costs = np.asarray(scenario['actual_by_predicted'], dtype=float).copy()
    if costs.shape != (3, 3) or not np.isfinite(costs).all() or (costs < 0).any():
        raise ValueError('Matriz de custos fictícios inválida.')
    costs[2, :2] *= missed_high
    for i in range(3):
        costs[i, i + 1:] *= overalert
    values = [costs[labels.index(a), labels.index(p)] for a, p in zip(actual, predicted, strict=True)]
    return {'total': float(np.sum(values)), 'per_decision': float(np.mean(values)),
            'currency': scenario['currency'], 'kind': 'fictional_academic_simulation'}


def cost_sensitivity(actual, predicted, reference, scenario):
    rows = []
    for missed in scenario['missed_high_multipliers']:
        for alert in scenario['overalert_multipliers']:
            model = simulated_cost(actual, predicted, scenario, missed, alert)
            base = simulated_cost(actual, reference, scenario, missed, alert)
            rows.append({'missed_high_multiplier': missed, 'overalert_multiplier': alert,
                          'model': model, 'reference': base,
                          'reference_minus_model': base['total'] - model['total']})
    return rows
