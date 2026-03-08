#!/usr/bin/env python3
"""SlideMax asset policy audit command bridge."""

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from slidemax.asset_policy import main  # noqa: E402,F401
from slidemax.command_bridge import run_entrypoint  # noqa: E402

__all__ = ["main"]


if __name__ == "__main__":
    run_entrypoint(main, catch_exceptions=True)
