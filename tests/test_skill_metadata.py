import json
import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SKILL_CASES = [
    {
        "meta_path": PROJECT_ROOT / "skills" / "slidemax_workflow" / "_meta.json",
        "expected_kind": "workflow-skill",
        "expected_canonical": True,
        "required_guides": [
            "AGENTS.md",
            "workflows/generate-ppt.md",
            "commands/README.md",
            "roles/README.md",
        ],
        "required_commands": [
            "commands/project_manager.py",
            "commands/pdf_to_md.py",
            "commands/web_to_md.py",
            "commands/image_generate.py",
            "commands/finalize_svg.py",
            "commands/svg_to_pptx.py",
        ],
    },
    {
        "meta_path": PROJECT_ROOT / ".agent" / "skills" / "ocr_image_to_markdown" / "_meta.json",
        "expected_kind": "fallback-skill",
        "expected_canonical": False,
        "required_guides": [],
        "required_commands": [],
    },
]

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


def _extract_frontmatter_name(skill_path: Path) -> str:
    lines = skill_path.read_text(encoding="utf-8").splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        raise AssertionError(f"Missing frontmatter in {skill_path}")
    for line in lines[1:10]:
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip()
    raise AssertionError(f"Missing frontmatter name in {skill_path}")


def _resolve_path(base_dir: Path, relative_path: str) -> Path:
    if relative_path.startswith("skills/") or relative_path.startswith(".agent/"):
        return PROJECT_ROOT / relative_path
    return base_dir / relative_path


class SkillMetadataTestCase(unittest.TestCase):
    def test_all_skill_metadata_files_are_valid(self):
        for case in SKILL_CASES:
            with self.subTest(meta_path=str(case["meta_path"])):
                data = json.loads(case["meta_path"].read_text(encoding="utf-8"))
                skill_dir = case["meta_path"].parent
                skill_md = skill_dir / "SKILL.md"

                self.assertEqual(data["schema_version"], 2)
                self.assertEqual(data["language"], "en")
                self.assertEqual(data["kind"], case["expected_kind"])
                self.assertEqual(data["canonical"], case["expected_canonical"])
                self.assertTrue(VERSION_PATTERN.match(data["version"]))
                self.assertTrue(DATE_PATTERN.match(data["created_at"]))
                self.assertTrue(DATE_PATTERN.match(data["updated_at"]))
                self.assertEqual(data["entrypoints"]["skill"], "SKILL.md")
                self.assertTrue(skill_md.exists())
                self.assertEqual(data["name"], _extract_frontmatter_name(skill_md))

                self.assertIsInstance(data["scope_paths"], list)
                self.assertGreater(len(data["scope_paths"]), 0)
                for scope_path in data["scope_paths"]:
                    self.assertTrue(_resolve_path(skill_dir, scope_path).exists())

                self.assertIsInstance(data["activation"]["triggers"], list)
                self.assertGreater(len(data["activation"]["triggers"]), 0)
                self.assertIsInstance(data["activation"]["do_not_use_when"], list)
                self.assertGreater(len(data["activation"]["do_not_use_when"]), 0)

                self.assertIsInstance(data["capabilities"], list)
                self.assertGreater(len(data["capabilities"]), 0)
                self.assertIsInstance(data["constraints"], list)
                self.assertGreater(len(data["constraints"]), 0)
                self.assertIsInstance(data["tags"], list)
                self.assertGreater(len(data["tags"]), 0)

                for guide in case["required_guides"]:
                    self.assertIn(guide, data["entrypoints"].get("guides", []))
                    self.assertTrue((skill_dir / guide).exists())

                for command_path in case["required_commands"]:
                    self.assertIn(command_path, data["entrypoints"].get("commands", []))
                    self.assertTrue((skill_dir / command_path).exists())

                for file_path in data["dependencies"]["files"]:
                    self.assertTrue(_resolve_path(skill_dir, file_path).exists())

                for reference_path in data["references"]:
                    self.assertTrue(_resolve_path(skill_dir, reference_path).exists())


if __name__ == "__main__":
    unittest.main()
