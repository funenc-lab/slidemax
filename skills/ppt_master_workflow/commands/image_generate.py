#!/usr/bin/env python3
"""Provider-neutral image generation CLI for PPT Master."""

from __future__ import annotations

import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from pptmaster.image_generation import build_parser, run_cli

from pptmaster.command_bridge import run_entrypoint  # noqa: E402

__all__ = [
    "build_parser",
    "main",
    "run_cli",
]


def main() -> int:
    parser = build_parser(
        description="Generate images using the configured PPT Master provider.",
        default_provider="gemini",
        default_prompt="Generate image",
        include_provider_argument=True,
    )
    args = parser.parse_args()
    return run_cli(args)


if __name__ == "__main__":
    run_entrypoint(main, catch_exceptions=True)
