import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PROJECT_ROOT / "skills" / "ppt_master_workflow"
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from pptmaster.config import CANVAS_FORMATS
from pptmaster.exporters.pptx_assets import get_slide_dimensions
from pptmaster.pptx_export import (
    DEFAULT_TRANSITION_CHOICES,
    build_cli_parser,
    build_native_svg_dependencies,
)


class PptxExportTestCase(unittest.TestCase):
    def test_build_cli_parser_uses_canonical_defaults(self):
        parser = build_cli_parser()

        args = parser.parse_args(["demo_project"])

        self.assertEqual(args.project_path, "demo_project")
        self.assertEqual(args.source, "output")
        self.assertIsNone(args.format)
        self.assertEqual(
            {action.dest for action in parser._actions if action.dest == "transition"},
            {"transition"},
        )

    def test_build_native_svg_dependencies_wires_canonical_runtime_adapters(self):
        dependencies = build_native_svg_dependencies()

        self.assertEqual(dependencies.canvas_formats, CANVAS_FORMATS)
        self.assertIs(dependencies.get_slide_dimensions, get_slide_dimensions)
        self.assertIn("fade", DEFAULT_TRANSITION_CHOICES)
        self.assertTrue(callable(dependencies.detect_format_from_svg))
        self.assertTrue(callable(dependencies.markdown_to_plain_text))


if __name__ == "__main__":
    unittest.main()
