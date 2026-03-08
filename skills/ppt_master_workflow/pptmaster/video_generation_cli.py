from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional, Sequence

from .video_generation import (
    DEFAULT_MAX_POLL_ATTEMPTS,
    DEFAULT_POLL_INTERVAL_SECONDS,
    VideoGenerationRequest,
    create_generation_task,
    download_video,
    get_generation_status,
    resolve_ark_config,
    resolve_timeout_seconds,
    resolve_video_model,
    run_generation_task,
    wait_for_task,
)


def str_to_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {'1', 'true', 'yes', 'y', 'on'}:
        return True
    if normalized in {'0', 'false', 'no', 'n', 'off'}:
        return False
    raise argparse.ArgumentTypeError(f'Invalid boolean value: {value}')


def add_common_generation_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('prompt', help='Prompt text.')
    parser.add_argument('--image-url', required=True, help='Source image URL.')
    parser.add_argument('--model', default=None, help='ARK model name. Defaults to ARK_VIDEO_MODEL when set.')
    parser.add_argument('--duration', type=int, default=5, help='Video duration in seconds.')
    parser.add_argument('--camera-fixed', type=str_to_bool, default=False, help='Whether the camera is fixed.')
    parser.add_argument('--watermark', type=str_to_bool, default=True, help='Whether to enable watermark.')
    parser.add_argument('--output', default=None, help='Optional output video path.')
    parser.add_argument(
        '--poll-interval',
        type=float,
        default=DEFAULT_POLL_INTERVAL_SECONDS,
        help='Polling interval in seconds.',
    )
    parser.add_argument(
        '--max-poll-attempts',
        type=int,
        default=DEFAULT_MAX_POLL_ATTEMPTS,
        help='Maximum number of status checks.',
    )
    parser.add_argument('--api-key', default=None, help='Optional ARK API key override.')
    parser.add_argument('--base-url', default=None, help='Optional ARK base URL override.')
    parser.add_argument('--timeout', type=int, default=None, help='Optional request timeout override.')


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Manage Doubao ARK image-to-video tasks.')
    subparsers = parser.add_subparsers(dest='command', required=True)

    create_parser = subparsers.add_parser('create', help='Create a task and print the task id.')
    add_common_generation_arguments(create_parser)
    create_parser.add_argument('--wait', action='store_true', help='Wait for task completion after creation.')

    run_parser = subparsers.add_parser('run', help='Create a task, wait for completion, and optionally download the result.')
    add_common_generation_arguments(run_parser)

    status_parser = subparsers.add_parser('status', help='Query task status.')
    status_parser.add_argument('task_id', help='ARK task id.')
    status_parser.add_argument('--api-key', default=None, help='Optional ARK API key override.')
    status_parser.add_argument('--base-url', default=None, help='Optional ARK base URL override.')
    status_parser.add_argument('--timeout', type=int, default=None, help='Optional request timeout override.')

    download_parser = subparsers.add_parser('download', help='Download a generated video from a video URL.')
    download_parser.add_argument('--video-url', required=True, help='Signed video URL from ARK.')
    download_parser.add_argument('--output', required=True, help='Output video path.')
    download_parser.add_argument('--timeout', type=int, default=None, help='Optional request timeout override.')

    return parser


def request_from_args(args: argparse.Namespace) -> VideoGenerationRequest:
    return VideoGenerationRequest(
        prompt=args.prompt,
        image_url=args.image_url,
        model=resolve_video_model(args.model),
        duration=args.duration,
        camera_fixed=args.camera_fixed,
        watermark=args.watermark,
        output_path=Path(args.output).expanduser() if args.output else None,
    )


def print_status(status) -> None:
    print(f'Task ID: {status.task_id}')
    print(f'Task status: {status.status}')
    if status.model:
        print(f'Model: {status.model}')
    if status.video_url:
        print(f'Video URL: {status.video_url}')


def print_result(result) -> None:
    print(f'Task created: {result.task_id}')
    print(f'Task status: {result.status}')
    if result.video_url:
        print(f'Video URL: {result.video_url}')
    if result.output_path:
        print(f'Video saved to: {result.output_path}')


def run_cli(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == 'download':
        timeout_seconds = resolve_timeout_seconds(args.timeout)
        output = download_video(args.video_url, Path(args.output), timeout_seconds)
        print(f'Video saved to: {output}')
        return 0

    if args.command == 'status':
        config = resolve_ark_config(api_key=args.api_key, base_url=args.base_url, timeout_seconds=args.timeout)
        status = get_generation_status(args.task_id, config)
        print_status(status)
        return 0

    if args.command == 'run':
        result = run_generation_task(
            request_from_args(args),
            api_key=args.api_key,
            base_url=args.base_url,
            timeout_seconds=args.timeout,
            poll_interval_seconds=args.poll_interval,
            max_poll_attempts=args.max_poll_attempts,
        )
        print_result(result)
        return 0

    request = request_from_args(args)
    config = resolve_ark_config(api_key=args.api_key, base_url=args.base_url, timeout_seconds=args.timeout)
    task_id = create_generation_task(request, config)
    print(f'Task created: {task_id}')
    if not args.wait:
        return 0

    status = wait_for_task(
        task_id,
        config,
        poll_interval_seconds=args.poll_interval,
        max_poll_attempts=args.max_poll_attempts,
    )
    print_status(status)
    if status.video_url and request.output_path:
        output = download_video(status.video_url, request.output_path, config.timeout_seconds)
        print(f'Video saved to: {output}')
    return 0


def main() -> None:
    raise SystemExit(run_cli())


__all__ = [
    'add_common_generation_arguments',
    'build_parser',
    'main',
    'print_result',
    'print_status',
    'request_from_args',
    'run_cli',
    'str_to_bool',
]
