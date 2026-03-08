from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional, Sequence

from .svg_processing.crop_images import process_directory, process_svg_images, require_pillow
from .svg_processing.embed_images import embed_images_in_svg
from .svg_processing.icons import DEFAULT_ICONS_DIR, process_svg_file as process_icon_file
from .svg_processing.image_aspect import fix_image_aspect_in_svg


def build_crop_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='SlideMax - smart image crop tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s workspace/my_project/svg_output
  %(prog)s page_01.svg --dry-run

preserveAspectRatio examples:
  xMidYMid slice   Crop from center
  xMidYMin slice   Keep the top region
  xMidYMax slice   Keep the bottom region
  xMinYMid slice   Keep the left region
  xMaxYMid slice   Keep the right region
  xMidYMid meet    Keep the full image without crop
        ''',
    )
    parser.add_argument('path', type=Path, help='SVG file or directory')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Preview changes without writing files')
    parser.add_argument('--quiet', '-q', action='store_true', help='Reduce console output')
    return parser


def run_crop_cli(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_crop_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        require_pillow()
    except RuntimeError as exc:
        print(f'Error: {exc}')
        return 1

    if not args.path.exists():
        print(f'[ERROR] Path not found: {args.path}')
        return 1

    print('SlideMax - smart image crop')
    print('=' * 50)

    if args.path.is_file():
        processed, errors = process_svg_images(args.path, dry_run=args.dry_run, verbose=not args.quiet)
    else:
        processed, errors = process_directory(args.path, dry_run=args.dry_run, verbose=not args.quiet)

    print()
    print(f'Done: {processed} image(s) cropped, {errors} error(s)')
    return 0


def build_embed_icons_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Replace SVG icon placeholders with embedded icon paths.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s svg_output/01_cover.svg
  %(prog)s svg_output/*.svg
  %(prog)s --dry-run svg_output/*.svg
  %(prog)s --icons-dir my_icons/ output.svg
        ''',
    )
    parser.add_argument('files', nargs='+', help='SVG files to process')
    parser.add_argument(
        '--icons-dir',
        type=Path,
        default=DEFAULT_ICONS_DIR,
        help=f'Icon directory path (default: {DEFAULT_ICONS_DIR})',
    )
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without writing files')
    parser.add_argument('--verbose', '-v', action='store_true', help='Print detailed replacement info')
    return parser


def run_embed_icons_cli(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_embed_icons_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if not args.icons_dir.exists():
        print(f'[ERROR] Icon directory not found: {args.icons_dir}')
        return 1

    print(f'[DIR] Icon directory: {args.icons_dir}')
    if args.dry_run:
        print('[PREVIEW] Dry-run mode')
    print()

    total_replaced = 0
    total_files = 0
    for file_pattern in args.files:
        svg_path = Path(file_pattern)
        if not svg_path.exists():
            print(f'[ERROR] File not found: {svg_path}')
            continue
        count = process_icon_file(svg_path, args.icons_dir, args.dry_run, args.verbose)
        total_replaced += count
        if count > 0:
            total_files += 1

    print()
    summary_suffix = ' (preview)' if args.dry_run else ' replaced'
    print(f'[Summary] Total: {total_files} file(s), {total_replaced} icon(s){summary_suffix}')
    return 0


def build_fix_aspect_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Fix SVG image aspect ratios to avoid PowerPoint stretching.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s slide_01.svg
  %(prog)s *.svg
  %(prog)s --dry-run *.svg
  %(prog)s workspace/xxx/svg_output/*.svg
        ''',
    )
    parser.add_argument('files', nargs='+', help='SVG files to process')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Preview changes without writing files')
    parser.add_argument('--quiet', '-q', action='store_true', help='Reduce console output')
    return parser


def run_fix_aspect_cli(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_fix_aspect_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.dry_run:
        print('[INFO] Dry-run mode: preview only\n')

    total_fixed = 0
    total_files = 0
    for svg_file in args.files:
        path = Path(svg_file)
        if not path.exists():
            if not args.quiet:
                print(f'[ERROR] File not found: {svg_file}')
            continue
        if path.suffix.lower() != '.svg':
            if not args.quiet:
                print(f'[SKIP] Skipping non-SVG file: {svg_file}')
            continue
        if not args.quiet:
            print(f'\n[FILE] {path.name}')
        fixed = fix_image_aspect_in_svg(path, dry_run=args.dry_run, verbose=not args.quiet)
        if fixed > 0:
            total_fixed += fixed
            total_files += 1
        elif not args.quiet:
            print('       No changes needed')

    print(f"\n{'=' * 50}")
    if args.dry_run:
        print(f'[PREVIEW] Will fix {total_fixed} image(s) across {total_files} file(s)')
    else:
        print(f'[DONE] Fixed {total_fixed} image(s) across {total_files} file(s)')
    return 0


def build_embed_images_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Convert external SVG image references into embedded Base64 data URIs.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s 01_cover.svg
  %(prog)s *.svg
  %(prog)s --dry-run *.svg
        ''',
    )
    parser.add_argument('files', nargs='+', help='SVG files to process')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Preview changes without writing files')
    return parser


def run_embed_images_cli(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_embed_images_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.dry_run:
        print('[INFO] Dry-run mode: preview only\n')

    total_images = 0
    total_files = 0
    for svg_file in args.files:
        path = Path(svg_file)
        if not path.exists():
            print(f'[ERROR] File not found: {svg_file}')
            continue
        if path.suffix.lower() != '.svg':
            print(f'[SKIP] Skipping non-SVG file: {svg_file}')
            continue

        images, _ = embed_images_in_svg(path, dry_run=args.dry_run)
        if images > 0:
            total_images += images
            total_files += 1

    print(f"\n{'=' * 50}")
    if args.dry_run:
        print(f'[PREVIEW] Will process {total_images} images in {total_files} files')
    else:
        print(f'[DONE] Embedded {total_images} images in {total_files} files')
    return 0


def crop_main() -> None:
    raise SystemExit(run_crop_cli())


def embed_icons_main() -> None:
    raise SystemExit(run_embed_icons_cli())


def fix_aspect_main() -> None:
    raise SystemExit(run_fix_aspect_cli())


def embed_images_main() -> None:
    raise SystemExit(run_embed_images_cli())


__all__ = [
    'build_crop_parser',
    'build_embed_icons_parser',
    'build_embed_images_parser',
    'build_fix_aspect_parser',
    'crop_main',
    'embed_icons_main',
    'embed_images_main',
    'fix_aspect_main',
    'run_crop_cli',
    'run_embed_icons_cli',
    'run_embed_images_cli',
    'run_fix_aspect_cli',
]
