import json
import os
import sys
import tempfile
import unittest
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

VIDEO_BYTES = b"\x00\x00\x00 ftypisom\x00\x00\x02\x00isomiso2mp41"


class _FakeResponse:
    def __init__(self, *, json_data=None, content=b"", status_code=200):
        self._json_data = json_data
        self.content = content
        self.status_code = status_code

    def json(self):
        if self._json_data is None:
            raise ValueError("No JSON payload configured.")
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class VideoGenerationTestCase(unittest.TestCase):
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
        captured = {}

        def fake_post(url, json=None, headers=None, timeout=None):
            captured["post"] = {
                "url": url,
                "json": json,
                "headers": headers,
                "timeout": timeout,
            }
            return _FakeResponse(json_data={"id": "task-demo-001"})

        def fake_get(url, headers=None, timeout=None):
            if url.endswith("/contents/generations/tasks/task-demo-001"):
                captured.setdefault("status_calls", 0)
                captured["status_calls"] += 1
                return _FakeResponse(
                    json_data={
                        "id": "task-demo-001",
                        "status": "succeeded",
                        "content": {"video_url": "https://cdn.example/files/demo.mp4"},
                    }
                )
            if url == "https://cdn.example/files/demo.mp4":
                captured["download"] = {"url": url, "timeout": timeout}
                return _FakeResponse(content=VIDEO_BYTES)
            raise AssertionError(f"Unexpected GET URL: {url}")

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
            with mock.patch("requests.post", side_effect=fake_post), mock.patch("requests.get", side_effect=fake_get):
                result = run_generation_task(
                    request,
                    api_key="secret",
                    base_url="https://ark.example/api/v3",
                    poll_interval_seconds=0,
                    max_poll_attempts=2,
                )

            self.assertEqual(result.task_id, "task-demo-001")
            self.assertEqual(result.status, "succeeded")
            self.assertTrue(result.output_path.exists())
            self.assertEqual(result.output_path.read_bytes(), VIDEO_BYTES)

        payload = captured["post"]["json"]
        self.assertEqual(captured["post"]["url"], "https://ark.example/api/v3/contents/generations/tasks")
        self.assertEqual(captured["post"]["timeout"], 180)
        self.assertEqual(payload["model"], "doubao-seedance-1-5-pro-251215")
        self.assertEqual(payload["content"][0]["type"], "text")
        self.assertIn("--duration 5", payload["content"][0]["text"])
        self.assertIn("--camerafixed false", payload["content"][0]["text"])
        self.assertIn("--watermark true", payload["content"][0]["text"])
        self.assertEqual(payload["content"][1]["image_url"]["url"], "https://example.com/demo.png")
        self.assertEqual(captured["status_calls"], 1)
        self.assertEqual(captured["download"], {"url": "https://cdn.example/files/demo.mp4", "timeout": 180})

    def test_download_video_fetches_binary_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "downloaded.mp4"
            with mock.patch("requests.get", return_value=_FakeResponse(content=VIDEO_BYTES)) as mock_get:
                download_video(
                    "https://cdn.example/files/demo.mp4",
                    output,
                    timeout_seconds=10,
                )

            mock_get.assert_called_once_with("https://cdn.example/files/demo.mp4", timeout=10)
            self.assertEqual(output.read_bytes(), VIDEO_BYTES)


if __name__ == "__main__":
    unittest.main()
