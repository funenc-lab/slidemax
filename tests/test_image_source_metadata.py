import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PROJECT_ROOT / "skills" / "slidemax_workflow"
UNIFIED_CLI = SKILL_ROOT / "scripts" / "slidemax.py"
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from slidemax.image_source_metadata import (
    SOURCE_METADATA_SUFFIX,
    build_generated_image_metadata,
    build_sidecar_path,
    read_source_metadata,
    write_source_metadata,
)


class ImageSourceMetadataTestCase(unittest.TestCase):
    def test_write_and_read_source_metadata_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "cover.png"
            image_path.write_bytes(b"png")
            metadata = build_generated_image_metadata(
                image_path,
                provider="gemini",
                model="gemini-3.1-flash-image-preview",
                prompt="city skyline",
                negative_prompt="watermark",
                local_path="images/cover.png",
            )

            sidecar = write_source_metadata(image_path, metadata)
            loaded = read_source_metadata(image_path)

            self.assertEqual(sidecar, build_sidecar_path(image_path))
            self.assertTrue(sidecar.name.endswith(SOURCE_METADATA_SUFFIX))
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.provider, "gemini")
            self.assertEqual(loaded.local_path, "images/cover.png")
            self.assertEqual(loaded.negative_prompt, "watermark")

    def test_register_command_writes_sidecar_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "hero.jpg"
            image_path.write_bytes(b"jpg")
            result = subprocess.run(
                [
                    sys.executable,
                    str(UNIFIED_CLI),
                    "register_image_source",
                    str(image_path),
                    "--source-type",
                    "stock",
                    "--provider",
                    "unsplash",
                    "--asset-id",
                    "abc123",
                    "--origin-url",
                    "https://unsplash.com/photos/abc123",
                    "--license-name",
                    "Unsplash License",
                    "--license-url",
                    "https://unsplash.com/license",
                    "--creator-name",
                    "Jane Doe",
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            payload = json.loads(result.stdout)
            sidecar = build_sidecar_path(image_path)
            self.assertEqual(payload["sidecar_path"], str(sidecar))
            self.assertTrue(sidecar.exists())
            self.assertEqual(payload["metadata"]["provider"], "unsplash")
            self.assertEqual(payload["metadata"]["source_type"], "stock")


if __name__ == "__main__":
    unittest.main()
