from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
from fire_risk.course import (COURSE_FILES, course_contract, create_course_manifest,
                              verify_course_manifest)
from fire_risk.validation import sha256
from check_delivery import check


class CourseTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / '.local')
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.raw = self.folder / 'raw'
        self.raw.mkdir()
        for name in COURSE_FILES:
            (self.raw / name).write_text('coluna_ficticia\nvalor_ficticio\n', encoding='utf-8')
        self.config = self.folder / 'contract.json'
        self.data = {'source': 'course', 'files': {n: sha256(self.raw / n) for n in COURSE_FILES}}
        self.config.write_text(json.dumps(self.data), encoding='utf-8')
        self.manifest = self.folder / 'manifest.json'

    def test_course_manifest_binds_all_files_without_approval(self):
        result = create_course_manifest(self.raw, self.config, self.manifest)
        self.assertEqual(result['source'], 'course')
        self.assertEqual(result['external_validation'], 'not_applicable')
        self.assertEqual(verify_course_manifest(self.manifest, self.raw, self.config), result)
        self.assertEqual({x['file'] for x in result['files']}, COURSE_FILES)

    def test_missing_changed_and_replaced_raw_block(self):
        create_course_manifest(self.raw, self.config, self.manifest)
        path = self.raw / 'MapBiomas.csv'
        path.write_text('diferente', encoding='utf-8')
        with self.assertRaises(ValueError):
            verify_course_manifest(self.manifest, self.raw, self.config)
        with self.assertRaises(ValueError):
            create_course_manifest(self.raw, self.config, self.manifest)
        path.unlink()
        with self.assertRaises(ValueError):
            create_course_manifest(self.raw, self.config, self.manifest)

    def test_external_or_incomplete_contract_rejected(self):
        for data in [{**self.data, 'source': 'external'},
                     {**self.data, 'files': {}},
                     {**self.data, 'files': dict.fromkeys(COURSE_FILES, 'not-a-hash')}]:
            self.config.write_text(json.dumps(data), encoding='utf-8')
            with self.assertRaises(ValueError):
                course_contract(self.config)

    def test_manifest_duplicates_and_contract_changes_block(self):
        result = create_course_manifest(self.raw, self.config, self.manifest)
        result['files'][0] = result['files'][1]
        self.manifest.write_text(json.dumps(result), encoding='utf-8')
        with self.assertRaises(ValueError):
            verify_course_manifest(self.manifest, self.raw, self.config)
        create_course_manifest(self.raw, self.config, self.manifest)
        self.config.write_text(json.dumps(self.data) + '\n', encoding='utf-8')
        with self.assertRaises(ValueError):
            verify_course_manifest(self.manifest, self.raw, self.config)

    def test_path_dispatch_preserves_external_approval_requirement(self):
        with patch('check_delivery.verify_course_manifest') as course, \
                patch('check_delivery.require_tutor_approval', side_effect=ValueError('pendente')) as external:
            self.assertIn('não aplicável', check({'path': '2', 'data_source': 'course'}, self.raw))
            course.assert_called_once()
            external.assert_not_called()
            with self.assertRaisesRegex(ValueError, 'pendente'):
                check({'path': '4', 'data_source': 'external'})
            external.assert_called_once()
            for config in [{'path': '2', 'data_source': 'external'},
                           {'path': '4', 'data_source': 'course'}, {'path': 'unknown'}]:
                with self.assertRaises(ValueError):
                    check(config, self.raw)
        with self.assertRaises(ValueError):
            check({'path': '2', 'data_source': 'course'})


if __name__ == '__main__':
    unittest.main()
