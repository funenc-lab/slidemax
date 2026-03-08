from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover - dependency availability check
    Image = None
    PIL_IMPORT_ERROR = exc
else:
    PIL_IMPORT_ERROR = None

SUPPORTED_IMAGE_EXTENSIONS = {
    '.jpg',
    '.jpeg',
    '.png',
    '.gif',
    '.webp',
    '.bmp',
    '.tiff',
    '.tif',
}


@dataclass(frozen=True)
class ImageAnalysisRecord:
    filename: str
    width: int
    height: int
    aspect_ratio: float
    layout_hint: str
    filesize_kb: float


@dataclass(frozen=True)
class ImageAnalysisSummary:
    records: List[ImageAnalysisRecord]
    fullscreen_fit_count: int


def require_pillow() -> None:
    if Image is None:
        raise RuntimeError('Pillow is required. Install it with: pip install Pillow')


def classify_layout_hint(aspect_ratio: float) -> str:
    if aspect_ratio > 1.5:
        return 'Wide landscape'
    if aspect_ratio > 1.2:
        return 'Standard landscape'
    if aspect_ratio > 0.8:
        return 'Near square'
    if aspect_ratio > 0.6:
        return 'Standard portrait'
    return 'Narrow portrait'


def layout_note(record: ImageAnalysisRecord) -> str:
    note = record.layout_hint
    if record.aspect_ratio > 2.0:
        note += ' (good for full-width or split layouts)'
    elif record.aspect_ratio > 1.2:
        note += ' (good for full-screen or large illustrations)'
    elif record.aspect_ratio < 0.8:
        note += ' (good for side-by-side layouts)'
    return note


def analyze_directory(images_dir: Path) -> List[ImageAnalysisRecord]:
    require_pillow()
    images_dir = images_dir.expanduser().resolve()

    records: List[ImageAnalysisRecord] = []
    for file_path in sorted(images_dir.iterdir(), key=lambda path: path.name.lower()):
        if not file_path.is_file() or file_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
            continue

        try:
            with Image.open(file_path) as image:
                width, height = image.size
        except Exception:
            continue

        if height == 0:
            continue

        aspect_ratio = width / height
        records.append(
            ImageAnalysisRecord(
                filename=file_path.name,
                width=width,
                height=height,
                aspect_ratio=aspect_ratio,
                layout_hint=classify_layout_hint(aspect_ratio),
                filesize_kb=file_path.stat().st_size / 1024,
            )
        )

    return records


def summarize_records(records: Sequence[ImageAnalysisRecord]) -> ImageAnalysisSummary:
    fullscreen_fit_count = sum(1 for record in records if 1.5 <= record.aspect_ratio <= 2.0)
    return ImageAnalysisSummary(records=list(records), fullscreen_fit_count=fullscreen_fit_count)


def group_by_aspect_ratio(records: Iterable[ImageAnalysisRecord]) -> List[tuple[str, List[ImageAnalysisRecord]]]:
    groups = [
        ('Wide (>1.5)', []),
        ('Standard (1.2-1.5)', []),
        ('Square (0.8-1.2)', []),
        ('Portrait (0.6-0.8)', []),
        ('Narrow (<0.6)', []),
    ]
    grouped = {name: bucket for name, bucket in groups}

    for record in records:
        ratio = record.aspect_ratio
        if ratio > 1.5:
            grouped['Wide (>1.5)'].append(record)
        elif ratio > 1.2:
            grouped['Standard (1.2-1.5)'].append(record)
        elif ratio > 0.8:
            grouped['Square (0.8-1.2)'].append(record)
        elif ratio > 0.6:
            grouped['Portrait (0.6-0.8)'].append(record)
        else:
            grouped['Narrow (<0.6)'].append(record)

    return groups


def render_console_report(records: Sequence[ImageAnalysisRecord]) -> str:
    summary = summarize_records(records)
    lines: List[str] = []
    lines.append('')
    lines.append('=' * 100)
    lines.append('Image Size Analysis Report')
    lines.append('=' * 100)
    lines.append('')
    lines.append(f"{'No.':<4} {'Width':<7} {'Height':<7} {'Ratio':<7} {'Size':<12} {'Layout':<20} Filename")
    lines.append('-' * 100)

    for index, record in enumerate(summary.records, 1):
        lines.append(
            f"{index:<4} {record.width:<7} {record.height:<7} {record.aspect_ratio:<7.2f} "
            f"{record.filesize_kb:<12.1f} {record.layout_hint:<20} {record.filename[:40]}"
        )

    lines.append('-' * 100)
    lines.append(f'Total: {len(summary.records)} images')
    lines.append('')
    lines.append('Group by Aspect Ratio:')
    lines.append('-' * 50)

    for group_name, group_records in group_by_aspect_ratio(summary.records):
        if not group_records:
            continue
        lines.append(f'')
        lines.append(f'{group_name}: {len(group_records)} images')
        for record in group_records[:5]:
            lines.append(
                f"  - {record.width}x{record.height} (ratio {record.aspect_ratio:.2f}) - {record.filename[:35]}"
            )
        if len(group_records) > 5:
            lines.append(f'  ... and {len(group_records) - 5} more')

    lines.append('')
    lines.append('=' * 100)
    lines.append('PPT Fit Suggestions (16:9 = 1280x720)')
    lines.append('=' * 100)
    lines.append('')
    lines.append('Standard PPT canvas: 1280x720 (ratio 1.78)')
    lines.append(f'Images suitable for full-screen display: {summary.fullscreen_fit_count}')
    return '\n'.join(lines)


def render_markdown_inventory(records: Sequence[ImageAnalysisRecord]) -> str:
    lines: List[str] = []
    lines.append('')
    lines.append('=' * 100)
    lines.append('Markdown Snippet for Strategist (Copy & Paste)')
    lines.append('=' * 100)
    lines.append('')
    lines.append('## Image Inventory (Auto Scan)')
    lines.append('')
    lines.append('| Filename | Dimensions | Ratio | Layout Suggestion | Usage | Status | Description |')
    lines.append('|----------|------------|-------|-------------------|-------|--------|-------------|')
    for record in records:
        lines.append(
            f"| {record.filename} | {record.width}×{record.height} | {record.aspect_ratio:.2f} | "
            f"{layout_note(record)} | (to fill) | existing | - |"
        )
    lines.append('')
    lines.append('=' * 100)
    lines.append('')
    return '\n'.join(lines)


def write_csv(records: Sequence[ImageAnalysisRecord], csv_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['No', 'Filename', 'Width', 'Height', 'AspectRatio', 'SizeKB', 'Layout'])
        for index, record in enumerate(records, 1):
            writer.writerow(
                [
                    index,
                    record.filename,
                    record.width,
                    record.height,
                    f'{record.aspect_ratio:.2f}',
                    f'{record.filesize_kb:.1f}',
                    record.layout_hint,
                ]
            )


def default_csv_path(images_dir: Path) -> Path:
    return images_dir.expanduser().resolve().parent / 'image_analysis.csv'


def run_analysis(images_dir: Path, csv_path: Optional[Path] = None) -> ImageAnalysisSummary:
    records = analyze_directory(images_dir)
    output_path = default_csv_path(images_dir) if csv_path is None else csv_path
    if records:
        write_csv(records, output_path)
    return summarize_records(records)


def run_cli(images_dir: Path, csv_path: Optional[Path] = None) -> int:
    require_pillow()
    images_dir = images_dir.expanduser().resolve()
    if not images_dir.exists():
        print(f'Error: directory not found: {images_dir}')
        return 1
    if not images_dir.is_dir():
        print(f'Error: not a directory: {images_dir}')
        return 1

    print(f'Analyzing: {images_dir}')
    records = analyze_directory(images_dir)
    if not records:
        print('No image files found in the directory.')
        return 0

    print(render_console_report(records))
    print(render_markdown_inventory(records))

    output_path = default_csv_path(images_dir) if csv_path is None else csv_path
    write_csv(records, output_path)
    print(f'CSV saved to: {output_path}')
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Analyze a directory of images for PPT layout planning.')
    parser.add_argument('images_dir', type=Path, help='Image directory path')
    parser.add_argument('--csv', type=Path, default=None, help='Optional CSV output path')
    return parser


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    raise SystemExit(run_cli(args.images_dir, args.csv))


__all__ = [
    'ImageAnalysisRecord',
    'ImageAnalysisSummary',
    'SUPPORTED_IMAGE_EXTENSIONS',
    'build_parser',
    'analyze_directory',
    'classify_layout_hint',
    'default_csv_path',
    'group_by_aspect_ratio',
    'layout_note',
    'main',
    'render_console_report',
    'render_markdown_inventory',
    'require_pillow',
    'run_analysis',
    'run_cli',
    'summarize_records',
    'write_csv',
]
