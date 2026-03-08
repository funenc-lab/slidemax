import argparse
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PROJECT_ROOT / "skills" / "slidemax_workflow"
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from slidemax.video_generation import (
    VideoGenerationRequest,
    VideoGenerationResult,
    VideoTaskStatus,
    execute_parsed_command,
    run_cli,
)


class VideoGenerationCliDispatchTestCase(unittest.TestCase):
    def test_download_command_uses_timeout_resolver_and_downloader(self):
        outputs = []
        calls = {}
        args = argparse.Namespace(command="download", video_url="https://cdn.example/demo.mp4", output="demo.mp4", timeout=12)

        def fake_resolve_timeout(value):
            calls["timeout"] = value
            return 34

        def fake_download(url, output_path, timeout_seconds):
            calls["download"] = (url, output_path, timeout_seconds)
            return output_path

        exit_code = execute_parsed_command(
            args,
            output_fn=outputs.append,
            timeout_resolver=fake_resolve_timeout,
            download_handler=fake_download,
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(calls["timeout"], 12)
        self.assertEqual(calls["download"], ("https://cdn.example/demo.mp4", Path("demo.mp4"), 34))
        self.assertEqual(outputs, ["Video saved to: demo.mp4"])

    def test_status_command_prints_all_available_fields(self):
        outputs = []
        args = argparse.Namespace(command="status", task_id="task-001", api_key="secret", base_url="https://ark.example/api/v3", timeout=22)

        status = VideoTaskStatus(
            task_id="task-001",
            status="succeeded",
            model="demo-model",
            video_url="https://cdn.example/demo.mp4",
            raw_response={"id": "task-001"},
        )

        exit_code = execute_parsed_command(
            args,
            output_fn=outputs.append,
            config_resolver=lambda **kwargs: kwargs,
            status_getter=lambda task_id, config: status,
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(outputs, [
            "Task ID: task-001",
            "Task status: succeeded",
            "Model: demo-model",
            "Video URL: https://cdn.example/demo.mp4",
        ])

    def test_run_command_uses_request_builder_and_runner(self):
        outputs = []
        args = argparse.Namespace(
            command="run",
            prompt="Fast drone flight",
            image_url="https://example.com/demo.png",
            model=None,
            duration=5,
            camera_fixed=False,
            watermark=True,
            output=None,
            api_key="secret",
            base_url="https://ark.example/api/v3",
            timeout=12,
            poll_interval=0.0,
            max_poll_attempts=2,
        )

        request = VideoGenerationRequest(prompt="p", image_url="i")
        result = VideoGenerationResult(
            task_id="task-run-001",
            status="succeeded",
            model="demo-model",
            video_url="https://cdn.example/demo.mp4",
            output_path=Path("result.mp4"),
            raw_response={"id": "task-run-001"},
        )
        captured = {}

        def fake_run(request_obj, **kwargs):
            captured["request"] = request_obj
            captured["kwargs"] = kwargs
            return result

        exit_code = execute_parsed_command(
            args,
            output_fn=outputs.append,
            request_builder=lambda parsed_args: request,
            run_task=fake_run,
        )

        self.assertEqual(exit_code, 0)
        self.assertIs(captured["request"], request)
        self.assertEqual(captured["kwargs"]["api_key"], "secret")
        self.assertEqual(captured["kwargs"]["poll_interval_seconds"], 0.0)
        self.assertEqual(outputs, [
            "Task created: task-run-001",
            "Task status: succeeded",
            "Video URL: https://cdn.example/demo.mp4",
            "Video saved to: result.mp4",
        ])

    def test_run_cli_accepts_executor_override(self):
        captured = {}

        def fake_executor(args):
            captured["command"] = args.command
            captured["prompt"] = args.prompt
            captured["image_url"] = args.image_url
            return 7

        exit_code = run_cli(
            [
                "run",
                "Fast drone flight",
                "--image-url",
                "https://example.com/demo.png",
            ],
            executor=fake_executor,
        )

        self.assertEqual(exit_code, 7)
        self.assertEqual(captured, {
            "command": "run",
            "prompt": "Fast drone flight",
            "image_url": "https://example.com/demo.png",
        })


    def test_create_command_with_wait_downloads_video_when_output_is_set(self):
        outputs = []
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "demo.mp4"
            args = argparse.Namespace(
                command="create",
                prompt="Fast drone flight",
                image_url="https://example.com/demo.png",
                model=None,
                duration=5,
                camera_fixed=False,
                watermark=True,
                output=str(output_path),
                api_key="secret",
                base_url="https://ark.example/api/v3",
                timeout=12,
                poll_interval=0.0,
                max_poll_attempts=2,
                wait=True,
            )

            request = VideoGenerationRequest(prompt="p", image_url="i", output_path=output_path)
            status = VideoTaskStatus(
                task_id="task-create-001",
                status="succeeded",
                model="demo-model",
                video_url="https://cdn.example/demo.mp4",
                raw_response={"id": "task-create-001"},
            )
            captured = {}

            def fake_download(url, path, timeout_seconds):
                captured["download"] = (url, path, timeout_seconds)
                return path

            exit_code = execute_parsed_command(
                args,
                output_fn=outputs.append,
                request_builder=lambda parsed_args: request,
                config_resolver=lambda **kwargs: {"config": kwargs},
                task_creator=lambda request_obj, config: "task-create-001",
                status_waiter=lambda task_id, config, **kwargs: status,
                download_handler=fake_download,
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(captured["download"], ("https://cdn.example/demo.mp4", output_path, 12))
        self.assertEqual(outputs, [
            "Task created: task-create-001",
            "Task status: succeeded",
            "Video URL: https://cdn.example/demo.mp4",
            f"Video saved to: {output_path}",
        ])


if __name__ == "__main__":
    unittest.main()
