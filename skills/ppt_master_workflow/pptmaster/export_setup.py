"""Setup helpers for PPT export dependencies."""

from __future__ import annotations

import argparse
import subprocess
import sys
from typing import List, Optional, Sequence


RENDERER_PACKAGES = {
    'none': [],
    'cairosvg': ['cairosvg'],
    'svglib': ['svglib', 'reportlab'],
}

BASE_EXPORT_PACKAGES = ['python-pptx']


def build_install_command(renderer: str = 'cairosvg') -> List[str]:
    """Build the canonical pip install command for PPT export dependencies."""

    normalized_renderer = renderer.strip().lower()
    if normalized_renderer not in RENDERER_PACKAGES:
        supported = ', '.join(sorted(RENDERER_PACKAGES.keys()))
        raise ValueError(f'Unsupported renderer: {renderer}. Supported: {supported}')

    packages = BASE_EXPORT_PACKAGES + RENDERER_PACKAGES[normalized_renderer]
    return [sys.executable, '-m', 'pip', 'install', *packages]


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for one-click export environment setup."""

    parser = argparse.ArgumentParser(
        description='Install PPT export dependencies for PPT Master.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s
  %(prog)s --renderer svglib
  %(prog)s --renderer none --dry-run
''',
    )
    parser.add_argument(
        '--renderer',
        choices=sorted(RENDERER_PACKAGES.keys()),
        default='cairosvg',
        help='Compatibility renderer package set to install.',
    )
    parser.add_argument('--dry-run', action='store_true', help='Print the install command without executing it.')
    return parser


def run_cli(argv: Optional[Sequence[str]] = None) -> int:
    """Run the export dependency installer CLI."""

    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    command = build_install_command(renderer=args.renderer)
    print('PPT export dependency setup')
    print('=' * 60)
    print(f'Renderer preset: {args.renderer}')
    print(f'Command: {" ".join(command)}')

    if args.dry_run:
        print('\n[OK] Dry run complete')
        return 0

    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        print(f'\n[ERROR] Installation failed with exit code {completed.returncode}')
        return completed.returncode

    print('\n[OK] Export dependencies installed')
    if args.renderer == 'cairosvg':
        print('Hint: on macOS you may still need `brew install cairo` if CairoSVG runtime libraries are missing.')
    return 0


__all__ = [
    'BASE_EXPORT_PACKAGES',
    'RENDERER_PACKAGES',
    'build_install_command',
    'build_parser',
    'run_cli',
]
