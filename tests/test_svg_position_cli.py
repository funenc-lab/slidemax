import argparse
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PROJECT_ROOT / "skills" / "slidemax_workflow"
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from slidemax.svg_position_cli import analyze_svg_file, build_chart_area, execute_parsed_command


class _FakeParser:
    def __init__(self) -> None:
        self.help_called = False

    def print_help(self) -> None:
        self.help_called = True


class SvgPositionCliTestCase(unittest.TestCase):
    def test_build_chart_area_parses_four_numbers(self):
        area = build_chart_area("10,20,110,220")

        self.assertIsNotNone(area)
        self.assertEqual((area.x_min, area.y_min, area.x_max, area.y_max), (10, 20, 110, 220))

    def test_analyze_svg_file_reports_shape_counts(self):
        svg = '''<svg viewBox="0 0 1280 720" width="1280" height="720" xmlns="http://www.w3.org/2000/svg">
<rect x="10" y="20" width="100" height="80" />
<circle cx="40" cy="50" r="12" />
<polyline points="0,0 10,10 20,5" />
<path d="M0 0 L10 10" />
</svg>'''
        with tempfile.TemporaryDirectory() as tmp:
            svg_path = Path(tmp) / "sample.svg"
            svg_path.write_text(svg, encoding="utf-8")

            report = analyze_svg_file(svg_path)

        self.assertIn("SVG analysis: sample.svg", report)
        self.assertIn("Canvas viewBox: 0 0 1280 720", report)
        self.assertIn("  - rect: 1", report)
        self.assertIn("  - circle: 1", report)
        self.assertIn("  - polyline/polygon: 1", report)
        self.assertIn("  - path: 1", report)

    def test_execute_parsed_command_requires_chart_type_for_calc(self):
        parser = _FakeParser()
        outputs = []
        args = argparse.Namespace(command="calc", chart_type=None)

        exit_code = execute_parsed_command(args, parser, output_fn=outputs.append)

        self.assertEqual(exit_code, 1)
        self.assertTrue(parser.help_called)
        self.assertEqual(outputs, [])

    def test_execute_parsed_command_routes_from_json_output(self):
        parser = _FakeParser()
        outputs = []
        args = argparse.Namespace(command="from-json", config_file="demo.json")

        exit_code = execute_parsed_command(
            args,
            parser,
            output_fn=outputs.append,
            json_loader=lambda path: f"Loaded config: {path}",
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(outputs, ["Loaded config: demo.json"])


if __name__ == "__main__":
    unittest.main()
