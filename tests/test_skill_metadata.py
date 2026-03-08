import json
import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SKILL_CASES = [
    {
        "meta_path": PROJECT_ROOT / "skills" / "ppt_master_workflow" / "_meta.json",
        "expected_kind": "workflow-skill",
        "required_guides": [
            "AGENTS.md",
            "workflows/generate-ppt.md",
            "commands/README.md",
        ],
    },
    {
        "meta_path": PROJECT_ROOT / ".agent" / "skills" / "ocr_image_to_markdown" / "_meta.json",
        "expected_kind": "fallback-skill",
        "required_guides": [],
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


class SkillMetadataTestCase(unittest.TestCase):
    def test_all_skill_metadata_files_are_valid(self):
        for case in SKILL_CASES:
            with self.subTest(meta_path=str(case["meta_path"])):
                data = json.loads(case["meta_path"].read_text(encoding="utf-8"))
                skill_dir = case["meta_path"].parent
                skill_md = skill_dir / "SKILL.md"

                self.assertEqual(data["schema_version"], 1)
                self.assertEqual(data["language"], "en")
                self.assertEqual(data["kind"], case["expected_kind"])
                self.assertTrue(VERSION_PATTERN.match(data["version"]))
                self.assertTrue(DATE_PATTERN.match(data["created_at"]))
                self.assertTrue(DATE_PATTERN.match(data["updated_at"]))
                self.assertEqual(data["entrypoints"]["skill"], "SKILL.md")
                self.assertTrue(skill_md.exists())
                self.assertEqual(data["name"], _extract_frontmatter_name(skill_md))
                self.assertIsInstance(data["tags"], list)
                self.assertGreater(len(data["tags"]), 0)

                for guide in case["required_guides"]:
                    self.assertIn(guide, data["entrypoints"].get("guides", []))
                    self.assertTrue((skill_dir / guide).exists())


if __name__ == "__main__":
    unittest.main()
