"""Métricas e incerteza descritiva; não ajusta modelos ou limiares."""
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, roc_auc_score

from .panel import LABELS


def prediction_metrics(actual, predicted, probabilities=None, classes=None):
    detail = classification_report(actual, predicted, labels=list(LABELS),
                                   output_dict=True, zero_division=0)
    result = {'rows': len(actual), 'accuracy': float(accuracy_score(actual, predicted)),
              'f1_macro': float(f1_score(actual, predicted, labels=list(LABELS), average='macro', zero_division=0)),
              'recall_alto': float(detail['alto']['recall']),
              'precision_macro': float(detail['macro avg']['precision']),
              'recall_macro': float(detail['macro avg']['recall']),
              'classification_report': detail, 'confusion_labels': list(LABELS),
              'confusion_matrix': confusion_matrix(actual, predicted, labels=list(LABELS)).tolist(),
              'auc_ovr_macro': None}
    if probabilities is not None and set(actual) == set(LABELS):
        order = sorted(LABELS)
        aligned = probabilities[:, [list(classes).index(label) for label in order]]
        result['auc_ovr_macro'] = float(roc_auc_score(actual, aligned, labels=order,
                                                    multi_class='ovr', average='macro'))
    return result


def grouped_metrics(frame, predicted):
    frame = frame.copy()
    frame['predicted'] = predicted
    frame['uf_code'] = frame['id_municipio'].str[:2]
    frame['station_coverage'] = np.where(frame['eligible_stations'] > 1, 'multiple', 'single')
    frame['week_start'] = (frame['data'] - pd.to_timedelta(frame['data'].dt.weekday, unit='D')).astype(str)
    groups = {}
    for field in ('uf_code', 'station_coverage', 'week_start'):
        groups[field] = {}
        for key, part in frame.groupby(field):
            metrics = prediction_metrics(part['target'], part['predicted'])
            metrics['high_support'] = int(part['target'].eq('alto').sum())
            metrics['sparse'] = len(part) < 30 or metrics['high_support'] < 10
            groups[field][str(key)] = metrics
    return groups


def bootstrap_days(frame, predicted, samples=1000, seed=42):
    rng = np.random.default_rng(seed)
    days = frame['data'].unique()
    positions = [np.flatnonzero(frame['data'].to_numpy() == day) for day in days]
    actual, predicted = frame['target'].to_numpy(), np.asarray(predicted)
    values = []
    for _ in range(samples):
        selected = np.concatenate([positions[i] for i in rng.integers(0, len(days), len(days))])
        values.append(f1_score(actual[selected], predicted[selected], labels=list(LABELS),
                               average='macro', zero_division=0))
    return {'method': 'resampling_target_days', 'samples': samples, 'unique_days': len(days),
            'f1_macro_percentile_95': np.quantile(values, [0.025, 0.975]).tolist(),
            'limitation': 'Intervalo descritivo; poucos dias, dependência entre dias e seleção espacial não resolvidas.'}
