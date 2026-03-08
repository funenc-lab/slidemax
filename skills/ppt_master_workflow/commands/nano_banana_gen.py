#!/usr/bin/env python3
"""Legacy Gemini wrapper for PPT Master image generation."""

from __future__ import annotations

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from pptmaster.image_generation import (  # noqa: E402,F401
    DEFAULT_MODELS,
    ImageGenerationRequest,
    build_legacy_gemini_parser,
    generate_image,
    generate_with_legacy_gemini,
    legacy_gemini_main,
    resolve_provider_config,
    run_legacy_gemini_cli,
)

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
    legacy_gemini_main()
