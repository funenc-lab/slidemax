import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PROJECT_ROOT / "skills" / "slidemax_workflow"
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from slidemax.svg_quality import summarize_svg_target


class SvgQualitySummaryTestCase(unittest.TestCase):
    def test_summarize_svg_target_prefers_svg_final_when_requested(self):
        clean_svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" '
            'width="1280" height="720"></svg>'
        )
        bad_svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" '
            'width="1280" height="720"><g opacity="0.4"><rect width="10" height="10" /></g></svg>'
        )

        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo_ppt169_20260313"
            (project / "svg_output").mkdir(parents=True)
            (project / "svg_final").mkdir()
            (project / "svg_output" / "slide_01_cover.svg").write_text(clean_svg, encoding="utf-8")
            (project / "svg_final" / "slide_01_cover.svg").write_text(bad_svg, encoding="utf-8")

            summary = summarize_svg_target(project, expected_format="ppt169", prefer_finalized=True)

        self.assertEqual(summary.stage_name, "svg_final")
        self.assertEqual(summary.total, 1)
        self.assertEqual(summary.errors, 1)
        self.assertFalse(summary.is_compatible)

    def test_summarize_svg_target_accepts_single_svg_file(self):
        clean_svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" '
            'width="1280" height="720"></svg>'
        )

        with tempfile.TemporaryDirectory() as tmp:
            svg_file = Path(tmp) / "slide_01_cover.svg"
            svg_file.write_text(clean_svg, encoding="utf-8")

            summary = summarize_svg_target(svg_file, expected_format="ppt169")

        self.assertEqual(summary.stage_name, "file")
        self.assertEqual(summary.total, 1)
        self.assertEqual(summary.errors, 0)
        self.assertTrue(summary.is_clean)

    def test_summarize_svg_target_reports_missing_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing_path = Path(tmp) / "missing_project"

            summary = summarize_svg_target(missing_path, expected_format="ppt169")

        self.assertEqual(summary.stage_name, "missing")
        self.assertEqual(summary.total, 0)
        self.assertEqual(summary.errors, 0)
        self.assertFalse(summary.is_compatible)


if __name__ == "__main__":
    unittest.main()
