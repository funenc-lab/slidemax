import os
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PROJECT_ROOT / "skills" / "ppt_master_workflow"
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from pptmaster.video_generation import VideoGenerationResult, execute_parsed_command
from pptmaster.video_generation_cli import run_cli

VIDEO_BYTES = b"\x00\x00\x00 ftypisom\x00\x00\x02\x00isomiso2mp41"


class DoubaoI2VTaskCliTestCase(unittest.TestCase):
    def test_download_subcommand_does_not_require_api_key(self):
        outputs = []
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "direct_download.mp4"

            def fake_download(url, output_path, timeout_seconds):
                self.assertEqual(url, "https://cdn.example/cli.mp4")
                self.assertEqual(timeout_seconds, 10)
                output_path.write_bytes(VIDEO_BYTES)
                return output_path

            def executor(args):
                return execute_parsed_command(
                    args,
                    output_fn=outputs.append,
                    download_handler=fake_download,
                )

            with mock.patch.dict(os.environ, {"ARK_API_KEY": "", "DOUBAO_API_KEY": ""}, clear=False):
                exit_code = run_cli(
                    [
                        "download",
                        "--video-url",
                        "https://cdn.example/cli.mp4",
                        "--output",
                        str(output),
                        "--timeout",
                        "10",
                    ],
                    executor=executor,
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(output.read_bytes(), VIDEO_BYTES)
            self.assertEqual(outputs, [f"Video saved to: {output}"])

    def test_run_subcommand_creates_waits_and_downloads(self):
        outputs = []
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "cli_result.mp4"

            def fake_run_task(request, **kwargs):
                self.assertEqual(request.prompt, "Fast drone flight")
                self.assertEqual(request.image_url, "https://example.com/demo.png")
                self.assertEqual(request.output_path, output)
                self.assertEqual(kwargs["api_key"], "secret")
                self.assertEqual(kwargs["base_url"], "https://ark.example/api/v3")
                self.assertEqual(kwargs["poll_interval_seconds"], 0.0)
                self.assertEqual(kwargs["max_poll_attempts"], 2)
                output.write_bytes(VIDEO_BYTES)
                return VideoGenerationResult(
                    task_id="task-cli-001",
                    status="succeeded",
                    model="doubao-seedance-1-5-pro-251215",
                    video_url="https://cdn.example/cli.mp4",
                    output_path=output,
                    raw_response={"id": "task-cli-001"},
                )

            def executor(args):
                return execute_parsed_command(
                    args,
                    output_fn=outputs.append,
                    run_task=fake_run_task,
                )

            exit_code = run_cli(
                [
                    "run",
                    "Fast drone flight",
                    "--image-url",
                    "https://example.com/demo.png",
                    "--base-url",
                    "https://ark.example/api/v3",
                    "--model",
                    "doubao-seedance-1-5-pro-251215",
                    "--poll-interval",
                    "0",
                    "--max-poll-attempts",
                    "2",
                    "--output",
                    str(output),
                    "--api-key",
                    "secret",
                ],
                executor=executor,
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(output.read_bytes(), VIDEO_BYTES)
            self.assertEqual(outputs, [
                "Task created: task-cli-001",
                "Task status: succeeded",
                "Video URL: https://cdn.example/cli.mp4",
                f"Video saved to: {output}",
            ])


if __name__ == "__main__":
    unittest.main()
