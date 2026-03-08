#!/usr/bin/env python3
"""Legacy Gemini wrapper for SlideMax image generation."""

from __future__ import annotations

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from slidemax.image_generation import (  # noqa: E402,F401
    DEFAULT_MODELS,
    ImageGenerationRequest,
    build_legacy_gemini_parser,
    generate_image,
    generate_with_legacy_gemini,
    legacy_gemini_main,
    resolve_provider_config,
    run_legacy_gemini_cli,
)

from slidemax.command_bridge import run_entrypoint  # noqa: E402
__all__ = [
    'DEFAULT_MODELS',
    'ImageGenerationRequest',
    'build_legacy_gemini_parser',
    'generate_image',
    'generate_with_legacy_gemini',
    'legacy_gemini_main',
    'resolve_provider_config',
    'run_legacy_gemini_cli',
]


if __name__ == '__main__':
    run_entrypoint(legacy_gemini_main, catch_exceptions=True)
