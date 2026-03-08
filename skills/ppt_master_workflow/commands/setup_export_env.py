#!/usr/bin/env python3
"""PPT Master export environment setup command bridge."""

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from pptmaster.command_bridge import run_entrypoint  # noqa: E402
from pptmaster.export_setup import run_cli  # noqa: E402


def main() -> int:
    return run_cli()


__all__ = ['main', 'run_cli']


if __name__ == '__main__':
    run_entrypoint(main)
