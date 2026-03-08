#!/usr/bin/env python3
"""Doubao ARK image-to-video command bridge."""

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from pptmaster.video_generation import (  # noqa: E402,F401
    add_common_generation_arguments,
    build_parser,
    main,
    print_result,
    print_status,
    request_from_args,
    run_cli,
    str_to_bool,
)

from pptmaster.command_bridge import run_entrypoint  # noqa: E402
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


if __name__ == '__main__':
    run_entrypoint(main)
