"""Inferência de um bundle confiável, com contrato e hash verificados."""
from importlib.metadata import version
from pathlib import Path

import joblib
import pandas as pd
from threadpoolctl import threadpool_limits

from .artifacts import read_json
from .panel import FEATURES, LABELS
from .validation import sha256


class ModelService:
    def __init__(self, directory, expected_manifest_sha256=None):
        self.directory = Path(directory)
        manifest_path = self.directory / 'manifest.json'
        if expected_manifest_sha256 and sha256(manifest_path) != expected_manifest_sha256:
            raise ValueError('Manifesto do modelo divergente.')
        self.metadata = read_json(manifest_path)
        if self.metadata.get('features') != list(FEATURES) or self.metadata.get('labels') != list(LABELS):
            raise ValueError('Contrato de inferência incompatível.')
        if self.metadata.get('file') != 'model.joblib':
            raise ValueError('Nome de artefato inválido.')
        model_path = self.directory / 'model.joblib'
        if sha256(model_path) != self.metadata['sha256']:
            raise ValueError('Modelo diverge do hash esperado.')
        if version('scikit-learn') != self.metadata['versions']['scikit-learn']:
            raise ValueError('Versão de scikit-learn incompatível com o modelo.')
        self.model = joblib.load(model_path)
        if set(self.model.classes_) != set(LABELS):
            raise ValueError('Modelo não contém as três classes.')

    def predict(self, features, municipality):
        frame = pd.DataFrame([{key: features[key] for key in FEATURES}])
        with threadpool_limits(limits=1):
            predicted = str(self.model.predict(frame)[0])
            probabilities = self.model.predict_proba(frame)[0]
        extrapolated = [key for key in FEATURES
                        if not self.metadata['training_ranges'][key][0] <= features[key] <= self.metadata['training_ranges'][key][1]]
        return {'classe_indice': predicted,
                'probabilidades_classes_indice': {str(label): float(value)
                                                  for label, value in zip(self.model.classes_, probabilities, strict=True)},
                'model_id': self.metadata['model_id'], 'modelo': self.metadata['selected'],
                'municipio_presente_no_desenvolvimento': municipality in self.metadata['municipalities'],
                'variaveis_fora_faixa_desenvolvimento': extrapolated,
                'uso_operacional_validado': False,
                'interpretacao': 'Classes do índice registrado, condicionadas à amostragem de detecções; probabilidades do modelo não são probabilidades físicas de incêndio.'}
