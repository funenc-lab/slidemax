#!/usr/bin/env python3
"""PPT Master project manager command bridge."""

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from pptmaster.project_management import main  # noqa: E402,F401

__all__ = ['main']


if __name__ == '__main__':
    main()
