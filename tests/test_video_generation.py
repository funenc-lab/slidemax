import base64
import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PROJECT_ROOT / "skills" / "ppt_master_workflow"
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from pptmaster.video_generation import (
    VideoGenerationRequest,
    download_video,
    resolve_ark_config,
    resolve_video_model,
    run_generation_task,
)

PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGNgYAAAAAIAAeIhvDMAAAAASUVORK5CYII="
)
VIDEO_BYTES = b"\x00\x00\x00 ftypisom\x00\x00\x02\x00isomiso2mp41"


class _ArkHandler(BaseHTTPRequestHandler):
    create_payload = None
    status_calls = 0

    def do_POST(self):
        if self.path != "/api/v3/contents/generations/tasks":
            self.send_response(404)
            self.end_headers()
            return
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length)
        self.__class__.create_payload = json.loads(raw.decode("utf-8"))
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"id": "task-demo-001"}).encode("utf-8"))

    def do_GET(self):
        if self.path == "/api/v3/contents/generations/tasks/task-demo-001":
            self.__class__.status_calls += 1
            body = {
                "id": "task-demo-001",
                "status": "succeeded",
                "content": {"video_url": f"http://127.0.0.1:{self.server.server_port}/files/demo.mp4"},
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(body).encode("utf-8"))
            return

        if self.path == "/files/demo.mp4":
            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Length", str(len(VIDEO_BYTES)))
            self.end_headers()
            self.wfile.write(VIDEO_BYTES)
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        return


class VideoGenerationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), _ArkHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}/api/v3"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_resolve_ark_config_uses_env(self):
        with mock.patch.dict(
            os.environ,
            {
                "ARK_API_KEY": "secret",
                "ARK_BASE_URL": "https://ark.example/api/v3",
                "ARK_TIMEOUT": "45",
            },
            clear=False,
        ):
            config = resolve_ark_config()

        self.assertEqual(config.api_key, "secret")
        self.assertEqual(config.base_url, "https://ark.example/api/v3")
        self.assertEqual(config.timeout_seconds, 45)

    def test_resolve_video_model_uses_env_override(self):
        with mock.patch.dict(os.environ, {"ARK_VIDEO_MODEL": "Doubao-Seedance-2.0"}, clear=False):
            self.assertEqual(resolve_video_model(), "Doubao-Seedance-2.0")

    def test_run_generation_task_posts_payload_and_downloads_video(self):
        with tempfile.TemporaryDirectory() as tmp:
            request = VideoGenerationRequest(
                prompt="Fast drone flight",
                image_url="https://example.com/demo.png",
                model="doubao-seedance-1-5-pro-251215",
                duration=5,
                camera_fixed=False,
                watermark=True,
                output_path=Path(tmp) / "result.mp4",
            )
            with mock.patch.dict(os.environ, {"ARK_API_KEY": "secret"}, clear=False):
                result = run_generation_task(
                    request,
                    api_key="secret",
                    base_url=self.base_url,
                    poll_interval_seconds=0,
                    max_poll_attempts=2,
                )

            self.assertEqual(result.task_id, "task-demo-001")
            self.assertEqual(result.status, "succeeded")
            self.assertTrue(result.output_path.exists())
            self.assertEqual(result.output_path.read_bytes(), VIDEO_BYTES)

            payload = _ArkHandler.create_payload
            self.assertEqual(payload["model"], "doubao-seedance-1-5-pro-251215")
            self.assertEqual(payload["content"][0]["type"], "text")
            self.assertIn("--duration 5", payload["content"][0]["text"])
            self.assertIn("--camerafixed false", payload["content"][0]["text"])
            self.assertIn("--watermark true", payload["content"][0]["text"])
            self.assertEqual(payload["content"][1]["image_url"]["url"], "https://example.com/demo.png")

    def test_download_video_fetches_binary_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "downloaded.mp4"
            download_video(
                f"http://127.0.0.1:{self.server.server_port}/files/demo.mp4",
                output,
                timeout_seconds=10,
            )
            self.assertEqual(output.read_bytes(), VIDEO_BYTES)


if __name__ == "__main__":
    unittest.main()
