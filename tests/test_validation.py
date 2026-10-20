from pathlib import Path
import json
import tempfile
import unittest
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / 'src'))
sys.path.insert(0,str(ROOT / 'scripts'))
import pandas as pd
from fire_risk.validation import require_tutor_approval, sha256, validate_panel, validate_availability
from check_publication import check_file


class ValidationTest(unittest.TestCase):
    def test_missing_or_outdated_approval_blocks(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.local') as temp:
            folder=Path(temp)
            self.assertTrue(folder.resolve().is_relative_to(ROOT.resolve()))
            manifest=folder/'manifest.json'; manifest.write_text('{}',encoding='utf-8')
            approval=folder/'approval.json'
            with self.assertRaises(ValueError): require_tutor_approval(approval,manifest)
            # Registro exclusivamente fictício para exercitar o contrato.
            data={'status':'approved','approved_by':'tutoria_ficticia','approved_at':'2026-01-01',
                  'evidence_ref':'evidencia_ficticia','dataset_manifest_sha256':sha256(manifest)}
            approval.write_text(json.dumps(data),encoding='utf-8')
            require_tutor_approval(approval,manifest)
            manifest.write_text('{"version":2}',encoding='utf-8')
            with self.assertRaises(ValueError): require_tutor_approval(approval,manifest)

    def test_duplicate_keys_missing_target_and_constant_class_fail(self):
        frame=pd.DataFrame({'region':['a','b','c','d'],'date':[1,1,1,1],'target':[0,1,0,1]})
        validate_panel(frame,['region','date'],'target',min_rows=4)
        for bad in [pd.concat([frame,frame.iloc[:1]]), frame.assign(target=None), frame.assign(target=0)]:
            with self.assertRaises(ValueError): validate_panel(bad,['region','date'],'target',min_rows=4)

    def test_future_information_fails(self):
        frame=pd.DataFrame({'available':[2],'issued':[1],'target_end':[3]})
        with self.assertRaises(ValueError): validate_availability(frame,'available','issued','target_end')
        validate_availability(frame.assign(available=0),'available','issued','target_end')

    def test_publication_blocks_paths_and_notebook_outputs(self):
        self.assertTrue(check_file(ROOT,'data/example.csv'))
        self.assertTrue(check_file(ROOT,'.local/approval.json'))
        with tempfile.TemporaryDirectory(dir=ROOT / '.local') as temp:
            folder=Path(temp); path=folder/'demo.ipynb'
            self.assertTrue(folder.resolve().is_relative_to(ROOT.resolve()))
            path.write_text(json.dumps({'cells':[{'cell_type':'code','outputs':[{}],'execution_count':1}]}),encoding='utf-8')
            self.assertTrue(check_file(folder,'demo.ipynb'))

    def test_publication_checks_supplied_git_blob(self):
        # Só um marcador sintético, sem chave, para verificar o conteúdo do índice.
        marker = ('-----BEGIN ' + 'PRIVATE KEY-----').encode('utf-8')
        self.assertTrue(check_file(ROOT,'example.py',contents=marker))


if __name__ == '__main__': unittest.main()
