"""Shared notes splitting service for SlideMax projects."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

HEADING_RE = re.compile(r'^(#{1,6})\s*(.+?)\s*$')
HR_RE = re.compile(r'^\s*[-*]{3,}\s*$')


def normalize_title(title: str) -> str:
    """Normalize a title for fuzzy matching against SVG filenames."""

    if not title:
        return ''
    text = title.strip()
    text = re.sub(r'[^0-9A-Za-z\u4e00-\u9fff]+', '_', text)
    text = re.sub(r'_+', '_', text).strip('_')
    return text.lower()


def extract_leading_number(text: str) -> Optional[int]:
    """Extract a leading slide number from common title patterns."""

    if not text:
        return None

    direct_match = re.match(r'^(\d{1,3})', text.strip())
    if direct_match:
        return int(direct_match.group(1))

    lower_text = text.lower().strip()
    english_match = re.match(r'^(?:slide|page|p)\s*[-_:]?\s*(\d{1,3})', lower_text)
    if english_match:
        return int(english_match.group(1))

    chinese_match = re.match('^\u7b2c\s*(\d{1,3})\s*[\u9875\u5f20]', lower_text)
    if chinese_match:
        return int(chinese_match.group(1))

    return None


def build_match_maps(svg_stems: List[str]) -> Tuple[Set[str], Dict[str, List[str]], Dict[int, List[str]]]:
    """Build lookup maps used to match note headings against SVG file stems."""

    exact = set(svg_stems)
    normalized_map: Dict[str, List[str]] = {}
    number_map: Dict[int, List[str]] = {}

    for stem in svg_stems:
        normalized = normalize_title(stem)
        if normalized:
            normalized_map.setdefault(normalized, []).append(stem)
        number = extract_leading_number(stem)
        if number is not None:
            number_map.setdefault(number, []).append(stem)

    return exact, normalized_map, number_map


def match_title(
    raw_title: str,
    exact: Set[str],
    normalized_map: Dict[str, List[str]],
    number_map: Dict[int, List[str]],
    svg_stems: Optional[List[str]] = None,
) -> Optional[str]:
    """Match a markdown heading title to a single SVG stem."""

    if raw_title in exact:
        return raw_title

    normalized = normalize_title(raw_title)
    if normalized in normalized_map and len(normalized_map[normalized]) == 1:
        return normalized_map[normalized][0]

    number = extract_leading_number(raw_title)
    if number is not None and number in number_map and len(number_map[number]) == 1:
        return number_map[number][0]

    if normalized and svg_stems:
        candidates = [stem for stem in svg_stems if normalized in normalize_title(stem)]
        if len(candidates) == 1:
            return candidates[0]

    return None


def find_svg_files(project_path: Path) -> List[Path]:
    """Find SVG files inside a project's `svg_output` directory."""

    svg_dir = project_path / 'svg_output'
    if not svg_dir.exists():
        print(f'[ERROR] Missing directory: {svg_dir}')
        return []
    return sorted(svg_dir.glob('*.svg'))


def parse_total_md(md_path: Path, svg_stems: Optional[List[str]] = None, verbose: bool = True) -> Dict[str, str]:
    """Parse `notes/total.md` and map its sections to SVG stems."""

    if not md_path.exists():
        print(f'[ERROR] Missing file: {md_path}')
        return {}

    try:
        content = md_path.read_text(encoding='utf-8')
    except Exception as exc:
        print(f'[ERROR] Unable to read file {md_path}: {exc}')
        return {}

    svg_stems = svg_stems or []
    exact, normalized_map, number_map = build_match_maps(svg_stems)

    notes: Dict[str, str] = {}
    current_key: Optional[str] = None
    current_lines: List[str] = []
    unmatched_headings: List[str] = []

    for line in content.splitlines():
        heading_match = HEADING_RE.match(line)
        if heading_match:
            raw_title = heading_match.group(2).strip()
            matched = match_title(raw_title, exact, normalized_map, number_map, svg_stems)
            if matched:
                if current_key is not None:
                    text = '\n'.join(current_lines).strip()
                    if current_key in notes and text:
                        notes[current_key] = (notes[current_key].rstrip() + '\n\n' + text).strip()
                    elif current_key not in notes:
                        notes[current_key] = text
                current_key = matched
                current_lines = []
                continue
            unmatched_headings.append(raw_title)

        if HR_RE.match(line):
            continue
        if current_key is not None:
            current_lines.append(line)

    if current_key is not None:
        text = '\n'.join(current_lines).strip()
        if current_key in notes and text:
            notes[current_key] = (notes[current_key].rstrip() + '\n\n' + text).strip()
        elif current_key not in notes:
            notes[current_key] = text

    if verbose and unmatched_headings:
        print('\n[INFO] Ignored unmatched headings:')
        for title in unmatched_headings[:10]:
            print(f'  - {title}')
        if len(unmatched_headings) > 10:
            print(f'  ... and {len(unmatched_headings) - 10} more')

    return notes


def check_svg_note_mapping(svg_files: List[Path], notes: Dict[str, str]) -> Tuple[bool, List[str]]:
    """Check whether every SVG file has a matching notes section."""

    missing_notes = [svg_path.stem for svg_path in svg_files if svg_path.stem not in notes]
    return len(missing_notes) == 0, missing_notes


def split_notes(notes: Dict[str, str], output_dir: Path, verbose: bool = True) -> bool:
    """Write one markdown note file per slide title."""

    if not notes:
        print('[ERROR] No notes content was found')
        return False

    output_dir.mkdir(parents=True, exist_ok=True)
    success_count = 0

    for title, content in notes.items():
        output_path = output_dir / f'{title}.md'
        try:
            output_path.write_text(content, encoding='utf-8')
            if verbose:
                print(f'  Generated: {output_path.name}')
            success_count += 1
        except Exception as exc:
            if verbose:
                print(f'  [ERROR] Unable to write {output_path}: {exc}')

    if verbose:
        print(f'\n[Done] Generated {success_count}/{len(notes)} file(s)')

    return success_count == len(notes)


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for splitting `notes/total.md`."""

    parser = argparse.ArgumentParser(
        description='SlideMax notes splitting tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
    %(prog)s workspace/<project>_ppt169_YYYYMMDD
    %(prog)s workspace/<project>_ppt169_YYYYMMDD -o notes
    %(prog)s workspace/<project>_ppt169_YYYYMMDD -q

Features:
    - Read notes/total.md
    - Validate SVG-to-note mapping
    - Split notes into one file per slide
    - Use SVG filenames for output names
''',
    )
    parser.add_argument('project_path', type=str, help='Project directory path')
    parser.add_argument('-o', '--output', type=str, default=None, help='Output directory path')
    parser.add_argument('-q', '--quiet', action='store_true', help='Quiet mode')
    return parser


def run_cli(argv: Optional[Sequence[str]] = None) -> int:
    """Execute the CLI entrypoint for note splitting."""

    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    project_path = Path(args.project_path)
    if not project_path.exists():
        print(f'[ERROR] Path not found: {project_path}')
        return 1

    output_dir = Path(args.output) if args.output else project_path / 'notes'
    verbose = not args.quiet

    if verbose:
        print('SlideMax - Notes Splitter')
        print('=' * 50)
        print(f'  Project path: {project_path}')
        print(f'  Output dir:   {output_dir}')
        print()

    svg_files = find_svg_files(project_path)
    if not svg_files:
        print('[ERROR] No SVG files were found')
        return 1

    if verbose:
        print(f'  Found {len(svg_files)} SVG file(s)')

    total_md_path = project_path / 'notes' / 'total.md'
    svg_stems = [path.stem for path in svg_files]
    notes = parse_total_md(total_md_path, svg_stems, verbose)
    if not notes:
        print('[ERROR] No notes content was found')
        return 1

    if verbose:
        print(f'  Found {len(notes)} note section(s)')
        print()

    all_match, missing_notes = check_svg_note_mapping(svg_files, notes)
    if not all_match:
        print('[ERROR] SVG files and notes are not fully aligned')
        print(f"  Missing notes: {', '.join(missing_notes)}")
        print('\nPlease regenerate notes/total.md so every SVG has a corresponding section.')
        return 1

    if verbose:
        print('[OK] Every SVG file has a matching note section')
        print()

    success = split_notes(notes, output_dir, verbose)
    if success:
        if verbose:
            print('\n[Done] Notes splitting completed')
        return 0

    print('\n[ERROR] Notes splitting failed')
    return 1


def main() -> None:
    raise SystemExit(run_cli())


__all__ = [
    'HEADING_RE',
    'HR_RE',
    'build_match_maps',
    'build_parser',
    'check_svg_note_mapping',
    'extract_leading_number',
    'find_svg_files',
    'main',
    'match_title',
    'normalize_title',
    'parse_total_md',
    'run_cli',
    'split_notes',
]
