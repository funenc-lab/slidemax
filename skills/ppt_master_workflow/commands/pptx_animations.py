#!/usr/bin/env python3
"""PPT Master PPTX animation compatibility bridge."""

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from pptmaster.pptx_animations import (  # noqa: E402,F401
    ANIMATIONS,
    SPEED_MAP,
    TRANSITIONS,
    create_timing_xml,
    create_transition_xml,
    duration_to_speed,
    get_animation_help,
    get_available_animations,
    get_available_transitions,
    get_transition_help,
)

__all__ = [
    'TRANSITIONS',
    'ANIMATIONS',
    'SPEED_MAP',
    'duration_to_speed',
    'create_transition_xml',
    'create_timing_xml',
    'get_available_transitions',
    'get_available_animations',
    'get_transition_help',
    'get_animation_help',
]
