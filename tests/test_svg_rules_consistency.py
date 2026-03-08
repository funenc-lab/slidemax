import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PROJECT_ROOT / "skills" / "slidemax_workflow"
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from slidemax.config import SVG_CONSTRAINTS
from slidemax.error_helper import ErrorHelper
from slidemax.svg_quality import SVGQualityChecker
from slidemax.svg_rules import (
    RECOMMENDED_SYSTEM_FONTS,
    build_error_solutions,
    build_svg_constraints,
    get_compound_detection_specs,
    get_regex_detection_specs,
    get_substring_detection_specs,
)


class SvgRulesConsistencyTestCase(unittest.TestCase):
    def test_config_constraints_match_canonical_svg_rules(self):
        self.assertEqual(SVG_CONSTRAINTS, build_svg_constraints())

    def test_error_helper_uses_canonical_svg_solutions(self):
        canonical = build_error_solutions()
        for error_code in [
            "foreignobject_detected",
            "clippath_detected",
            "mask_detected",
            "style_element_detected",
            "symbol_use_detected",
            "marker_end_detected",
            "rgba_detected",
            "animation_detected",
            "script_detected",
        ]:
            self.assertEqual(ErrorHelper.ERROR_SOLUTIONS[error_code], canonical[error_code])

    def test_svg_quality_checker_detects_canonical_rule_messages(self):
        svg = '''<svg viewBox="0 0 1280 720" width="1280" height="720" xmlns="http://www.w3.org/2000/svg">
<style>.bad{fill:red;}</style>
<defs><symbol id="shape"><rect width="10" height="10" /></symbol></defs>
<use href="#shape" />
<path d="M0 0 L10 10" marker-end="url(#arrow)" />
<g opacity="0.5"><rect width="100" height="100" /></g>
</svg>'''

        with tempfile.TemporaryDirectory() as tmp:
            svg_path = Path(tmp) / "bad.svg"
            svg_path.write_text(svg, encoding="utf-8")

            result = SVGQualityChecker().check_file(str(svg_path), expected_format="ppt169")

        expected_errors = {
            spec.error_message for spec in get_substring_detection_specs()
            if spec.error_code == "style_element_detected"
        }
        expected_errors.update(
            spec.error_message for spec in get_regex_detection_specs()
            if spec.error_code in {"marker_end_detected", "group_opacity_detected"}
        )
        expected_errors.update(
            spec.error_message for spec in get_compound_detection_specs()
            if spec.error_code == "symbol_use_detected"
        )

        self.assertTrue(expected_errors.issubset(set(result["errors"])))

    def test_recommended_fonts_are_shared(self):
        self.assertEqual(
            SVG_CONSTRAINTS["recommended_fonts"],
            RECOMMENDED_SYSTEM_FONTS,
        )

    def test_svg_quality_checker_allows_safe_defs_ids(self):
        svg = '''<svg viewBox="0 0 1280 720" width="1280" height="720" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="grad"><stop offset="0%" stop-color="#000"/><stop offset="100%" stop-color="#fff"/></linearGradient></defs>
<rect width="1280" height="720" fill="url(#grad)" />
</svg>'''

        with tempfile.TemporaryDirectory() as tmp:
            svg_path = Path(tmp) / "safe.svg"
            svg_path.write_text(svg, encoding="utf-8")

            result = SVGQualityChecker().check_file(str(svg_path), expected_format="ppt169")

        self.assertTrue(result["passed"])
        self.assertFalse(result["errors"])

    def test_svg_quality_checker_still_rejects_ids_outside_defs(self):
        svg = '''<svg viewBox="0 0 1280 720" width="1280" height="720" xmlns="http://www.w3.org/2000/svg">
<rect id="hero" width="1280" height="720" fill="#fff" />
</svg>'''

        with tempfile.TemporaryDirectory() as tmp:
            svg_path = Path(tmp) / "bad_id.svg"
            svg_path.write_text(svg, encoding="utf-8")

            result = SVGQualityChecker().check_file(str(svg_path), expected_format="ppt169")

        self.assertFalse(result["passed"])
        self.assertIn("Detected forbidden id attribute", result["errors"][0])


if __name__ == "__main__":
    unittest.main()
