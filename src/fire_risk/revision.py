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


def development_review(panel):
    # Filtra antes de calcular qualquer estatística ou ajustar modelo.
    development = panel.loc[panel['split'].isin(['train', 'validation', 'gap'])
                            & panel['data'].le(pd.Timestamp('2025-02-02'))].copy()
    train = development.loc[development['split'].eq('train')]
    valid = development.loc[development['split'].eq('validation')]
    validate_development(train, valid)
    fallback = train['target'].value_counts().idxmax()
    predictions = persistence(development, valid, fallback)
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
            'history_scope': 'painel elegível; não inclui detecções sem meteorologia elegível',
            'test_used_for_selection': False,
            'protocol': 'análise complementar após feedback; teste original já observado; sem promoção de modelo'}
