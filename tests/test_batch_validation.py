import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PROJECT_ROOT / "skills" / "ppt_master_workflow"
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from pptmaster.batch_validation import BatchValidator


class BatchValidationTestCase(unittest.TestCase):
    def test_validate_directory_accepts_single_project_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo_ppt169_20260308"
            (project / "svg_output").mkdir(parents=True)
            (project / "images").mkdir()
            (project / "notes").mkdir()
            (project / "templates").mkdir()
            (project / "README.md").write_text("# demo\n", encoding="utf-8")
            (project / "设计规范与内容大纲.md").write_text("# spec\n", encoding="utf-8")
            (project / "svg_output" / "01_封面.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720"></svg>',
                encoding="utf-8",
            )

            validator = BatchValidator()
            results = validator.validate_directory(str(project))

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "demo")
        self.assertEqual(validator.summary["total"], 1)


if __name__ == "__main__":
    unittest.main()
