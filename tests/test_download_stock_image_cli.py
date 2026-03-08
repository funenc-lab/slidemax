import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PROJECT_ROOT / "skills" / "slidemax_workflow"
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from slidemax.stock_sources import execute_download_command, run_download_cli

IMAGE_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc``\x00\x00\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"


class _FakeResponse:
    def __init__(self, *, content=b"", status_code=200):
        self.content = content
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class DownloadStockImageCliTestCase(unittest.TestCase):
    def test_download_command_saves_image_and_updates_manifest(self):
        outputs = []
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp) / "demo_project"
            project_dir.mkdir()
            download_url = "https://cdn.example/assets/demo.png"

            def executor(args):
                return execute_download_command(args, output_fn=outputs.append)

            with mock.patch("requests.get", return_value=_FakeResponse(content=IMAGE_BYTES)) as mock_get:
                exit_code = run_download_cli(
                    [
                        str(project_dir),
                        "--provider",
                        "pexels",
                        "--source-url",
                        "https://www.pexels.com/photo/demo/",
                        "--download-url",
                        download_url,
                        "--filename",
                        "cover.png",
                        "--creator-name",
                        "Demo Creator",
                        "--keywords",
                        "hero, blue",
                    ],
                    executor=executor,
                )

            self.assertEqual(exit_code, 0)
            mock_get.assert_called_once_with(download_url, timeout=60)
            downloaded = project_dir / "images" / "stock" / "cover.png"
            self.assertTrue(downloaded.exists())
            self.assertEqual(downloaded.read_bytes(), IMAGE_BYTES)

            manifest_file = project_dir / "images" / "stock" / "manifest.json"
            manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
            self.assertEqual(len(manifest["images"]), 1)
            record = manifest["images"][0]
            self.assertEqual(record["filename"], "cover.png")
            self.assertEqual(record["local_path"], "images/stock/cover.png")
            self.assertEqual(record["source_provider"], "pexels")
            self.assertEqual(record["download_url"], download_url)
            self.assertEqual(record["creator_name"], "Demo Creator")
            self.assertEqual(record["keywords"], ["hero", "blue"])
            sidecar = project_dir / "images" / "stock" / "cover.png.source.json"
            self.assertTrue(sidecar.exists())
            metadata = json.loads(sidecar.read_text(encoding="utf-8"))
            self.assertEqual(metadata["provider"], "pexels")
            self.assertEqual(outputs, [
                f"Downloaded stock image: {downloaded}",
                f"Manifest updated: {manifest_file}",
            ])


if __name__ == "__main__":
    unittest.main()
