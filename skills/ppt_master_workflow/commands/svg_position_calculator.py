#!/usr/bin/env python3
"""PPT Master SVG position calculator command bridge."""

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from pptmaster.svg_position_cli import (  # noqa: E402,F401
    analyze_svg_file,
    build_chart_area,
    build_parser,
    configure_console_encoding,
    format_canvas_label,
    from_json_config,
    handle_calc_command,
    handle_validate_command,
    interactive_mode,
    main,
    read_text_file,
    render_custom_line_report,
    run_cli,
)

__all__ = [
    'analyze_svg_file',
    'build_chart_area',
    'build_parser',
    'configure_console_encoding',
    'format_canvas_label',
    'from_json_config',
    'handle_calc_command',
    'handle_validate_command',
    'interactive_mode',
    'main',
    'read_text_file',
    'render_custom_line_report',
    'run_cli',
]


if __name__ == '__main__':
    main()
