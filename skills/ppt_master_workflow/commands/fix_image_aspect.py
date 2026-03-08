#!/usr/bin/env python3
"""Fix SVG image frames to preserve source aspect ratios."""

from __future__ import annotations

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from pptmaster.svg_asset_cli import build_fix_aspect_parser, fix_aspect_main, run_fix_aspect_cli  # noqa: E402,F401

__all__ = [
    'build_fix_aspect_parser',
    'fix_aspect_main',
    'run_fix_aspect_cli',
]


if __name__ == '__main__':
    fix_aspect_main()
