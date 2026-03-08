from __future__ import annotations

from typing import Optional, Sequence

from .video_generation import (
    add_common_generation_arguments,
    build_parser,
    execute_parsed_command,
    print_result,
    print_status,
    request_from_args,
    run_cli,
    str_to_bool,
)


def main(argv: Optional[Sequence[str]] = None) -> None:
    raise SystemExit(run_cli(argv))


__all__ = [
    "add_common_generation_arguments",
    "build_parser",
    "execute_parsed_command",
    "main",
    "print_result",
    "print_status",
    "request_from_args",
    "run_cli",
    "str_to_bool",
]
