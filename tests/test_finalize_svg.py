import sys
import tempfile
import unittest
from base64 import b64decode
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PROJECT_ROOT / "skills" / "slidemax_workflow"
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from slidemax.finalize import FinalizeOptions, finalize_project
from slidemax.svg_quality import SVGQualityChecker


class FinalizeSvgTestCase(unittest.TestCase):
    def test_finalize_project_embeds_project_root_images_directory_assets(self):
        png_bytes = b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aF9sAAAAASUVORK5CYII="
        )
        svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720">
  <image href="images/cover.png" x="0" y="0" width="1280" height="720" />
</svg>
"""

        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo_ppt169_20260313"
            (project / "svg_output").mkdir(parents=True)
            (project / "images").mkdir()
            (project / "images" / "cover.png").write_bytes(png_bytes)
            (project / "svg_output" / "slide_01_cover.svg").write_text(svg, encoding="utf-8")

            success = finalize_project(project, FinalizeOptions())

            self.assertTrue(success)

            final_svg = project / "svg_final" / "slide_01_cover.svg"
            content = final_svg.read_text(encoding="utf-8")

        self.assertIn("data:image/png;base64,", content)

    def test_finalize_project_sanitizes_common_svg_compatibility_issues(self):
        svg = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
     xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
     viewBox="0 0 1280 720"
     width="1280"
     height="720"
     id="root"
     sodipodi:docname="bad.svg"
     inkscape:version="1.4.2">
  <sodipodi:namedview
      id="namedview1"
      inkscape:current-layer="root"
      pagecolor="#ffffff" />
  <defs id="defs1">
    <linearGradient id="heroGradient" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#111111" />
      <stop offset="100%" stop-color="#333333" />
    </linearGradient>
  </defs>
  <rect id="background" width="1280" height="720" fill="url(#heroGradient)" />
  <g opacity="0.7">
    <text
        x="80"
        y="120"
        font-family="system-ui, -apple-system, sans-serif"
        font-size="28"
        fill="#FFFFFF">Trusted example</text>
  </g>
</svg>
"""

        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo_ppt169_20260313"
            (project / "svg_output").mkdir(parents=True)
            (project / "svg_output" / "slide_01_cover.svg").write_text(svg, encoding="utf-8")

            success = finalize_project(project, FinalizeOptions())

            self.assertTrue(success)

            final_svg = project / "svg_final" / "slide_01_cover.svg"
            content = final_svg.read_text(encoding="utf-8")
            self.assertNotIn("sodipodi", content.lower())
            self.assertNotIn("inkscape", content.lower())
            self.assertNotIn('id="root"', content)
            self.assertNotIn('id="background"', content)
            self.assertIn('id="heroGradient"', content)
            self.assertNotIn("<g opacity=", content.lower())
            self.assertIn('opacity="0.7"', content)

            result = SVGQualityChecker().check_file(str(final_svg), expected_format="ppt169")

        self.assertTrue(result["passed"], result)
        self.assertFalse(result["warnings"], result)

    def test_finalize_project_combines_nested_group_opacity(self):
        svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720">
  <g opacity="0.5">
    <g opacity="0.4">
      <text x="80" y="120" opacity="0.8">Nested opacity</text>
    </g>
  </g>
</svg>
"""

        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo_ppt169_20260313"
            (project / "svg_output").mkdir(parents=True)
            (project / "svg_output" / "slide_01_cover.svg").write_text(svg, encoding="utf-8")

            success = finalize_project(project, FinalizeOptions())

            self.assertTrue(success)

            final_svg = project / "svg_final" / "slide_01_cover.svg"
            content = final_svg.read_text(encoding="utf-8")

        self.assertNotIn("<g opacity=", content.lower())
        self.assertIn('opacity="0.16"', content)


if __name__ == "__main__":
    unittest.main()
