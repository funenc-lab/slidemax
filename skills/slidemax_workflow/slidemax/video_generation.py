"""Shared ARK video generation helpers for SlideMax."""

from __future__ import annotations

import argparse
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

DEFAULT_ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_ARK_TIMEOUT_SECONDS = 180
DEFAULT_POLL_INTERVAL_SECONDS = 5.0
DEFAULT_MAX_POLL_ATTEMPTS = 60
DEFAULT_VIDEO_MODEL = "doubao-seedance-1-5-pro-251215"


class VideoGenerationError(RuntimeError):
    """Raised when ARK video generation fails."""


@dataclass(frozen=True)
class ArkConfig:
    """Resolved ARK request configuration."""

    api_key: str
    base_url: str = DEFAULT_ARK_BASE_URL
    timeout_seconds: int = DEFAULT_ARK_TIMEOUT_SECONDS


@dataclass(frozen=True)
class VideoGenerationRequest:
    """Normalized image-to-video task request."""

    prompt: str
    image_url: str
    model: str = DEFAULT_VIDEO_MODEL
    duration: int = 5
    camera_fixed: bool = False
    watermark: bool = True
    output_path: Optional[Path] = None


@dataclass(frozen=True)
class VideoTaskStatus:
    """ARK task status payload summary."""

    task_id: str
    status: str
    model: Optional[str] = None
    video_url: Optional[str] = None
    raw_response: Optional[dict] = None


@dataclass(frozen=True)
class VideoGenerationResult:
    """Final result metadata for a completed video task."""

    task_id: str
    status: str
    model: Optional[str]
    video_url: Optional[str]
    output_path: Optional[Path]
    raw_response: dict


TERMINAL_STATUSES = {"succeeded", "failed", "canceled"}


def _first_env(*names: str) -> Optional[str]:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return None


def _bool_token(value: bool) -> str:
    return "true" if value else "false"


def resolve_video_model(model: Optional[str] = None) -> str:
    """Resolve the preferred ARK video model from explicit input or env vars."""

    return model or _first_env("ARK_VIDEO_MODEL", "DOUBAO_VIDEO_MODEL") or DEFAULT_VIDEO_MODEL


def resolve_timeout_seconds(timeout_seconds: Optional[int] = None) -> int:
    """Resolve request timeout seconds from explicit input or env vars."""

    raw_timeout = timeout_seconds or _first_env("ARK_TIMEOUT", "SLIDEMAX_IMAGE_TIMEOUT")
    return int(raw_timeout) if raw_timeout else DEFAULT_ARK_TIMEOUT_SECONDS


def resolve_ark_config(
    *,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    timeout_seconds: Optional[int] = None,
) -> ArkConfig:
    """Resolve ARK credentials and defaults from explicit values or env vars."""

    resolved_api_key = api_key or _first_env("ARK_API_KEY", "DOUBAO_API_KEY")
    if not resolved_api_key:
        raise ValueError("Missing API key. Set ARK_API_KEY or DOUBAO_API_KEY.")

    resolved_base_url = base_url or _first_env("ARK_BASE_URL") or DEFAULT_ARK_BASE_URL
    resolved_timeout = resolve_timeout_seconds(timeout_seconds)
    return ArkConfig(
        api_key=resolved_api_key,
        base_url=resolved_base_url.rstrip("/"),
        timeout_seconds=resolved_timeout,
    )


def build_task_prompt(request: VideoGenerationRequest) -> str:
    """Build the prompt string accepted by the ARK content task API."""

    prompt = request.prompt.strip()
    if not prompt:
        raise ValueError("prompt is required.")
    if not request.image_url.strip():
        raise ValueError("image_url is required.")
    if request.duration <= 0:
        raise ValueError("duration must be greater than zero.")

    suffix = (
        f" --duration {request.duration}"
        f" --camerafixed {_bool_token(request.camera_fixed)}"
        f" --watermark {_bool_token(request.watermark)}"
    )
    return f"{prompt}{suffix}"


def build_create_payload(request: VideoGenerationRequest) -> dict:
    """Build the JSON payload for the ARK content generation endpoint."""

    return {
        "model": request.model,
        "content": [
            {
                "type": "text",
                "text": build_task_prompt(request),
            },
            {
                "type": "image_url",
                "image_url": {"url": request.image_url},
            },
        ],
    }


def _tasks_endpoint(config: ArkConfig) -> str:
    return f"{config.base_url}/contents/generations/tasks"


def create_generation_task(request: VideoGenerationRequest, config: ArkConfig) -> str:
    """Create a new ARK content generation task and return its task id."""

    import requests

    response = requests.post(
        _tasks_endpoint(config),
        json=build_create_payload(request),
        headers={
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        },
        timeout=config.timeout_seconds,
    )
    response.raise_for_status()
    data = response.json()
    task_id = data.get("id")
    if not task_id:
        raise VideoGenerationError(f"Task creation response does not contain an id: {data}")
    return str(task_id)


def get_generation_status(task_id: str, config: ArkConfig) -> VideoTaskStatus:
    """Fetch the current task status from ARK."""

    import requests

    response = requests.get(
        f"{_tasks_endpoint(config)}/{task_id}",
        headers={"Authorization": f"Bearer {config.api_key}"},
        timeout=config.timeout_seconds,
    )
    response.raise_for_status()
    data = response.json()
    status = str(data.get("status") or "unknown")
    content = data.get("content") or {}
    return VideoTaskStatus(
        task_id=str(data.get("id") or task_id),
        status=status,
        model=data.get("model"),
        video_url=content.get("video_url"),
        raw_response=data,
    )


def wait_for_task(
    task_id: str,
    config: ArkConfig,
    *,
    poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
    max_poll_attempts: int = DEFAULT_MAX_POLL_ATTEMPTS,
) -> VideoTaskStatus:
    """Poll ARK until the task reaches a terminal status."""

    if max_poll_attempts <= 0:
        raise ValueError("max_poll_attempts must be greater than zero.")

    last_status: Optional[VideoTaskStatus] = None
    for attempt in range(max_poll_attempts):
        status = get_generation_status(task_id, config)
        last_status = status
        if status.status in TERMINAL_STATUSES:
            if status.status != "succeeded":
                raise VideoGenerationError(
                    f"Task {task_id} finished with status '{status.status}': {status.raw_response}"
                )
            return status
        if attempt < max_poll_attempts - 1:
            time.sleep(max(0.0, poll_interval_seconds))

    raise VideoGenerationError(
        f"Task {task_id} did not finish after {max_poll_attempts} status check(s). Last status: {last_status}"
    )


def download_video(video_url: str, output_path: Path, timeout_seconds: int) -> Path:
    """Download the generated video to the requested output path."""

    import requests

    destination = Path(output_path).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(video_url, timeout=timeout_seconds)
    response.raise_for_status()
    destination.write_bytes(response.content)
    return destination


def run_generation_task(
    request: VideoGenerationRequest,
    *,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    timeout_seconds: Optional[int] = None,
    poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
    max_poll_attempts: int = DEFAULT_MAX_POLL_ATTEMPTS,
) -> VideoGenerationResult:
    """Create, wait for, and optionally download an ARK video generation task."""

    config = resolve_ark_config(api_key=api_key, base_url=base_url, timeout_seconds=timeout_seconds)
    task_id = create_generation_task(request, config)
    status = wait_for_task(
        task_id,
        config,
        poll_interval_seconds=poll_interval_seconds,
        max_poll_attempts=max_poll_attempts,
    )
    downloaded_path: Optional[Path] = None
    if request.output_path and status.video_url:
        downloaded_path = download_video(status.video_url, request.output_path, config.timeout_seconds)
    return VideoGenerationResult(
        task_id=status.task_id,
        status=status.status,
        model=status.model,
        video_url=status.video_url,
        output_path=downloaded_path,
        raw_response=status.raw_response or {},
    )


def str_to_bool(value: str) -> bool:
    """Parse boolean-like CLI tokens."""

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"Invalid boolean value: {value}")


def add_common_generation_arguments(parser: argparse.ArgumentParser) -> None:
    """Register arguments shared by create and run commands."""

    parser.add_argument("prompt", help="Prompt text.")
    parser.add_argument("--image-url", required=True, help="Source image URL.")
    parser.add_argument("--model", default=None, help="ARK model name. Defaults to ARK_VIDEO_MODEL when set.")
    parser.add_argument("--duration", type=int, default=5, help="Video duration in seconds.")
    parser.add_argument("--camera-fixed", type=str_to_bool, default=False, help="Whether the camera is fixed.")
    parser.add_argument("--watermark", type=str_to_bool, default=True, help="Whether to enable watermark.")
    parser.add_argument("--output", default=None, help="Optional output video path.")
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=DEFAULT_POLL_INTERVAL_SECONDS,
        help="Polling interval in seconds.",
    )
    parser.add_argument(
        "--max-poll-attempts",
        type=int,
        default=DEFAULT_MAX_POLL_ATTEMPTS,
        help="Maximum number of status checks.",
    )
    parser.add_argument("--api-key", default=None, help="Optional ARK API key override.")
    parser.add_argument("--base-url", default=None, help="Optional ARK base URL override.")
    parser.add_argument("--timeout", type=int, default=None, help="Optional request timeout override.")


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for Doubao image-to-video tasks."""

    parser = argparse.ArgumentParser(description="Manage Doubao ARK image-to-video tasks.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create", help="Create a task and print the task id.")
    add_common_generation_arguments(create_parser)
    create_parser.add_argument("--wait", action="store_true", help="Wait for task completion after creation.")

    run_parser = subparsers.add_parser("run", help="Create a task, wait for completion, and optionally download the result.")
    add_common_generation_arguments(run_parser)

    status_parser = subparsers.add_parser("status", help="Query task status.")
    status_parser.add_argument("task_id", help="ARK task id.")
    status_parser.add_argument("--api-key", default=None, help="Optional ARK API key override.")
    status_parser.add_argument("--base-url", default=None, help="Optional ARK base URL override.")
    status_parser.add_argument("--timeout", type=int, default=None, help="Optional request timeout override.")

    download_parser = subparsers.add_parser("download", help="Download a generated video from a video URL.")
    download_parser.add_argument("--video-url", required=True, help="Signed video URL from ARK.")
    download_parser.add_argument("--output", required=True, help="Output video path.")
    download_parser.add_argument("--timeout", type=int, default=None, help="Optional request timeout override.")

    return parser


def request_from_args(args: argparse.Namespace) -> VideoGenerationRequest:
    """Convert parsed CLI arguments into a normalized task request."""

    return VideoGenerationRequest(
        prompt=args.prompt,
        image_url=args.image_url,
        model=resolve_video_model(args.model),
        duration=args.duration,
        camera_fixed=args.camera_fixed,
        watermark=args.watermark,
        output_path=Path(args.output).expanduser() if args.output else None,
    )


def print_status(status: VideoTaskStatus, *, output_fn=print) -> None:
    """Print a task status payload using the provided output function."""

    output_fn(f"Task ID: {status.task_id}")
    output_fn(f"Task status: {status.status}")
    if status.model:
        output_fn(f"Model: {status.model}")
    if status.video_url:
        output_fn(f"Video URL: {status.video_url}")


def print_result(result: VideoGenerationResult, *, output_fn=print) -> None:
    """Print a task result payload using the provided output function."""

    output_fn(f"Task created: {result.task_id}")
    output_fn(f"Task status: {result.status}")
    if result.video_url:
        output_fn(f"Video URL: {result.video_url}")
    if result.output_path:
        output_fn(f"Video saved to: {result.output_path}")


def execute_parsed_command(
    args: argparse.Namespace,
    *,
    output_fn=print,
    timeout_resolver=resolve_timeout_seconds,
    config_resolver=resolve_ark_config,
    request_builder=request_from_args,
    task_creator=create_generation_task,
    status_getter=get_generation_status,
    status_waiter=wait_for_task,
    download_handler=download_video,
    run_task=run_generation_task,
) -> int:
    """Execute parsed CLI arguments with injectable handlers for testing."""

    if args.command == "download":
        timeout_seconds = timeout_resolver(args.timeout)
        output = download_handler(args.video_url, Path(args.output), timeout_seconds)
        output_fn(f"Video saved to: {output}")
        return 0

    if args.command == "status":
        config = config_resolver(api_key=args.api_key, base_url=args.base_url, timeout_seconds=args.timeout)
        status = status_getter(args.task_id, config)
        print_status(status, output_fn=output_fn)
        return 0

    if args.command == "run":
        request = request_builder(args)
        result = run_task(
            request,
            api_key=args.api_key,
            base_url=args.base_url,
            timeout_seconds=args.timeout,
            poll_interval_seconds=args.poll_interval,
            max_poll_attempts=args.max_poll_attempts,
        )
        print_result(result, output_fn=output_fn)
        return 0

    request = request_builder(args)
    config = config_resolver(api_key=args.api_key, base_url=args.base_url, timeout_seconds=args.timeout)
    task_id = task_creator(request, config)
    output_fn(f"Task created: {task_id}")
    if not args.wait:
        return 0

    status = status_waiter(
        task_id,
        config,
        poll_interval_seconds=args.poll_interval,
        max_poll_attempts=args.max_poll_attempts,
    )
    output_fn(f"Task status: {status.status}")
    if status.video_url:
        output_fn(f"Video URL: {status.video_url}")
        if request.output_path:
            download_timeout_seconds = timeout_resolver(args.timeout)
            output = download_handler(status.video_url, request.output_path, download_timeout_seconds)
            output_fn(f"Video saved to: {output}")
    return 0


def run_cli(argv: Optional[Sequence[str]] = None, *, executor=execute_parsed_command) -> int:
    """Execute the Doubao image-to-video CLI."""

    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    return executor(args)


def main() -> int:
    """CLI main entrypoint."""

    return run_cli()


__all__ = [
    "ArkConfig",
    "DEFAULT_ARK_BASE_URL",
    "DEFAULT_ARK_TIMEOUT_SECONDS",
    "DEFAULT_MAX_POLL_ATTEMPTS",
    "DEFAULT_POLL_INTERVAL_SECONDS",
    "DEFAULT_VIDEO_MODEL",
    "TERMINAL_STATUSES",
    "VideoGenerationError",
    "VideoGenerationRequest",
    "VideoGenerationResult",
    "VideoTaskStatus",
    "build_create_payload",
    "build_task_prompt",
    "create_generation_task",
    "download_video",
    "execute_parsed_command",
    "get_generation_status",
    "resolve_ark_config",
    "resolve_timeout_seconds",
    "resolve_video_model",
    "run_generation_task",
    "str_to_bool",
    "add_common_generation_arguments",
    "build_parser",
    "request_from_args",
    "run_cli",
    "main",
    "print_result",
    "print_status",
    "wait_for_task",
]
