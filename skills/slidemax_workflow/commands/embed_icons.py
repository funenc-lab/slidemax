#!/usr/bin/env python3
"""Embed icon placeholders into SVG files."""

from __future__ import annotations

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from slidemax.svg_asset_cli import build_embed_icons_parser, embed_icons_main, run_embed_icons_cli  # noqa: E402,F401

from slidemax.command_bridge import run_entrypoint  # noqa: E402
__all__ = [
    'build_embed_icons_parser',
    'embed_icons_main',
    'run_embed_icons_cli',
]


if __name__ == '__main__':
    run_entrypoint(embed_icons_main)
