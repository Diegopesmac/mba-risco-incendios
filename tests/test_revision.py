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

if __name__ == '__main__':
    unittest.main()
