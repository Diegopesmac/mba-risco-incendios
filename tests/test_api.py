import base64
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
from fire_risk.api import create_app
from fire_risk.bundle import encode_bundle, materialize
from fire_risk.serving import ModelService
from fire_risk.validation import sha256
from make_synthetic_bundle import create


class ApiTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / '.local')
        self.addCleanup(self.temp.cleanup)
        self.folder = create(Path(self.temp.name) / 'bundle')
        self.anchor = sha256(self.folder / 'manifest.json')
        self.client = TestClient(create_app(self.folder, self.anchor))
        self.request = {'municipio': '0000000', 'data_alvo': '2025-02-04',
                        'data_meteorologia': '2025-02-02', 'chuva_d2': 0.0,
                        'temperatura_d2': 1.0, 'umidade_d2': 2.0, 'vento_d2': 3.0}

    def test_real_serialized_model_contract_and_probabilities(self):
        self.assertEqual(self.client.get('/health').status_code, 200)
        response = self.client.post('/predict', json=self.request)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result['model_id'], 'synthetic-ci-only')
        self.assertAlmostEqual(sum(result['probabilidades_classes_indice'].values()), 1)
        self.assertFalse(result['uso_operacional_validado'])
        self.assertFalse(result['disponibilidade_historica_verificada'])
        self.assertTrue(result['municipio_presente_no_desenvolvimento'])
        self.assertEqual(self.client.get('/docs').status_code, 200)

    def test_invalid_extra_future_or_non_numeric_inputs_rejected(self):
        for change in [{'umidade_d2': 101}, {'chuva_d2': -1}, {'vento_d2': '3'},
                       {'umidade_d2': True}, {'municipio': '../bad'},
                       {'data_meteorologia': '2025-02-04'}, {'risco_fogo': 0.8},
                       {'temperatura_d2': None}]:
            with self.subTest(change=change):
                self.assertEqual(self.client.post('/predict', json={**self.request, **change}).status_code, 422)
        raw = self.client.post('/predict', content=b'{"umidade_d2":NaN}', headers={'Content-Type':'application/json'})
        self.assertEqual(raw.status_code, 422)

    def test_missing_model_returns_503_not_a_fake_prediction(self):
        client = TestClient(create_app())
        self.assertEqual(client.get('/health').status_code, 503)
        self.assertEqual(client.post('/predict', json=self.request).status_code, 503)

    def test_model_hash_rejected_before_unpickling(self):
        (self.folder / 'model.joblib').write_bytes(b'changed')
        with patch('fire_risk.serving.joblib.load', side_effect=AssertionError('unpickle')):
            with self.assertRaises(ValueError):
                ModelService(self.folder, self.anchor)
        self.assertEqual(TestClient(create_app(self.folder, self.anchor)).get('/health').status_code, 503)

    def test_bundle_roundtrip_and_manifest_anchor(self):
        payload = encode_bundle(self.folder)
        output = Path(self.temp.name) / 'decoded'
        materialize(payload, self.anchor, output)
        self.assertEqual(sha256(output / 'model.joblib'), sha256(self.folder / 'model.joblib'))
        self.assertEqual(ModelService(output, self.anchor).metadata['model_id'], 'synthetic-ci-only')
        for anchor in [None, '0' * 64]:
            with self.assertRaises(ValueError):
                materialize(payload, anchor, output)
        with self.assertRaises(ValueError):
            materialize(payload + '!' * 1_000_000, self.anchor, output)

    def test_out_of_range_and_new_municipality_are_explicit(self):
        response = self.client.post('/predict', json={**self.request, 'municipio':'9999999','temperatura_d2':50.0}).json()
        self.assertFalse(response['municipio_presente_no_desenvolvimento'])
        self.assertIn('temperatura_d2', response['variaveis_fora_faixa_desenvolvimento'])


if __name__ == '__main__':
    unittest.main()
