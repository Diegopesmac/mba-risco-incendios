from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_course_notebook import SECTIONS


class NotebookTest(unittest.TestCase):
    def test_generated_code_cells_have_valid_python_indentation(self):
        for index, (kind, content) in enumerate(SECTIONS):
            if kind == 'code':
                with self.subTest(index=index):
                    compile(content, '<course-notebook>', 'exec')


if __name__ == '__main__':
    unittest.main()
