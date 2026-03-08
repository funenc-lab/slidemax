"""Shared finalize pipeline for PPT Master SVG post-processing."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

from .config import TEMPLATES_DIR
from .finalize_steps import (
    STEP_CHOICES,
    FinalizeContext,
    build_step_registry,
    copy_svg_output,
)


@dataclass(frozen=True)
class FinalizeOptions:
    """Typed options for the SVG finalize pipeline."""

    steps: Tuple[str, ...] = STEP_CHOICES

    @classmethod
    def from_only_steps(cls, steps: Iterable[str] | None) -> "FinalizeOptions":
        """Create options from the ``--only`` CLI argument."""

        if not steps:
            return cls()

        selected = set(steps)
        return cls(steps=tuple(step_name for step_name in STEP_CHOICES if step_name in selected))

    def enabled_steps(self) -> List[str]:
        """Return enabled step names in execution order."""

        return list(self.steps)


def safe_print(text: str) -> None:
    """Print text safely across terminals with limited Unicode support."""

    try:
        print(text)
    except UnicodeEncodeError:
        sanitized = text.replace("✅", "[OK]").replace("❌", "[ERROR]")
        sanitized = sanitized.replace("📁", "[DIR]").replace("📄", "[FILE]")
        print(sanitized)


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for finalize entrypoints."""

    parser = argparse.ArgumentParser(
        description="PPT Master - SVG finalize pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s workspace/my_project           # Run all steps (default)
  %(prog)s workspace/my_project --only embed-icons fix-rounded
  %(prog)s workspace/my_project -q        # Quiet mode

Step names for --only:
  embed-icons
  crop-images
  fix-aspect
  embed-images
  flatten-text
  fix-rounded
        """,
    )
    parser.add_argument("project_dir", type=Path, help="Project directory")
    parser.add_argument(
        "--only",
        nargs="+",
        metavar="STEP",
        choices=STEP_CHOICES,
        help="Run only the specified steps",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Preview operations without modifying files",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Reduce console output",
    )
    return parser


def build_context(project_dir: Path) -> FinalizeContext:
    """Build the resolved filesystem context for the finalize pipeline."""

    return FinalizeContext(
        project_dir=project_dir,
        svg_output=project_dir / "svg_output",
        svg_final=project_dir / "svg_final",
        icons_dir=TEMPLATES_DIR / "icons",
    )


def finalize_project(
    project_dir: Path,
    options: FinalizeOptions,
    dry_run: bool = False,
    quiet: bool = False,
) -> bool:
    """Run the full finalize pipeline for a project."""

    context = build_context(project_dir)

    if not context.svg_output.exists():
        safe_print(f"[ERROR] Missing svg_output directory: {context.svg_output}")
        return False

    svg_files = list(context.svg_output.glob("*.svg"))
    if not svg_files:
        safe_print("[ERROR] No SVG files found in svg_output")
        return False

    if not quiet:
        print()
        safe_print(f"[DIR] Project: {project_dir.name}")
        safe_print(f"[FILE] {len(svg_files)} SVG files")

    if dry_run:
        safe_print("[PREVIEW] Dry-run mode, no changes applied")
        return True

    copy_svg_output(context.svg_output, context.svg_final)

    if not quiet:
        print()

    step_registry = build_step_registry()
    enabled_steps = [step_registry[step_name] for step_name in options.enabled_steps()]
    total_steps = len(enabled_steps)
    svg_final_files = list(context.svg_final.glob("*.svg"))

    for index, step in enumerate(enabled_steps, start=1):
        if not quiet:
            safe_print(f"[{index}/{total_steps}] {step.title}...")

        count = step.runner(context, svg_final_files)

        if quiet:
            continue

        if count > 0:
            safe_print(f"      {count} {step.success_suffix}")
        else:
            safe_print(f"      {step.empty_message}")

    if not quiet:
        print()
        safe_print("[OK] Finalize complete")
        print()
        print("Next step:")
        print(f"  python3 skills/ppt_master_workflow/commands/svg_to_pptx.py \"{project_dir}\" -s final")

    return True


def run_cli(args: argparse.Namespace) -> int:
    """Execute the finalize CLI from parsed arguments."""

    if not args.project_dir.exists():
        safe_print(f"[ERROR] Project directory not found: {args.project_dir}")
        return 1

    options = FinalizeOptions.from_only_steps(args.only)
    success = finalize_project(args.project_dir, options, args.dry_run, args.quiet)
    return 0 if success else 1

def main(argv: Optional[Sequence[str]] = None) -> None:
    """Execute the finalize CLI entrypoint."""

    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    raise SystemExit(run_cli(args))

