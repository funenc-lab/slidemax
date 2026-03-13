import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PROJECT_ROOT / "skills" / "slidemax_workflow"
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from slidemax.examples_index import CANONICAL_CLI, build_examples_index, build_render_context


class ExamplesIndexTestCase(unittest.TestCase):
    def _write_svg(self, path: Path, *, opacity_group: bool = False) -> None:
        body = '<rect width="1280" height="720" fill="#FFFFFF" />'
        if opacity_group:
            body += '<g opacity="0.4"><rect width="20" height="20" fill="#000000" /></g>'
        path.write_text(
            (
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" '
                'width="1280" height="720">'
                f"{body}"
                "</svg>"
            ),
            encoding="utf-8",
        )

    def _create_curated_project(self, root: Path) -> None:
        project = root / "curated_demo_ppt169_20260313"
        (project / "svg_output").mkdir(parents=True)
        (project / "svg_final").mkdir()
        (project / "images").mkdir()
        (project / "notes").mkdir()
        (project / "templates").mkdir()
        (project / "README.md").write_text("# Curated demo\n", encoding="utf-8")
        (project / "design_specification.md").write_text("# Spec\n", encoding="utf-8")
        (project / "images" / "image_prompts.md").write_text("# Prompts\n", encoding="utf-8")
        (project / "notes" / "total.md").write_text("## slide_01_cover\nSpeaker notes.\n", encoding="utf-8")
        (project / "notes" / "slide_01_cover.md").write_text("Speaker notes.\n", encoding="utf-8")
        (project / "templates" / ".gitkeep").write_text("", encoding="utf-8")
        (project / "curated_demo_ppt169_20260313.pptx").write_bytes(b"pptx")
        self._write_svg(project / "svg_output" / "slide_01_cover.svg")
        self._write_svg(project / "svg_final" / "slide_01_cover.svg")

    def _create_curated_project_without_date(self, root: Path) -> None:
        project = root / "legacy_curated_demo_ppt169"
        (project / "svg_output").mkdir(parents=True)
        (project / "svg_final").mkdir()
        (project / "images").mkdir()
        (project / "notes").mkdir()
        (project / "templates").mkdir()
        (project / "README.md").write_text("# Legacy curated demo\n", encoding="utf-8")
        (project / "design_specification.md").write_text("# Spec\n", encoding="utf-8")
        (project / "images" / "image_prompts.md").write_text("# Prompts\n", encoding="utf-8")
        (project / "notes" / "total.md").write_text("## slide_01_cover\nSpeaker notes.\n", encoding="utf-8")
        (project / "notes" / "slide_01_cover.md").write_text("Speaker notes.\n", encoding="utf-8")
        (project / "templates" / ".gitkeep").write_text("", encoding="utf-8")
        (project / "legacy_curated_demo_ppt169.pptx").write_bytes(b"pptx")
        self._write_svg(project / "svg_output" / "slide_01_cover.svg")
        self._write_svg(project / "svg_final" / "slide_01_cover.svg")

    def _create_preview_only_project(self, root: Path) -> None:
        project = root / "legacy_demo_ppt169_20260312"
        (project / "svg_output").mkdir(parents=True)
        (project / "svg_final").mkdir()
        (project / "images").mkdir()
        (project / "notes").mkdir()
        (project / "templates").mkdir()
        (project / "design_specification.md").write_text("# Spec\n", encoding="utf-8")
        self._write_svg(project / "svg_output" / "slide_01_cover.svg")
        self._write_svg(project / "svg_final" / "slide_01_cover.svg", opacity_group=True)

    def test_build_render_context_uses_unified_cli_inside_repo(self):
        context = build_render_context(SKILL_ROOT / "examples")

        self.assertIn("scripts/slidemax.py", context.command_reference)
        self.assertIn("scripts/slidemax.py", context.project_manager_command)
        self.assertIn("project_manager init", context.project_manager_command)
        self.assertIn("generate_examples_index", context.update_command)
        self.assertNotIn("commands/project_manager.py", context.project_manager_command)
        self.assertNotIn("commands/generate_examples_index.py", context.update_command)

    def test_build_render_context_uses_unified_cli_for_external_examples_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            context = build_render_context(Path(tmp))

        self.assertEqual(context.command_reference, str(CANONICAL_CLI))
        self.assertIn("project_manager validate", context.validate_command)
        self.assertIn("generate_examples_index", context.update_command)

    def test_build_examples_index_separates_curated_and_preview_only_projects(self):
        with tempfile.TemporaryDirectory() as tmp:
            examples_root = Path(tmp)
            self._create_curated_project(examples_root)
            self._create_preview_only_project(examples_root)

            result = build_examples_index(examples_root, now=datetime(2026, 3, 13, 12, 0, 0))

        self.assertIn("Curated Reference Projects", result.content)
        self.assertIn("Preview-only Projects", result.content)
        self.assertIn("curated_demo", result.content)
        self.assertIn("legacy_demo", result.content)
        self.assertIn("passes delivery validation", result.content)
        self.assertIn("must not be used as a canonical workflow reference", result.content)

    def test_build_examples_index_sorts_unknown_dates_after_known_dates(self):
        with tempfile.TemporaryDirectory() as tmp:
            examples_root = Path(tmp)
            self._create_curated_project(examples_root)
            self._create_curated_project_without_date(examples_root)

            result = build_examples_index(examples_root, now=datetime(2026, 3, 13, 12, 0, 0))

        recent_section = result.content.split("## Recently Updated\n", 1)[1].split(
            "\n## Curated Reference Projects\n",
            1,
        )[0]
        curated_section = result.content.split("## Curated Reference Projects\n", 1)[1].split(
            "\n## Preview-only Projects\n",
            1,
        )[0]

        self.assertLess(recent_section.index("curated_demo"), recent_section.index("legacy_curated_demo"))
        self.assertLess(curated_section.index("curated_demo"), curated_section.index("legacy_curated_demo"))


if __name__ == "__main__":
    unittest.main()
