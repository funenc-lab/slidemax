#!/usr/bin/env python3
"""PPT Master project utility command bridge."""

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from pptmaster.project_utils import (  # noqa: E402
    CANVAS_FORMATS,
    CANVAS_FORMAT_ALIASES,
    find_all_projects,
    format_file_size,
    get_project_info,
    get_project_stats,
    main,
    normalize_canvas_format,
    parse_project_name,
    validate_project_structure,
    validate_svg_viewbox,
)

from pptmaster.command_bridge import run_entrypoint  # noqa: E402
__all__ = [
    'CANVAS_FORMATS',
    'CANVAS_FORMAT_ALIASES',
    'normalize_canvas_format',
    'parse_project_name',
    'get_project_info',
    'validate_project_structure',
    'validate_svg_viewbox',
    'find_all_projects',
    'format_file_size',
    'get_project_stats',
    'main',
]


if __name__ == '__main__':
    run_entrypoint(main)
