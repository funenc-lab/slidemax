from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Optional, Sequence, Tuple

from .svg_processing.flatten_text import compute_default_output_base, process_svg_file


def interactive_get_paths() -> Tuple[Optional[str], Optional[str]]:
    print('[Interactive mode] No input path provided.')
    print('Enter an SVG file path or a directory containing SVG files.')
    print('Enter q to cancel.\n')

    while True:
        raw = input('Input path (file/dir): ').strip()
        if raw.lower() in {'q', 'quit', 'exit'} or raw == '':
            return None, None
        input_path = os.path.expanduser(raw)
        if os.path.exists(input_path):
            break
        print('Path does not exist. Try again or enter q to cancel.')

    default_output = compute_default_output_base(input_path)
    prompt = f'Output path [default: {default_output}]: '
    raw_output = input(prompt).strip()
    output_path = os.path.expanduser(raw_output) if raw_output else default_output
    return input_path, output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Flatten <tspan> lines into multiple <text> nodes for better compatibility.',
        add_help=True,
    )
    parser.add_argument('input', nargs='?', help='Input path: SVG file or directory')
    parser.add_argument('output', nargs='?', help='Optional output file or directory')
    parser.add_argument(
        '-i',
        '--interactive',
        action='store_true',
        help='Run in interactive prompt mode to input paths',
    )
    return parser


def process_directory(input_path: str, output_base: Optional[str]) -> int:
    if output_base is None:
        output_base = compute_default_output_base(input_path)

    total = 0
    changed_count = 0
    output_base_abs = os.path.abspath(output_base)
    for root, dirs, files in os.walk(input_path):
        dirs[:] = [
            directory
            for directory in dirs
            if os.path.abspath(os.path.join(root, directory)) != output_base_abs
        ]
        rel_root = os.path.relpath(root, input_path)
        for filename in files:
            if not filename.lower().endswith('.svg'):
                continue
            source = os.path.join(root, filename)
            destination = (
                os.path.join(output_base, rel_root, filename)
                if rel_root != '.'
                else os.path.join(output_base, filename)
            )
            total += 1
            changed = process_svg_file(source, destination)
            if changed:
                changed_count += 1
    print(f'Processed {total} SVG file(s). Flattened: {changed_count}.')
    print(f'Output written to: {output_base}')
    return 0


def process_single_file(input_path: str, output_base: Optional[str]) -> int:
    source = input_path
    if output_base is None:
        output_base = compute_default_output_base(source)
    changed = process_svg_file(source, output_base)
    print(f'Written: {output_base} (flattened: {changed})')
    return 0


def run_cli(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.interactive or not args.input:
        input_path, output_base = interactive_get_paths()
        if not input_path:
            print('Canceled. Usage: python3 skills/slidemax_workflow/commands/flatten_tspan.py <input_dir_or_svg> [output_dir]')
            return 0
    else:
        input_path = args.input
        output_base = args.output

    if os.path.isdir(input_path):
        return process_directory(input_path, output_base)
    return process_single_file(input_path, output_base)


def main() -> None:
    raise SystemExit(run_cli())


__all__ = [
    'build_parser',
    'interactive_get_paths',
    'main',
    'process_directory',
    'process_single_file',
    'run_cli',
]
