from pathlib import Path
import io
import json
import sys
import tempfile
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
from fire_risk.submission import (DICTIONARY, PANEL_FILE, NOTEBOOKS, read_panel,
                                  sha256_bytes, training_correlations, verify_submission)
from check_publication import check_file
from build_submission import export_evidence


def synthetic():
    rows = []
    for index, (day, target, value) in enumerate([
            ('2025-01-03', 'baixo', .2), ('2025-01-04', 'medio', .5),
            ('2025-01-05', 'alto', .9), ('2025-02-04', 'alto', .8)]):
        day = pd.Timestamp(day)
        rows.append({'id_municipio': '0000001', 'data': day, 'target_index': value,
                     'detection_records': 2, 'valid_index_records': 1,
                     'weather_date': day-pd.Timedelta(days=2), 'chuva_d2': float(index),
                     'temperatura_d2': float(index+20), 'umidade_d2': float(80-index),
                     'vento_d2': float(index+1), 'eligible_stations': 1, 'target': target,
                     'split': 'train' if index < 3 else 'test', 'prediction_issued_at': day,
                     'target_window_end': day+pd.Timedelta(days=1),
                     'assumed_features_available_at': day, 'historical_publication_verified': False})
    return pd.DataFrame(rows)


class SubmissionTest(unittest.TestCase):
    def test_reconstruction_without_deploy_does_not_reuse_old_publication(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.local') as temp:
            folder = Path(temp)
            source, output = folder / 'source', folder / 'exported'
            for name in ['manifest.json', 'panel-summary.json', 'prepared/resumo_preparacao.json',
                         'optimization/results.json', 'final/freeze.json', 'final/evaluation.json']:
                path = source / name
                path.parent.mkdir(exist_ok=True, parents=True)
                path.write_bytes(b'{"fixture":true}\r\n')
            output.mkdir()
            (output / 'deployment.json').write_text('{"status":"live"}', encoding='utf-8')
            export_evidence(source, output)
            record = json.loads((output / 'deployment.json').read_text(encoding='utf-8'))
            self.assertEqual(record['status'], 'not_deployed')
            self.assertFalse(record['http_verified'])
            self.assertEqual((output / 'freeze.json').read_bytes(), (source / 'final/freeze.json').read_bytes())
            original = b'{"status":"live","http_verified":true}\r\n'
            (source / 'deployment.json').write_bytes(original)
            export_evidence(source, output)
            self.assertEqual((output / 'deployment.json').read_bytes(), original)

    def test_csv_roundtrip_preserves_zero_prefix_and_rejects_schema_and_labels(self):
        frame = synthetic()
        loaded = read_panel(io.StringIO(frame.to_csv(index=False)))
        self.assertEqual(loaded['id_municipio'].iloc[0], '0000001')
        self.assertEqual(set(loaded), set(DICTIONARY))
        for bad in [frame.assign(extra=1), frame.assign(target='baixo'),
                    frame.assign(historical_publication_verified=True), frame.assign(split='test'),
                    frame.assign(valid_index_records=5)]:
            with self.subTest(columns=list(bad)):
                with self.assertRaises(ValueError):
                    read_panel(io.StringIO(bad.to_csv(index=False)))

    def test_correlations_ignore_poisoned_test_and_keep_ordinal_class_order(self):
        frame = synthetic()
        training, before = training_correlations(frame)
        poisoned = frame.copy()
        poisoned.loc[poisoned['split'].eq('test'), ['target_index', 'chuva_d2']] = float('nan')
        _, after = training_correlations(poisoned)
        self.assertEqual(training['target_ordinal'].tolist(), [0, 1, 2])
        for method in before:
            pd.testing.assert_frame_equal(before[method], after[method])

    def test_manifest_detects_changed_payload_and_missing_panel(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.local') as temp:
            root = Path(temp)
            (root / 'submission').mkdir()
            output = root / PANEL_FILE
            synthetic().to_csv(output, index=False)
            manifest = {'rows': 4, 'splits': {'train': 3, 'test': 1},
                        'files': {PANEL_FILE: sha256_bytes(output.read_bytes())}}
            (root / 'submission/manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
            verify_submission(root)
            output.write_bytes(output.read_bytes().replace(b'0.2', b'0.3'))
            with self.assertRaises(ValueError):
                verify_submission(root)
            manifest['files'] = {}
            (root / 'submission/manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
            with self.assertRaises(ValueError):
                verify_submission(root)

    def test_publication_exception_is_narrow_and_requires_successful_execution(self):
        content = json.dumps({'cells': [{'cell_type': 'code', 'execution_count': 1,
                                         'outputs': [{'output_type': 'stream', 'text': 'ok'}]}]}).encode()
        self.assertFalse(check_file(ROOT, NOTEBOOKS[0], content))
        self.assertTrue(check_file(ROOT, 'notebooks/unreviewed.ipynb', content))
        incomplete = json.loads(content)
        incomplete['cells'][0]['execution_count'] = None
        self.assertTrue(check_file(ROOT, NOTEBOOKS[0], json.dumps(incomplete).encode()))
        incomplete['cells'][0].update(execution_count=1, outputs=[{'output_type': 'error'}])
        self.assertTrue(check_file(ROOT, NOTEBOOKS[0], json.dumps(incomplete).encode()))
        self.assertTrue(check_file(ROOT, 'submission/another.csv', b'a\n1'))
        self.assertTrue(check_file(ROOT, PANEL_FILE, b'a\n1'))


if __name__ == '__main__':
    unittest.main()
