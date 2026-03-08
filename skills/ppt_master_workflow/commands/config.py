#!/usr/bin/env python3
"""PPT Master configuration command bridge."""

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from pptmaster.config import (  # noqa: E402
    CANVAS_FORMATS,
    CHART_TEMPLATES_DIR,
    COMMANDS_DIR,
    Config,
    DESIGN_COLORS,
    DOCS_DIR,
    EXAMPLES_DIR,
    EXTRA_EXAMPLE_PATHS_ENV,
    FONT_SIZES,
    FONTS,
    INDUSTRY_COLORS,
    LAYOUT_MARGINS,
    PROJECT_ROOT,
    ROLES_DIR,
    SKILL_ROOT as PACKAGE_SKILL_ROOT,
    SVG_CONSTRAINTS,
    TEMPLATES_DIR,
    TESTS_DIR,
    TOOLS_DIR,
    WORKSPACE_DIR,
    get_example_dirs,
    get_extra_example_dirs,
    main,
)

SKILL_ROOT = PACKAGE_SKILL_ROOT

__all__ = [
    'SKILL_ROOT',
    'PROJECT_ROOT',
    'TOOLS_DIR',
    'COMMANDS_DIR',
    'DOCS_DIR',
    'TEMPLATES_DIR',
    'EXAMPLES_DIR',
    'WORKSPACE_DIR',
    'ROLES_DIR',
    'TESTS_DIR',
    'CHART_TEMPLATES_DIR',
    'EXTRA_EXAMPLE_PATHS_ENV',
    'get_extra_example_dirs',
    'get_example_dirs',
    'CANVAS_FORMATS',
    'DESIGN_COLORS',
    'INDUSTRY_COLORS',
    'FONTS',
    'FONT_SIZES',
    'LAYOUT_MARGINS',
    'SVG_CONSTRAINTS',
    'Config',
    'main',
]


if __name__ == '__main__':
    main()
