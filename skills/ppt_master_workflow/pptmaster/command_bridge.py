"""Shared helpers for command bridge entrypoints."""

from __future__ import annotations

from typing import Callable, Optional


def run_entrypoint(
    main_fn: Callable[[], Optional[int]],
    *,
    catch_exceptions: bool = False,
    error_output=print,
) -> None:
    """Execute a bridge entrypoint and terminate with the returned exit code."""

    try:
        raise SystemExit(main_fn())
    except SystemExit:
        raise
    except Exception as error:
        if not catch_exceptions:
            raise
        error_output(f"Error: {error}")
        raise SystemExit(1) from error
