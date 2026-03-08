import json
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
COMMAND = PROJECT_ROOT / "skills" / "ppt_master_workflow" / "commands" / "download_stock_image.py"
IMAGE_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc``\x00\x00\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"


class _ImageHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/assets/demo.png":
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.send_header("Content-Length", str(len(IMAGE_BYTES)))
        self.end_headers()
        self.wfile.write(IMAGE_BYTES)

    def log_message(self, format, *args):
        return


class DownloadStockImageCliTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), _ImageHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_download_command_saves_image_and_updates_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp) / "demo_project"
            project_dir.mkdir()
            download_url = f"{self.base_url}/assets/demo.png"

            result = subprocess.run(
                [
                    sys.executable,
                    str(COMMAND),
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
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("Downloaded stock image", result.stdout)
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


if __name__ == "__main__":
    unittest.main()
