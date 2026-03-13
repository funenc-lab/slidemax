import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
COMMAND = PROJECT_ROOT / "skills" / "slidemax_workflow" / "scripts" / "slidemax.py"


class RegisterStockImageCliTestCase(unittest.TestCase):
    def test_list_providers(self):
        result = subprocess.run(
            [sys.executable, str(COMMAND), "register_stock_image", "--list-providers"],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("unsplash", result.stdout)
        self.assertIn("pexels", result.stdout)
        self.assertIn("pixabay", result.stdout)

    def test_register_command_writes_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_dir = root / "demo_project"
            project_dir.mkdir()
            local_file = root / "downloaded.jpg"
            local_file.write_bytes(b"stock-image")

            result = subprocess.run(
                [
                    sys.executable,
                    str(COMMAND),
                    "register_stock_image",
                    str(project_dir),
                    "--provider",
                    "unsplash",
                    "--source-url",
                    "https://unsplash.com/photos/abc123",
                    "--local-file",
                    str(local_file),
                    "--filename",
                    "hero.jpg",
                    "--creator-name",
                    "Jane Doe",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("Registered stock image", result.stdout)

            manifest = json.loads((project_dir / "images" / "stock" / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(len(manifest["images"]), 1)
            self.assertEqual(manifest["images"][0]["filename"], "hero.jpg")
            self.assertEqual(manifest["images"][0]["creator_name"], "Jane Doe")
            sidecar = project_dir / "images" / "stock" / "hero.jpg.source.json"
            self.assertTrue(sidecar.exists())
            metadata = json.loads(sidecar.read_text(encoding="utf-8"))
            self.assertEqual(metadata["provider"], "unsplash")


if __name__ == "__main__":
    unittest.main()
