"""Optuna somente em folds cronológicos do treino; seleção em validação."""
import numpy as np
import optuna
from sklearn.metrics import f1_score
from sklearn.model_selection import TimeSeriesSplit
from threadpoolctl import threadpool_limits

from .metrics import prediction_metrics
from .panel import FEATURES, LABELS
from .training import candidates, validate_development


def chronological_folds(train, plan):
    days = np.sort(train['data'].unique())
    splitter = TimeSeriesSplit(n_splits=plan['cv_splits'],
                               test_size=plan['cv_validation_days'], gap=plan['cv_gap_days'])
    folds = []
    for fit_days, valid_days in splitter.split(days):
        fit = train[train['data'].isin(days[fit_days])]
        valid = train[train['data'].isin(days[valid_days])]
        if set(fit['target']) != set(LABELS) or set(valid['target']) != set(LABELS):
            raise ValueError('Fold temporal sem as três classes; não alterar cortes pelo teste.')
        folds.append((fit, valid))
    return folds


def parameters(family, trial):
    if family == 'logistica':
        return {'C': trial.suggest_float('C', 0.001, 100, log=True)}
    if family == 'floresta':
        return {'n_estimators': trial.suggest_categorical('n_estimators', [100, 200, 300]),
                'max_depth': trial.suggest_categorical('max_depth', [3, 5, 8, 12, None]),
                'min_samples_leaf': trial.suggest_int('min_samples_leaf', 2, 20),
                'max_features': trial.suggest_categorical('max_features', ['sqrt', 'log2', 1.0])}
    return {'learning_rate': trial.suggest_float('learning_rate', 0.02, 0.2, log=True),
            'max_iter': trial.suggest_categorical('max_iter', [80, 150, 250]),
            'max_leaf_nodes': trial.suggest_categorical('max_leaf_nodes', [7, 15, 31]),
            'l2_regularization': trial.suggest_float('l2_regularization', 0.001, 10, log=True),
            'min_samples_leaf': trial.suggest_categorical('min_samples_leaf', [5, 10, 20, 30])}


def estimator(family, params):
    model = candidates()[family]
    if family == 'logistica':
        params = {'logisticregression__' + key: value for key, value in params.items()}
    return model.set_params(**params)


def optimize_models(train, validation, plan):
    validate_development(train, validation)
    folds = chronological_folds(train, plan)
    studies, models, results = {}, {}, {}
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    with threadpool_limits(limits=1):
        for family in ('logistica', 'floresta', 'boosting'):
            def objective(trial):
                params = parameters(family, trial)
                scores = []
                for fit, valid in folds:
                    model = estimator(family, params)
                    model.fit(fit[list(FEATURES)], fit['target'])
                    predicted = model.predict(valid[list(FEATURES)])
                    scores.append(f1_score(valid['target'], predicted, labels=list(LABELS),
                                            average='macro', zero_division=0))
                return float(np.mean(scores))
            study = optuna.create_study(direction='maximize',
                sampler=optuna.samplers.TPESampler(seed=plan['seed']))
            study.optimize(objective, n_trials=plan['trials_per_family'], n_jobs=1)
            studies[family] = {'best_cv_f1_macro': study.best_value, 'best_params': study.best_params,
                               'trials': [{'number': t.number, 'value': t.value, 'params': t.params}
                                          for t in study.trials]}
        pool = candidates()
        pool.update({'otimizada_' + name: estimator(name, item['best_params']) for name, item in studies.items()})
        for name, model in pool.items():
            model.fit(train[list(FEATURES)], train['target'])
            results[name] = prediction_metrics(validation['target'], model.predict(validation[list(FEATURES)]),
                                               model.predict_proba(validation[list(FEATURES)]), model.classes_)
            models[name] = model
    selected = max(results, key=lambda n: (results[n]['f1_macro'], results[n]['recall_alto'], n))
    fold_summary = [{'train_end': str(a['data'].max().date()), 'validation_start': str(b['data'].min().date()),
                     'validation_end': str(b['data'].max().date()), 'train_rows': len(a), 'validation_rows': len(b)}
                    for a, b in folds]
    return models, {'studies': studies, 'validation': results, 'selected': selected,
                    'folds': fold_summary, 'test_evaluated': False}
