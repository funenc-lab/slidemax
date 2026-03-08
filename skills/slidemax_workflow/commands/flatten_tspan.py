#!/usr/bin/env python3
"""Flatten tspan-based SVG text into simpler text nodes."""

from __future__ import annotations

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from slidemax.flatten_text_cli import (  # noqa: E402,F401
    build_parser,
    interactive_get_paths,
    main,
    process_directory,
    process_single_file,
    run_cli,
)

from slidemax.command_bridge import run_entrypoint  # noqa: E402
__all__ = [
    'build_parser',
    'interactive_get_paths',
    'main',
    'process_directory',
    'process_single_file',
    'run_cli',
]


if __name__ == '__main__':
    run_entrypoint(main)
