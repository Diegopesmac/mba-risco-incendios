import csv
import io
from pathlib import Path
import tempfile
import unittest
import zipfile
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from fire_risk.sources import profile_reference


class SourceTest(unittest.TestCase):
    def test_missing_calendar_day_is_reported_not_labeled(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.local') as tmp:
            root=Path(tmp).resolve()
            self.assertTrue(root.is_relative_to(ROOT.resolve()))
            data=io.StringIO()
            writer=csv.writer(data)
            writer.writerow(['id_bdq','foco_id','lat','lon','data_pas','pais','estado','municipio','bioma'])
            for i,day in enumerate(['2024-02-28','2024-03-01']):
                writer.writerow([str(i),f'ficticio-{i}','0','0',day+' 12:00:00','FICTICIO','FICTICIO','FICTICIO','FICTICIO'])
            path=root/'test.zip'
            with zipfile.ZipFile(path,'w') as archive:
                archive.writestr('test.csv',data.getvalue())
            result=profile_reference(path)
            self.assertEqual(result['calendar_days_without_records'],['2024-02-29'])
            self.assertEqual(result['rows'],2)
            self.assertEqual(result['target'],'not_defined')


if __name__ == '__main__': unittest.main()
