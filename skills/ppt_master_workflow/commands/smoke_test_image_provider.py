#!/usr/bin/env python3
"""Smoke test a live image provider configuration."""

from __future__ import annotations

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from pptmaster.image_generation import (  # noqa: E402,F401
    build_smoke_test_parser,
    run_smoke_test_cli,
)


def main() -> int:
    parser = build_smoke_test_parser()
    args = parser.parse_args()
    return run_smoke_test_cli(args)


__all__ = [
    'build_smoke_test_parser',
    'main',
    'run_smoke_test_cli',
]


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        print(f'Error: {error}')
        sys.exit(1)
