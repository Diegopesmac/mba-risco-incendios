"""Comparações complementares após revisão, sem substituir ciência congelada."""
import pandas as pd
from threadpoolctl import threadpool_limits
from .panel import FEATURES, LABELS
from .training import candidates, validate_development
from .metrics import prediction_metrics


def persistence(history, queries, fallback):
    """Última classe do painel elegível até D-2; disponibilidade histórica assumida."""
    if fallback not in LABELS:
        raise ValueError('Fallback inválido.')
    if history.duplicated(['id_municipio', 'data']).any():
        raise ValueError('Histórico tem chaves duplicadas.')
    if not history['target'].isin(LABELS).all():
        raise ValueError('Histórico tem classe inválida.')
    rows = []
    for row in queries.itertuples():
        cutoff = pd.Timestamp(row.data) - pd.Timedelta(days=2)
        eligible = history.loc[history['id_municipio'].eq(row.id_municipio)
                               & history['data'].le(cutoff)].sort_values('data')
        last = eligible.iloc[-1] if len(eligible) else None
        rows.append({'predicted': last['target'] if last is not None else fallback,
                     'history_date': last['data'] if last is not None else pd.NaT,
                     'fallback_used': last is None})
    return pd.DataFrame(rows, index=queries.index)


def development_review(panel, history=None):
    # Filtra antes de calcular qualquer estatística ou ajustar modelo.
    development = panel.loc[panel['split'].isin(['train', 'validation', 'gap'])
                            & panel['data'].le(pd.Timestamp('2025-02-02'))].copy()
    train = development.loc[development['split'].eq('train')]
    valid = development.loc[development['split'].eq('validation')]
    validate_development(train, valid)
    fallback = train['target'].value_counts().idxmax()
    predictions = persistence(development if history is None else history, valid, fallback)
    results = {'persistencia_d2': prediction_metrics(valid['target'], predictions['predicted'])}
    with threadpool_limits(limits=1):
        for label, weight in [('logistica_sem_pesos', None), ('logistica_balanceada', 'balanced')]:
            model = candidates()['logistica']
            model.set_params(logisticregression__class_weight=weight)
            model.fit(train[list(FEATURES)], train['target'])
            results[label] = prediction_metrics(valid['target'], model.predict(valid[list(FEATURES)]))
    counts = pd.crosstab(development['split'], development['target']).reindex(columns=LABELS, fill_value=0)
    return {'metrics': results, 'class_counts': counts.to_dict(orient='index'),
            'fallback_class': fallback, 'fallback_rows': int(predictions['fallback_used'].sum()),
            'history_scope': 'detecções originais sem filtro meteorológico' if history is not None else 'painel elegível',
            'test_used_for_selection': False,
            'protocol': 'análise complementar após feedback; teste original já observado; sem promoção de modelo'}


def build_label_history(fire_path, end_date='2025-02-02'):
    """Mediana diária de todos os índices válidos, antes de juntar meteorologia."""
    import duckdb
    from .panel import risk_class
    with duckdb.connect() as con:
        frame = con.execute("""SELECT id_municipio,
            try_cast(data_hora AS TIMESTAMP)::DATE AS data,
            median(try_cast(risco_fogo AS DOUBLE)) AS target_index
            FROM read_csv(?, header=true, delim=';', all_varchar=true)
            WHERE regexp_full_match(id_municipio, '[0-9]{7}')
              AND try_cast(data_hora AS TIMESTAMP)::DATE <= CAST(? AS DATE)
              AND isfinite(try_cast(risco_fogo AS DOUBLE))
              AND try_cast(risco_fogo AS DOUBLE) BETWEEN 0 AND 1
            GROUP BY ALL ORDER BY data,id_municipio""", [str(fire_path), str(pd.Timestamp(end_date).date())]).df()
    frame['data'] = pd.to_datetime(frame['data'])
    frame['target'] = frame['target_index'].map(risk_class)
    return frame[['id_municipio', 'data', 'target']]


def evaluate_test_persistence(panel, history, scenario):
    """Avalia a regra fixa no teste, sem ajustar modelo, pesos ou limiares."""
    from .assessment import simulated_cost
    train = panel.loc[panel['split'].eq('train')]
    test = panel.loc[panel['split'].eq('test')]
    if train.empty or test.empty or train['data'].max() >= test['data'].min():
        raise ValueError('Treino e teste temporal válidos são obrigatórios.')
    fallback = train['target'].value_counts().idxmax()
    predictions = persistence(history, test, fallback)
    actual, predicted = test['target'], predictions['predicted']
    sensitivity = []
    for missed in scenario['missed_high_multipliers']:
        for alert in scenario['overalert_multipliers']:
            sensitivity.append({'missed_high_multiplier': missed, 'overalert_multiplier': alert,
                'persistence': simulated_cost(actual, predicted, scenario, missed, alert)})
    return {'metrics': prediction_metrics(actual, predicted),
            'simulated_cost': simulated_cost(actual, predicted, scenario),
            'cost_sensitivity': sensitivity, 'fallback_class': fallback,
            'fallback_rows': int(predictions['fallback_used'].sum()),
            'test_used_for_selection': False,
            'protocol': 'Regra D−2 fixa, avaliação complementar; sem seleção ou retreinamento. Disponibilidade histórica assumida.'}


def tune_balance(train, validation):
    """Escolhe intensidade dos pesos por CV interna; validação só avalia."""
    from .optimization import chronological_folds
    validate_development(train, validation)
    folds = chronological_folds(train, {'cv_splits':3, 'cv_validation_days':4, 'cv_gap_days':1})
    powers = (0.0, 0.5, 1.0, 1.5)
    def fit(frame, power):
        counts = frame['target'].value_counts()
        weights = {label: float((len(frame)/(len(LABELS)*counts[label]))**power) for label in LABELS}
        model = candidates()['logistica'].set_params(logisticregression__class_weight=weights)
        model.fit(frame[list(FEATURES)], frame['target'])
        return model, weights
    with threadpool_limits(limits=1):
        scores = {}
        for power in powers:
            values = []
            for subset, held_out in folds:
                model, _ = fit(subset, power)
                values.append(prediction_metrics(held_out['target'], model.predict(held_out[list(FEATURES)]))['f1_macro'])
            scores[str(power)] = {'fold_f1':values, 'mean_f1':sum(values)/len(values)}
        chosen = max(powers, key=lambda power:(scores[str(power)]['mean_f1'], -power))
        model, weights = fit(train, chosen)
        result = prediction_metrics(validation['target'], model.predict(validation[list(FEATURES)]))
    return model, {'selected_power':chosen, 'weights':weights, 'cv':scores, 'validation':result,
                   'selection_data':'chronological_training_folds_only', 'test_evaluated':False}
