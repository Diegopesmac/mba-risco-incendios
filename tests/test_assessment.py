from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from fire_risk.artifacts import read_json, write_json
from fire_risk.assessment import simulated_cost, cost_sensitivity, humidity_hypothesis
from fire_risk.optimization import chronological_folds, optimize_models
from fire_risk.metrics import grouped_metrics, bootstrap_days
from fire_risk.finalization import evaluate_once
from fire_risk.panel import FEATURES
from fire_risk.validation import sha256


class AssessmentTest(unittest.TestCase):
    def setUp(self):
        self.plan = read_json(ROOT / 'configs/evaluation-plan.json')
        rows = []
        for day in pd.date_range('2025-01-03', '2025-02-02'):
            split = 'train' if day.day <= 25 and day.month == 1 else 'validation'
            if day == pd.Timestamp('2025-01-26'):
                continue
            for i, label in enumerate(('baixo','medio','alto')):
                rows.append({'id_municipio': f'{i:07}', 'data': day, 'target': label,
                             'split': split, 'eligible_stations': 1,
                             **{name: float(i + j) for j, name in enumerate(FEATURES)}})
        self.frame = pd.DataFrame(rows)
        self.train = self.frame[self.frame['split'] == 'train']
        self.valid = self.frame[self.frame['split'] == 'validation']

    def test_folds_separate_entire_dates_and_respect_gap(self):
        folds = chronological_folds(self.train, self.plan)
        self.assertEqual(len(folds), 3)
        for fit, valid in folds:
            self.assertTrue(fit['data'].max() + pd.Timedelta(days=1) < valid['data'].min())
            self.assertFalse(set(fit['data']) & set(valid['data']))

    def test_optuna_operates_without_test_partition(self):
        plan = {**self.plan, 'trials_per_family': 1}
        models, result = optimize_models(self.train, self.valid, plan)
        self.assertEqual(len(result['studies']), 3)
        self.assertEqual(len(models), 7)
        self.assertFalse(result['test_evaluated'])
        with self.assertRaises(ValueError):
            optimize_models(self.train, self.valid.assign(split='test'), plan)

    def test_cost_matrix_direction_and_sensitivity(self):
        scenario = self.plan['cost_scenario']
        self.assertEqual(simulated_cost(['alto'], ['baixo'], scenario)['total'], 200)
        self.assertEqual(simulated_cost(['baixo'], ['alto'], scenario)['total'], 30)
        self.assertEqual(simulated_cost(['alto'], ['baixo'], scenario, missed_high=2)['total'], 400)
        self.assertEqual(len(cost_sensitivity(['alto'], ['alto'], ['baixo'], scenario)), 12)
        with self.assertRaises(ValueError):
            simulated_cost(['baixo','alto'], ['baixo'], scenario)

    def test_groups_and_day_bootstrap_report_sparse_support(self):
        predicted = self.valid['target'].to_numpy()
        groups = grouped_metrics(self.valid, predicted)
        self.assertEqual(groups['station_coverage']['single']['f1_macro'], 1)
        self.assertTrue(any(g['sparse'] for g in groups['uf_code'].values()))
        result = bootstrap_days(self.valid, predicted, samples=20)
        self.assertEqual(result['f1_macro_percentile_95'], [1,1])

    def test_hypothesis_does_not_use_validation(self):
        with self.assertRaises(ValueError):
            humidity_hypothesis(self.valid, self.plan)
        self.assertEqual(humidity_hypothesis(self.train, self.plan)['status'], 'insufficient_pairs')

    def test_cached_final_evaluation_does_not_read_test_again(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.local') as tmp:
            root = Path(tmp)
            freeze = root / '.local/course/final/freeze.json'
            write_json(freeze, {'frozen': True})
            expected = {'freeze_sha256': sha256(freeze), 'test_evaluated': True}
            write_json(freeze.with_name('evaluation.json'), expected)
            with patch('fire_risk.finalization.verify_freeze', return_value={}), \
                    patch('fire_risk.finalization.duckdb.connect', side_effect=AssertionError('teste relido')):
                self.assertEqual(evaluate_once(root), expected)
                write_json(freeze, {'frozen': 'changed'})
                with self.assertRaises(ValueError):
                    evaluate_once(root)


if __name__ == '__main__':
    unittest.main()
