import csv
import io
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from fire_risk.coverage import diagnose_state_days, FIELDS, STATES
from fire_risk.validation import sha256

spec = importlib.util.spec_from_file_location('build_entrega0', ROOT / 'scripts/build_entrega0.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class CoverageTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / '.local')
        self.folder = Path(self.temp.name).resolve()
        self.assertTrue(self.folder.is_relative_to(ROOT.resolve()))
        self.addCleanup(self.temp.cleanup)

    def archive(self, name, records, fields=None):
        fields = sorted(FIELDS) if fields is None else fields
        content = io.StringIO()
        writer = csv.DictWriter(content, fieldnames=fields)
        writer.writeheader()
        for identity, day, region in records:
            row = dict.fromkeys(fields, 'FICTICIO')
            row.update({key: value for key, value in {
                'id_bdq': identity, 'data_pas': day + ' 12:00:00', 'estado': region
            }.items() if key in fields})
            writer.writerow(row)
        path = self.folder / name
        with zipfile.ZipFile(path, 'w') as output:
            output.writestr('synthetic.csv', content.getvalue())
        return path

    def test_full_calendar_fixed_population_and_no_negative_labels(self):
        path = self.archive('a.zip', [('a', '2024-02-28', 'REGIAO A'),
                                      ('b', '2024-03-01', 'REGIAO A'),
                                      ('c', '2024-03-01', 'REGIAO A')])
        rows, report = diagnose_state_days({2024: path}, ('REGIAO A', 'REGIAO B'))
        self.assertEqual(len(rows), 366 * 2)
        self.assertEqual(rows[0]['date'], '2024-01-01')
        self.assertEqual(rows[-1]['date'], '2024-12-31')
        leap = [r for r in rows if r['date'] == '2024-02-29']
        self.assertTrue(all(r['archive_status'] == 'national_archive_gap' for r in leap))
        regional = next(r for r in rows if r['date'] == '2024-03-01' and r['state'] == 'REGIAO B')
        self.assertEqual(regional['archive_status'], 'no_regional_record')
        self.assertIsNone(regional['recorded_detection_count'])
        self.assertEqual(sum(r['recorded_detection_count'] or 0 for r in rows), 3)
        self.assertTrue(all(r['coverage_status'] == 'unverified' for r in rows))
        self.assertFalse(report['target_created'])
        self.assertFalse(report['training_authorized'])
        self.assertEqual(report['source_detection_rows'], 3)

    def test_duplicate_id_across_years_blocks(self):
        a = self.archive('a.zip', [('same', '2023-01-01', 'REGIAO')])
        b = self.archive('b.zip', [('same', '2024-01-01', 'REGIAO')])
        with self.assertRaisesRegex(ValueError, 'ID repetido'):
            diagnose_state_days({2023: a, 2024: b}, ('REGIAO',))

    def test_wrong_year_and_unknown_region_block(self):
        for day, region in [('2023-01-01', 'REGIAO'), ('2024-01-01', 'OUTRA')]:
            with self.subTest(day=day, region=region):
                path = self.archive('a.zip', [('a', day, region)])
                with self.assertRaisesRegex(ValueError, 'fora da população'):
                    diagnose_state_days({2024: path}, ('REGIAO',))

    def test_schema_and_missing_fields_block(self):
        path = self.archive('a.zip', [('a', '2024-01-01', 'REGIAO')], ['id_bdq'])
        with self.assertRaisesRegex(ValueError, 'Esquema'):
            diagnose_state_days({2024: path}, ('REGIAO',))
        path = self.archive('a.zip', [('', '2024-01-01', 'REGIAO')])
        with self.assertRaisesRegex(ValueError, 'incompleta'):
            diagnose_state_days({2024: path}, ('REGIAO',))

    def test_population_must_be_fixed_unique_and_nonempty(self):
        self.assertEqual(len(STATES), 27)
        self.assertEqual(len(set(STATES)), 27)
        for regions in [(), ('REGIAO', 'REGIAO')]:
            with self.assertRaisesRegex(ValueError, 'População'):
                diagnose_state_days({}, regions)
        with self.assertRaisesRegex(ValueError, 'arquivo anual'):
            diagnose_state_days({})

    def test_delivery_rejects_stale_manifest_or_regional_csv(self):
        manifest = self.folder / 'manifest.json'
        output = self.folder / 'state-days.csv'
        summary_path = self.folder / 'state-days-summary.json'
        manifest.write_text('{}', encoding='utf-8')
        output.write_text('synthetic', encoding='utf-8')
        self.assertIsNone(builder.regional_evidence(self.folder, manifest))
        summary = {'manifest_sha256': sha256(manifest), 'output_sha256': sha256(output)}
        summary_path.write_text(json.dumps(summary), encoding='utf-8')
        self.assertEqual(builder.regional_evidence(self.folder, manifest), summary)
        for path in (manifest, output):
            original = path.read_bytes()
            path.write_bytes(original + b'changed')
            with self.assertRaisesRegex(ValueError, 'desatualizado'):
                builder.regional_evidence(self.folder, manifest)
            path.write_bytes(original)


if __name__ == '__main__':
    unittest.main()
