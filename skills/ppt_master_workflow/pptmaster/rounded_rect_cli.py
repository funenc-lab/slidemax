from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional, Sequence

from .svg_processing.rounded_rects import find_svg_files, process_svg_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='PPT Master - SVG rounded-rect to path tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
    %(prog)s skills/ppt_master_workflow/examples/demo_project_intro_ppt169_20251211
    %(prog)s skills/ppt_master_workflow/examples/demo_project_intro_ppt169_20251211 -s final
    %(prog)s skills/ppt_master_workflow/examples/demo_project_intro_ppt169_20251211/svg_output/slide_01_cover.svg

Processing:
    Convert <rect> nodes with rx or ry into equivalent <path> geometry.
''',
    )
    parser.add_argument('path', type=str, help='SVG file path or project directory')
    parser.add_argument(
        '-s',
        '--source',
        type=str,
        default='output',
        help='SVG source: output/final/flat/final_flat or a custom subdirectory',
    )
    parser.add_argument(
        '-o',
        '--output',
        type=str,
        default='svg_rounded',
        help='Output directory name for project mode',
    )
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('-q', '--quiet', action='store_true', help='Quiet mode')
    return parser


def run_cli(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    input_path = Path(args.path)

    if not input_path.exists():
        print(f'Error: path does not exist: {input_path}')
        return 1

    verbose = args.verbose and not args.quiet
    quiet = args.quiet

    if not quiet:
        print('PPT Master - SVG rounded-rect to path tool')
        print('=' * 50)

    total_converted = 0

    if input_path.is_file() and input_path.suffix.lower() == '.svg':
        output_path = input_path.with_stem(input_path.stem + '_rounded')
        if not quiet:
            print(f'  Input: {input_path}')
            print(f'  Output: {output_path}')
            print()

        success, count = process_svg_file(input_path, output_path, verbose)
        total_converted = count
        if success:
            if not quiet:
                print(f'[Done] Saved: {output_path}')
        else:
            print('[Failed] Processing failed')
            return 1
    else:
        svg_files, source_dir = find_svg_files(input_path, args.source)
        if not svg_files:
            print('Error: no SVG files found')
            return 1

        output_dir = input_path / args.output
        if not quiet:
            print(f'  Project path: {input_path}')
            print(f'  SVG source: {source_dir}')
            print(f'  Output directory: {args.output}')
            print(f'  File count: {len(svg_files)}')
            print()

        success_count = 0
        for index, svg_file in enumerate(svg_files, start=1):
            output_path = output_dir / svg_file.name
            if verbose:
                print(f'  [{index}/{len(svg_files)}] {svg_file.name}')
            success, count = process_svg_file(svg_file, output_path, verbose)
            if success:
                success_count += 1
                total_converted += count
                if not verbose and not quiet:
                    print(f'  [{index}/{len(svg_files)}] {svg_file.name} OK')
            elif not quiet:
                print(f'  [{index}/{len(svg_files)}] {svg_file.name} FAILED')

        if not quiet:
            print()
            print(f'[Done] Success: {success_count}/{len(svg_files)}')
            print(f'  Output directory: {output_dir}')

    if not quiet:
        print()
        print(f'Conversion summary: rounded rects -> path: {total_converted}')

    return 0


def main() -> None:
    raise SystemExit(run_cli())


__all__ = [
    'build_parser',
    'main',
    'run_cli',
]
