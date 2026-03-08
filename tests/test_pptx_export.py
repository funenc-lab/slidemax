import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PROJECT_ROOT / "skills" / "slidemax_workflow"
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from slidemax.config import CANVAS_FORMATS
from slidemax.exporters.pptx_assets import get_slide_dimensions
from slidemax.pptx_export import (
    DEFAULT_TRANSITION_CHOICES,
    build_cli_parser,
    build_native_svg_dependencies,
    resolve_context,
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

    def test_resolve_context_auto_splits_total_notes_before_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo_ppt169_20260308"
            (project / "svg_output").mkdir(parents=True)
            (project / "notes").mkdir()
            (project / "svg_output" / "01_封面.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720"></svg>',
                encoding="utf-8",
            )
            (project / "notes" / "total.md").write_text(
                '## 01 封面\nhello export notes\n',
                encoding="utf-8",
            )

            request = type(
                "Request",
                (),
                {
                    "project_path": project,
                    "output": None,
                    "source": "output",
                    "canvas_format": None,
                    "quiet": True,
                    "use_compat_mode": True,
                    "transition": None,
                    "transition_duration": 0.5,
                    "auto_advance": None,
                    "enable_notes": True,
                },
            )()

            context = resolve_context(
                request,
                get_project_info_func=lambda _path: {"name": "demo", "format": "ppt169"},
            )

            self.assertIn("01_封面", context.notes)
            self.assertEqual(context.notes["01_封面"], "hello export notes")
            self.assertTrue((project / "notes" / "01_封面.md").exists())


if __name__ == "__main__":
    unittest.main()
