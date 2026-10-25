from pathlib import Path
import sys
import unittest

import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from fire_risk.panel import FEATURES
from fire_risk.training import compare_models, validate_development


class TrainingTest(unittest.TestCase):
    def setUp(self):
        self.train = self.frame('2025-01-10', 'train')
        self.valid = self.frame('2025-01-28', 'validation')

    def frame(self, day, split):
        values = np.tile(np.arange(3), 30)
        frame = pd.DataFrame({feature: values.astype(float) + i for i, feature in enumerate(FEATURES)})
        frame['data'] = pd.Timestamp(day)
        frame['id_municipio'] = [f'{i:07}' for i in range(len(frame))]
        frame['target'] = np.array(['baixo', 'medio', 'alto'])[values]
        frame['split'] = split
        return frame

    def test_benchmark_uses_development_only_and_reports_all_candidates(self):
        models, result = compare_models(self.train, self.valid)
        self.assertEqual(set(models), {'referencia', 'logistica', 'floresta', 'boosting'})
        self.assertFalse(result['test_evaluated'])
        self.assertFalse(result['operational_use_validated'])
        winner = result['models'][result['selected']]
        self.assertEqual(winner['f1_macro'], max(x['f1_macro'] for x in result['models'].values()))
        for name, values in result['models'].items():
            self.assertTrue(0 <= values['f1_macro'] <= 1)
            self.assertEqual(sum(sum(row) for row in values['confusion_matrix']), len(self.valid))
            predicted = set(models[name].predict(self.valid[list(FEATURES)]))
            if name == 'referencia':
                self.assertEqual(len(predicted), 1)
            else:
                self.assertEqual(predicted, {'baixo', 'medio', 'alto'})

    def test_final_test_and_relabelled_test_dates_are_rejected(self):
        for bad in [self.valid.assign(split='test'),
                    self.valid.assign(data=pd.Timestamp('2025-02-05'))]:
            with self.assertRaises(ValueError):
                compare_models(self.train, bad)

    def test_duplicates_missing_classes_and_nonfinite_features_block(self):
        for bad in [pd.concat([self.train, self.train.iloc[:1]]),
                    self.train.assign(target='baixo'), self.train.assign(chuva_d2=float('nan'))]:
            with self.assertRaises(ValueError):
                validate_development(bad, self.valid)


if __name__ == '__main__':
    unittest.main()
