from pathlib import Path
import sys
import unittest
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from fire_risk.revision import persistence, development_review
from fire_risk.submission import verify_submission

class RevisionTest(unittest.TestCase):
    def test_persistence_cutoff_no_future_and_cold_start(self):
        history = pd.DataFrame({'id_municipio':['a']*3, 'data':pd.to_datetime(['2025-01-01','2025-01-03','2025-01-04']), 'target':['baixo','medio','alto']})
        query = pd.DataFrame({'id_municipio':['a','a','b'], 'data':pd.to_datetime(['2025-01-04','2025-01-05','2025-01-05'])})
        result = persistence(history, query, 'baixo')
        self.assertEqual(result['predicted'].tolist(), ['baixo','medio','baixo'])
        self.assertEqual(result['fallback_used'].tolist(), [False,False,True])
        history.loc[2,'target']='baixo'
        pd.testing.assert_frame_equal(result,persistence(history,query,'baixo'))

    def test_development_ignores_poisoned_test(self):
        panel,_ = verify_submission(ROOT)
        before = development_review(panel)
        panel.loc[panel['split'].eq('test'), ['target','chuva_d2']] = None
        self.assertEqual(before, development_review(panel))

    def test_raw_history_includes_dates_without_weather_and_excludes_test(self):
        import tempfile
        from fire_risk.revision import build_label_history
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp)/'fires.csv'
            source.write_text('id_municipio;data_hora;risco_fogo\n0000001;2024-12-01 00:00:00;0.2\n0000001;2024-12-01 01:00:00;0.8\n0000001;2025-01-01 00:00:00;-999\n0000001;2025-02-04 00:00:00;1\n',encoding='utf-8')
            result=build_label_history(source)
            self.assertEqual(len(result),1)
            self.assertEqual(result.iloc[0]['target'],'medio')
            self.assertEqual(result.iloc[0]['data'],pd.Timestamp('2024-12-01'))
            extended=build_label_history(source, '2025-02-04')
            self.assertEqual(len(extended),2)
            self.assertEqual(extended.iloc[-1]['data'],pd.Timestamp('2025-02-04'))

    def test_fixed_test_baseline_uses_d2_and_same_cost_matrix(self):
        import json
        from fire_risk.revision import evaluate_test_persistence
        panel=pd.DataFrame({'id_municipio':['a','b','a','a','b'],
            'data':pd.to_datetime(['2025-01-01','2025-01-01','2025-02-04','2025-02-05','2025-02-05']),
            'split':['train','train','test','test','test'], 'target':['baixo','baixo','alto','medio','alto']})
        history=pd.DataFrame({'id_municipio':['a']*3,
            'data':pd.to_datetime(['2025-02-02','2025-02-03','2025-02-04']),
            'target':['baixo','medio','alto']})
        scenario=json.loads((ROOT/'configs/evaluation-plan.json').read_text())['cost_scenario']
        before=evaluate_test_persistence(panel,history,scenario)
        self.assertEqual(before['metrics']['rows'],3)
        self.assertEqual(before['simulated_cost']['total'],400)
        self.assertEqual(before['fallback_rows'],1)
        self.assertFalse(before['test_used_for_selection'])
        history.loc[2,'target']='baixo'
        self.assertEqual(before,evaluate_test_persistence(panel,history,scenario))
        self.assertEqual(len(before['cost_sensitivity']),12)

    def test_balance_selection_does_not_depend_on_validation_labels(self):
        from fire_risk.revision import tune_balance
        panel,_=verify_submission(ROOT)
        train=panel.loc[panel['split'].eq('train')]
        valid=panel.loc[panel['split'].eq('validation')].copy()
        _,before=tune_balance(train,valid)
        valid['target']=valid['target'].map({'baixo':'alto','alto':'medio','medio':'baixo'})
        _,after=tune_balance(train,valid)
        self.assertEqual(before['cv'],after['cv'])
        self.assertEqual(before['weights'],after['weights'])
        self.assertFalse(after['test_evaluated'])

if __name__ == '__main__':
    unittest.main()
