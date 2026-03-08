"""Shared SVG quality validation service for PPT Master."""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path
from typing import DefaultDict, Dict, List, Optional, Sequence

from .config import EXTRA_EXAMPLE_PATHS_ENV, get_example_dirs
from .project_utils import CANVAS_FORMATS, find_all_projects
from .svg_rules import (
    RECOMMENDED_SYSTEM_FONTS,
    get_compound_detection_specs,
    get_regex_detection_specs,
    get_substring_detection_specs,
)


SUBSTRING_FORBIDDEN_SPECS = get_substring_detection_specs()
REGEX_FORBIDDEN_SPECS = get_regex_detection_specs()
COMPOUND_FORBIDDEN_SPECS = get_compound_detection_specs()

FORBIDDEN_RULES = [(spec.marker, spec.error_message) for spec in SUBSTRING_FORBIDDEN_SPECS]
REGEX_FORBIDDEN_RULES = [(spec.pattern, spec.error_message) for spec in REGEX_FORBIDDEN_SPECS]

DEFS_BLOCK_RE = re.compile(r'<defs\b[^>]*>.*?</defs>', re.IGNORECASE | re.DOTALL)
ID_ATTRIBUTE_RE = re.compile(r'\bid\s*=\s*("[^"]*"|\'[^\']*\')')


class SVGQualityChecker:
    """Validate SVG files against PPT Master compatibility rules."""

    def __init__(self) -> None:
        self.results: List[Dict[str, object]] = []
        self.summary = {'total': 0, 'passed': 0, 'warnings': 0, 'errors': 0}
        self.issue_types: DefaultDict[str, int] = defaultdict(int)

    def check_file(self, svg_file: str, expected_format: Optional[str] = None) -> Dict[str, object]:
        """Check a single SVG file and return its validation result."""

        svg_path = Path(svg_file)
        if not svg_path.exists():
            result: Dict[str, object] = {
                'file': str(svg_file),
                'exists': False,
                'errors': ['File does not exist.'],
                'warnings': [],
                'passed': False,
            }
            self._record_result(result)
            return result

        result = {
            'file': svg_path.name,
            'path': str(svg_path),
            'exists': True,
            'errors': [],
            'warnings': [],
            'info': {},
            'passed': True,
        }

        try:
            content = svg_path.read_text(encoding='utf-8')
            self._check_viewbox(content, result, expected_format)
            self._check_forbidden_elements(content, result)
            self._check_fonts(content, result)
            self._check_dimensions(content, result)
            self._check_text_elements(content, result)
            result['passed'] = len(result['errors']) == 0
        except Exception as exc:
            result['errors'].append(f'Failed to read file: {exc}')
            result['passed'] = False

        self._record_result(result)
        return result

    def _record_result(self, result: Dict[str, object]) -> None:
        self.summary['total'] += 1
        if result['passed']:
            if result['warnings']:
                self.summary['warnings'] += 1
            else:
                self.summary['passed'] += 1
        else:
            self.summary['errors'] += 1

        for error in result['errors']:
            self.issue_types[self._categorize_issue(str(error))] += 1

        self.results.append(result)

    def _check_viewbox(
        self,
        content: str,
        result: Dict[str, object],
        expected_format: Optional[str] = None,
    ) -> None:
        viewbox_match = re.search(r'viewBox="([^"]+)"', content)
        if not viewbox_match:
            result['errors'].append('Missing viewBox attribute.')
            return

        viewbox = viewbox_match.group(1)
        result['info']['viewbox'] = viewbox

        if not re.match(r'0 0 \d+ \d+', viewbox):
            result['warnings'].append(f'Unexpected viewBox format: {viewbox}')

        if expected_format and expected_format in CANVAS_FORMATS:
            expected_viewbox = CANVAS_FORMATS[expected_format]['viewbox']
            if viewbox != expected_viewbox:
                result['errors'].append(
                    f"viewBox mismatch: expected '{expected_viewbox}', got '{viewbox}'"
                )

    def _check_forbidden_elements(self, content: str, result: Dict[str, object]) -> None:
        content_lower = content.lower()

        for spec in SUBSTRING_FORBIDDEN_SPECS:
            if spec.marker in content_lower:
                result['errors'].append(spec.error_message)

        for spec in COMPOUND_FORBIDDEN_SPECS:
            has_required_markers = all(marker in content_lower for marker in spec.markers)
            has_required_patterns = all(re.search(pattern, content_lower) is not None for pattern in spec.regex_patterns)
            if has_required_markers and has_required_patterns:
                result['errors'].append(spec.error_message)

        for spec in REGEX_FORBIDDEN_SPECS:
            haystack = content_lower if spec.search_in_lowercase else content
            if spec.error_code == 'id_attribute_detected':
                haystack = self._strip_safe_defs_ids(haystack)
            if re.search(spec.pattern, haystack):
                result['errors'].append(spec.error_message)

    def _strip_safe_defs_ids(self, content: str) -> str:
        """Ignore id attributes inside defs blocks while keeping other rule checks intact."""

        def _replace_defs(match: re.Match[str]) -> str:
            block = match.group(0)
            return ID_ATTRIBUTE_RE.sub('', block)

        return DEFS_BLOCK_RE.sub(_replace_defs, content)

    def _check_fonts(self, content: str, result: Dict[str, object]) -> None:
        font_matches = re.findall(r'font-family[:\s]*["\']([^"\']+)["\']', content, re.IGNORECASE)
        if not font_matches:
            return

        result['info']['fonts'] = sorted(set(font_matches))
        for font_family in font_matches:
            has_recommended = any(font in font_family for font in RECOMMENDED_SYSTEM_FONTS)
            if not has_recommended:
                result['warnings'].append(f'Recommended system UI font stack not found: {font_family}')
                break

    def _check_dimensions(self, content: str, result: Dict[str, object]) -> None:
        width_match = re.search(r'width="(\d+)"', content)
        height_match = re.search(r'height="(\d+)"', content)
        if not width_match or not height_match:
            return

        width = width_match.group(1)
        height = height_match.group(1)
        result['info']['dimensions'] = f'{width}×{height}'

        if 'viewbox' not in result['info']:
            return

        viewbox_parts = str(result['info']['viewbox']).split()
        if len(viewbox_parts) != 4:
            return

        viewbox_width, viewbox_height = viewbox_parts[2], viewbox_parts[3]
        if width != viewbox_width or height != viewbox_height:
            result['warnings'].append(
                f'width/height ({width}×{height}) does not match viewBox ({viewbox_width}×{viewbox_height})'
            )

    def _check_text_elements(self, content: str, result: Dict[str, object]) -> None:
        text_count = content.count('<text')
        tspan_count = content.count('<tspan')
        result['info']['text_elements'] = text_count
        result['info']['tspan_elements'] = tspan_count

        text_matches = re.findall(r'<text[^>]*>([^<]{100,})</text>', content)
        if text_matches:
            result['warnings'].append(
                f'Detected {len(text_matches)} potentially long single-line text element(s); consider using tspan wrapping.'
            )

    def _categorize_issue(self, error_message: str) -> str:
        if 'viewBox' in error_message:
            return 'viewBox issues'
        if 'foreignObject' in error_message:
            return 'foreignObject'
        if 'font' in error_message.lower():
            return 'font issues'
        if 'opacity' in error_message.lower():
            return 'opacity issues'
        return 'other'

    def check_directory(self, directory: str, expected_format: Optional[str] = None) -> List[Dict[str, object]]:
        """Check all SVG files under a file path, svg_output directory, or raw SVG directory."""

        dir_path = Path(directory)
        if not dir_path.exists():
            print(f'[ERROR] Directory does not exist: {directory}')
            return []

        if dir_path.is_file():
            svg_files = [dir_path]
        else:
            svg_output = dir_path / 'svg_output' if (dir_path / 'svg_output').exists() else dir_path
            svg_files = sorted(svg_output.glob('*.svg'))

        if not svg_files:
            print('[WARN] No SVG files found')
            return []

        print(f'\n[SCAN] Checking {len(svg_files)} SVG file(s)...\n')
        for svg_file in svg_files:
            result = self.check_file(str(svg_file), expected_format)
            self._print_result(result)
        return self.results

    def _print_result(self, result: Dict[str, object]) -> None:
        if result['passed']:
            if result['warnings']:
                icon, status = '[WARN]', 'passed with warnings'
            else:
                icon, status = '[OK]', 'passed'
        else:
            icon, status = '[ERROR]', 'failed'

        print(f"{icon} {result['file']} - {status}")

        info = result.get('info', {})
        if info:
            info_items: List[str] = []
            if 'viewbox' in info:
                info_items.append(f"viewBox: {info['viewbox']}")
            if info_items:
                print(f"   {' | '.join(info_items)}")

        for error in result['errors']:
            print(f'   [ERROR] {error}')

        warnings = list(result['warnings'])
        for warning in warnings[:2]:
            print(f'   [WARN] {warning}')
        if len(warnings) > 2:
            print(f'   ... and {len(warnings) - 2} more warning(s)')
        print()

    def print_summary(self) -> None:
        print('=' * 80)
        print('[SUMMARY] Validation summary')
        print('=' * 80)
        print(f"\nTotal files: {self.summary['total']}")
        print(f"  [OK] Passed cleanly: {self.summary['passed']} ({self._percentage(self.summary['passed'])}%)")
        print(f"  [WARN] Passed with warnings: {self.summary['warnings']} ({self._percentage(self.summary['warnings'])}%)")
        print(f"  [ERROR] Failed: {self.summary['errors']} ({self._percentage(self.summary['errors'])}%)")

        if self.issue_types:
            print('\nIssue categories:')
            for issue_type, count in sorted(self.issue_types.items(), key=lambda item: item[1], reverse=True):
                print(f'  {issue_type}: {count}')

        if self.summary['errors'] > 0 or self.summary['warnings'] > 0:
            print('\n[TIP] Common fixes:')
            print('  1. viewBox issues: keep it aligned with docs/canvas_formats.md')
            print('  2. foreignObject: replace with <text> + <tspan> manual wrapping')
            print('  3. font issues: use a system UI font stack')

    def _percentage(self, count: int) -> int:
        if self.summary['total'] == 0:
            return 0
        return int(count / self.summary['total'] * 100)

    def export_report(self, output_file: str = 'svg_quality_report.txt') -> None:
        output_path = Path(output_file)
        with output_path.open('w', encoding='utf-8') as handle:
            handle.write('PPT Master SVG Quality Report\n')
            handle.write('=' * 80 + '\n\n')

            for result in self.results:
                status = '[OK] Passed' if result['passed'] else '[ERROR] Failed'
                handle.write(f"{status} - {result['file']}\n")
                handle.write(f"Path: {result.get('path', 'N/A')}\n")

                if result['info']:
                    handle.write(f"Info: {result['info']}\n")
                if result['errors']:
                    handle.write('\nErrors:\n')
                    for error in result['errors']:
                        handle.write(f'  - {error}\n')
                if result['warnings']:
                    handle.write('\nWarnings:\n')
                    for warning in result['warnings']:
                        handle.write(f'  - {warning}\n')
                handle.write('\n' + '-' * 80 + '\n\n')

            handle.write('\n' + '=' * 80 + '\n')
            handle.write('Summary\n')
            handle.write('=' * 80 + '\n\n')
            handle.write(f"Total files: {self.summary['total']}\n")
            handle.write(f"Passed cleanly: {self.summary['passed']}\n")
            handle.write(f"Passed with warnings: {self.summary['warnings']}\n")
            handle.write(f"Failed: {self.summary['errors']}\n")

        print(f'\n[REPORT] Report exported to: {output_path}')


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for the SVG quality checker."""

    parser = argparse.ArgumentParser(
        description='PPT Master SVG quality checker',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s path/to/slide.svg
  %(prog)s path/to/svg_output
  %(prog)s path/to/project --format ppt169
  %(prog)s --all skills/ppt_master_workflow/examples
  %(prog)s path/to/project --export --output svg_quality_report.txt
''',
    )
    parser.add_argument('target', nargs='?', help='SVG file, SVG directory, or project directory')
    parser.add_argument('--all', action='store_true', help='Check all detected example projects')
    parser.add_argument('--format', dest='expected_format', help='Expected canvas format, such as ppt169')
    parser.add_argument('--export', action='store_true', help='Export the report to a text file')
    parser.add_argument('--output', default='svg_quality_report.txt', help='Output report file path')
    return parser


def _run_all_projects(checker: SVGQualityChecker, target: Optional[str]) -> None:
    if target:
        base_dirs = [Path(target)]
    else:
        base_dirs = get_example_dirs()
        extra_example_dirs = get_example_dirs(include_default=False)
        if extra_example_dirs:
            print(f'[INFO] Extra example roots from {EXTRA_EXAMPLE_PATHS_ENV}:')
            for path in extra_example_dirs:
                print(f'  - {path}')
            print()

    for base_dir in base_dirs:
        projects = find_all_projects(str(base_dir))
        for project in projects:
            print(f"\n{'=' * 80}")
            print(f'Checking project: {project.name}')
            print('=' * 80)
            checker.check_directory(str(project))


def run_cli(argv: Optional[Sequence[str]] = None) -> int:
    """Execute the CLI entrypoint."""

    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if not args.target and not args.all:
        parser.print_help()
        return 0

    checker = SVGQualityChecker()
    if args.all:
        _run_all_projects(checker, args.target)
    else:
        checker.check_directory(args.target, args.expected_format)

    checker.print_summary()
    if args.export:
        checker.export_report(args.output)
    return 1 if checker.summary['errors'] > 0 else 0


def main() -> None:
    raise SystemExit(run_cli())


__all__ = [
    'FORBIDDEN_RULES',
    'REGEX_FORBIDDEN_RULES',
    'RECOMMENDED_SYSTEM_FONTS',
    'SVGQualityChecker',
    'build_parser',
    'main',
    'run_cli',
]
