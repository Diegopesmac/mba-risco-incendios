"""Comparação inicial em desenvolvimento/validação, sem avaliar teste final."""
from time import perf_counter

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                             f1_score, roc_auc_score)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from .panel import FEATURES, LABELS, temporal_split


def candidates():
    return {
        'referencia': DummyClassifier(strategy='prior'),
        'logistica': make_pipeline(StandardScaler(), LogisticRegression(
            max_iter=2000, class_weight='balanced', random_state=42)),
        'floresta': RandomForestClassifier(n_estimators=200, max_depth=8,
            min_samples_leaf=3, class_weight='balanced_subsample', random_state=42, n_jobs=1),
        'boosting': HistGradientBoostingClassifier(max_iter=150, learning_rate=0.07,
            max_leaf_nodes=15, l2_regularization=1, class_weight='balanced',
            early_stopping=False, random_state=42),
    }


def validate_development(train, validation):
    for frame, name in ((train, 'train'), (validation, 'validation')):
        if frame.empty or not frame['split'].eq(name).all():
            raise ValueError('Somente treino e validação nas respectivas partições.')
        if not frame['data'].map(temporal_split).eq(name).all():
            raise ValueError('Datas divergem do plano temporal.')
        if frame[['id_municipio', 'data']].isna().any().any() or frame.duplicated(['id_municipio', 'data']).any():
            raise ValueError('Chaves de desenvolvimento ausentes ou repetidas.')
        if not np.isfinite(frame[list(FEATURES)].to_numpy(dtype=float)).all():
            raise ValueError('Features devem ser numéricas e finitas.')
        if set(frame['target']) != set(LABELS):
            raise ValueError('Cada partição deve conter as três classes antes de comparar modelos.')
    if pd.to_datetime(train['data']).max() >= pd.to_datetime(validation['data']).min():
        raise ValueError('Treino deve anteceder validação.')


def _compare_models(train, validation):
    validate_development(train, validation)
    x_train, y_train = train[list(FEATURES)], train['target']
    x_valid, y_valid = validation[list(FEATURES)], validation['target']
    fitted, results = {}, {}
    for name, model in candidates().items():
        start = perf_counter()
        model.fit(x_train, y_train)
        fit_seconds = perf_counter() - start
        start = perf_counter()
        prediction = model.predict(x_valid)
        infer_seconds = perf_counter() - start
        probabilities = model.predict_proba(x_valid)
        order = sorted(LABELS)
        probabilities = probabilities[:, [list(model.classes_).index(label) for label in order]]
        detail = classification_report(y_valid, prediction, labels=list(LABELS),
                                       output_dict=True, zero_division=0)
        results[name] = {
            'accuracy': float(accuracy_score(y_valid, prediction)),
            'f1_macro': float(f1_score(y_valid, prediction, labels=list(LABELS),
                                      average='macro', zero_division=0)),
            'recall_alto': float(detail['alto']['recall']),
            'precision_macro': float(detail['macro avg']['precision']),
            'recall_macro': float(detail['macro avg']['recall']),
            'auc_ovr_macro': float(roc_auc_score(y_valid, probabilities, labels=order,
                                                multi_class='ovr', average='macro')),
            'confusion_labels': list(LABELS),
            'confusion_matrix': confusion_matrix(y_valid, prediction, labels=list(LABELS)).tolist(),
            'classification_report': detail, 'fit_seconds': fit_seconds,
            'inference_seconds': infer_seconds,
        }
        fitted[name] = model
    # Referência participa da comparação e pode vencer; não promover modelo pior.
    selected = max(results, key=lambda name: (results[name]['f1_macro'],
                                             results[name]['recall_alto'], name))
    return fitted, {'schema_version': 1, 'stage': 'initial_validation_only',
                    'selection_rule': 'f1_macro; desempate recall_alto e nome',
                    'selected': selected, 'train_rows': len(train),
                    'validation_rows': len(validation), 'features': list(FEATURES),
                    'models': results, 'test_evaluated': False,
                    'hyperparameter_search_completed': False,
                    'operational_use_validated': False}


def compare_models(train, validation):
    with threadpool_limits(limits=1):
        return _compare_models(train, validation)
