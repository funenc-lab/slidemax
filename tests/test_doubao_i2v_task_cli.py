import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
COMMAND = PROJECT_ROOT / "skills" / "ppt_master_workflow" / "commands" / "doubao_i2v_task.py"
VIDEO_BYTES = b"\x00\x00\x00 ftypisom\x00\x00\x02\x00isomiso2mp41"


class _ArkCliHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/api/v3/contents/generations/tasks":
            self.send_response(404)
            self.end_headers()
            return
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length)
        payload = json.loads(raw.decode("utf-8"))
        if payload["model"] != "doubao-seedance-1-5-pro-251215":
            self.send_response(400)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"id": "task-cli-001"}).encode("utf-8"))

    def do_GET(self):
        if self.path == "/api/v3/contents/generations/tasks/task-cli-001":
            body = {
                "id": "task-cli-001",
                "status": "succeeded",
                "content": {"video_url": f"http://127.0.0.1:{self.server.server_port}/files/cli.mp4"},
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(body).encode("utf-8"))
            return

        if self.path == "/files/cli.mp4":
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


class DoubaoI2VTaskCliTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), _ArkCliHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}/api/v3"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_download_subcommand_does_not_require_api_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "direct_download.mp4"
            env = dict(os.environ)
            env.pop("ARK_API_KEY", None)
            result = subprocess.run(
                [
                    sys.executable,
                    str(COMMAND),
                    "download",
                    "--video-url",
                    f"http://127.0.0.1:{self.server.server_port}/files/cli.mp4",
                    "--output",
                    str(output),
                    "--timeout",
                    "10",
                ],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertIn("Video saved to:", result.stdout)
            self.assertEqual(output.read_bytes(), VIDEO_BYTES)

    def test_run_subcommand_creates_waits_and_downloads(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "cli_result.mp4"
            env = dict(os.environ)
            env["ARK_API_KEY"] = "secret"
            result = subprocess.run(
                [
                    sys.executable,
                    str(COMMAND),
                    "run",
                    "Fast drone flight",
                    "--image-url",
                    "https://example.com/demo.png",
                    "--base-url",
                    self.base_url,
                    "--model",
                    "doubao-seedance-1-5-pro-251215",
                    "--poll-interval",
                    "0",
                    "--max-poll-attempts",
                    "2",
                    "--output",
                    str(output),
                ],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertIn("Task created: task-cli-001", result.stdout)
            self.assertIn("Task status: succeeded", result.stdout)
            self.assertIn("Video saved to:", result.stdout)
            self.assertEqual(output.read_bytes(), VIDEO_BYTES)


if __name__ == "__main__":
    unittest.main()
