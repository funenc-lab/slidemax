"""Shared batch project validation service for SlideMax."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import DefaultDict, Dict, List, Optional, Sequence

from .config import EXTRA_EXAMPLE_PATHS_ENV, WORKSPACE_DIR, get_example_dirs
from .project_utils import (
    find_all_projects,
    get_project_info,
    validate_project_structure,
    validate_svg_viewbox,
)


class BatchValidator:
    """Validate multiple SlideMax projects and aggregate their results."""

    def __init__(self) -> None:
        self.results: List[Dict[str, object]] = []
        self.summary = {
            'total': 0,
            'valid': 0,
            'has_errors': 0,
            'has_warnings': 0,
            'missing_readme': 0,
            'missing_spec': 0,
            'svg_issues': 0,
        }

    def validate_directory(self, directory: str, recursive: bool = False) -> List[Dict[str, object]]:
        """Validate all detected projects within a directory."""

        del recursive
        dir_path = Path(directory)
        if not dir_path.exists():
            print(f'[ERROR] Directory does not exist: {directory}')
            return []

        print(f'\n[SCAN] Scanning directory: {directory}')
        print('=' * 80)

        if self._looks_like_project_root(dir_path):
            print('[INFO] Detected single project directory\n')
            self.validate_project(str(dir_path))
            return self.results

        projects = find_all_projects(directory)
        if not projects:
            print('[WARN] No projects found')
            return []

        print(f'Found {len(projects)} project(s)\n')
        for project_path in projects:
            self.validate_project(str(project_path))
        return self.results

    def _looks_like_project_root(self, dir_path: Path) -> bool:
        """Return whether the provided directory already looks like a project root."""

        if not dir_path.is_dir():
            return False

        required_paths = [
            dir_path / 'README.md',
            dir_path / 'svg_output',
            dir_path / 'images',
            dir_path / 'notes',
            dir_path / 'templates',
        ]
        return all(path.exists() for path in required_paths)

    def validate_project(self, project_path: str) -> Dict[str, object]:
        """Validate a single SlideMax project."""

        self.summary['total'] += 1
        info = get_project_info(project_path)
        is_valid, errors, warnings = validate_project_structure(project_path)

        svg_warnings: List[str] = []
        if info['svg_files']:
            project_root = Path(project_path)
            svg_files = [project_root / 'svg_output' / filename for filename in info['svg_files']]
            svg_warnings = validate_svg_viewbox(svg_files, info['format'])

        result = {
            'path': project_path,
            'name': info['name'],
            'format': info['format_name'],
            'date': info['date_formatted'],
            'svg_count': info['svg_count'],
            'is_valid': is_valid,
            'errors': errors,
            'warnings': warnings + svg_warnings,
            'has_readme': info['has_readme'],
            'has_spec': info['has_spec'],
        }
        self.results.append(result)

        if is_valid and not warnings and not svg_warnings:
            self.summary['valid'] += 1
            status = '[OK]'
        elif errors:
            self.summary['has_errors'] += 1
            status = '[ERROR]'
        else:
            self.summary['has_warnings'] += 1
            status = '[WARN]'

        if not info['has_readme']:
            self.summary['missing_readme'] += 1
        if not info['has_spec']:
            self.summary['missing_spec'] += 1
        if svg_warnings:
            self.summary['svg_issues'] += 1

        print(f"{status} {info['name']}")
        print(f'   Path: {project_path}')
        print(f"   Format: {info['format_name']} | SVG: {info['svg_count']} file(s) | Date: {info['date_formatted']}")

        if errors:
            print(f"   [ERROR] Errors ({len(errors)}):")
            for error in errors:
                print(f'      - {error}')

        all_warnings = warnings + svg_warnings
        if all_warnings:
            print(f"   [WARN] Warnings ({len(all_warnings)}):")
            for warning in all_warnings[:3]:
                print(f'      - {warning}')
            if len(all_warnings) > 3:
                print(f'      ... and {len(all_warnings) - 3} more warning(s)')

        print()
        return result

    def print_summary(self) -> None:
        """Print the aggregated validation summary."""

        print('\n' + '=' * 80)
        print('[SUMMARY] Validation summary')
        print('=' * 80)

        print(f"\nTotal projects: {self.summary['total']}")
        print(f"  [OK] Passed cleanly: {self.summary['valid']} ({self._percentage(self.summary['valid'])}%)")
        print(f"  [WARN] With warnings: {self.summary['has_warnings']} ({self._percentage(self.summary['has_warnings'])}%)")
        print(f"  [ERROR] With errors: {self.summary['has_errors']} ({self._percentage(self.summary['has_errors'])}%)")

        print('\nCommon issues:')
        print(f"  Missing README.md: {self.summary['missing_readme']} project(s)")
        print(f"  Missing design spec: {self.summary['missing_spec']} project(s)")
        print(f"  SVG format issues: {self.summary['svg_issues']} project(s)")

        format_stats: DefaultDict[str, int] = defaultdict(int)
        for result in self.results:
            format_stats[str(result['format'])] += 1

        if format_stats:
            print('\nCanvas format distribution:')
            for canvas_format, count in sorted(format_stats.items(), key=lambda item: item[1], reverse=True):
                print(f'  {canvas_format}: {count} project(s)')

        if self.summary['has_errors'] > 0 or self.summary['has_warnings'] > 0:
            print('\n[TIP] Suggested fixes:')
            if self.summary['missing_readme'] > 0:
                print('  1. Add README.md files for incomplete projects')
                print('     Reference: skills/slidemax_workflow/examples/ppt169_谷歌风_google_annual_report/README.md')
            if self.summary['svg_issues'] > 0:
                print('  2. Check SVG viewBox settings and align them with the canvas format')
            if self.summary['missing_spec'] > 0:
                print('  3. Add the design specification file')
                print('     Recommended name: design_specification.md or the workflow default spec filename')

    def _percentage(self, count: int) -> int:
        if self.summary['total'] == 0:
            return 0
        return int(count / self.summary['total'] * 100)

    def export_report(self, output_file: str = 'validation_report.txt') -> None:
        """Export the validation report to a text file."""

        output_path = Path(output_file)
        with output_path.open('w', encoding='utf-8') as handle:
            handle.write('SlideMax Project Validation Report\n')
            handle.write('=' * 80 + '\n\n')

            for result in self.results:
                if result['is_valid'] and not result['warnings']:
                    status = '[OK] Passed'
                elif result['errors']:
                    status = '[ERROR] Errors'
                else:
                    status = '[WARN] Warnings'

                handle.write(f"{status} - {result['name']}\n")
                handle.write(f"Path: {result['path']}\n")
                handle.write(f"Format: {result['format']} | SVG: {result['svg_count']} file(s)\n")

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
            handle.write(f"Total projects: {self.summary['total']}\n")
            handle.write(f"Passed cleanly: {self.summary['valid']}\n")
            handle.write(f"With warnings: {self.summary['has_warnings']}\n")
            handle.write(f"With errors: {self.summary['has_errors']}\n")

        print(f'\n[REPORT] Validation report exported: {output_path}')


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for batch project validation."""

    parser = argparse.ArgumentParser(
        description='SlideMax batch project validator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s skills/slidemax_workflow/examples
  %(prog)s skills/slidemax_workflow/examples workspace
  %(prog)s --all
  %(prog)s skills/slidemax_workflow/examples --export --output validation_report.txt
''',
    )
    parser.add_argument('directories', nargs='*', help='Project root directories to scan')
    parser.add_argument('--all', action='store_true', help='Validate default examples, extra example roots, and workspace')
    parser.add_argument('--export', action='store_true', help='Export the validation report to a text file')
    parser.add_argument('--output', default='validation_report.txt', help='Output report file path')
    return parser


def resolve_directories(args: argparse.Namespace) -> List[str]:
    """Resolve the directory list from CLI arguments while preserving legacy behavior."""

    if args.all:
        directories = [str(path) for path in get_example_dirs()] + [str(WORKSPACE_DIR)]
        extra_example_dirs = get_example_dirs(include_default=False)
        if extra_example_dirs:
            print(f'[INFO] Extra example roots from {EXTRA_EXAMPLE_PATHS_ENV}:')
            for path in extra_example_dirs:
                print(f'  - {path}')
            print()
    else:
        directories = list(args.directories)

    seen: set[str] = set()
    unique_directories: List[str] = []
    for directory in directories:
        if directory in seen:
            continue
        seen.add(directory)
        unique_directories.append(directory)
    return unique_directories


def run_cli(argv: Optional[Sequence[str]] = None) -> int:
    """Execute the batch validation CLI entrypoint."""

    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if not args.directories and not args.all:
        parser.print_help()
        return 0

    validator = BatchValidator()
    directories = resolve_directories(args)

    for directory in directories:
        if Path(directory).exists():
            validator.validate_directory(directory)
        else:
            print(f'[WARN] Skipping missing directory: {directory}\n')

    validator.print_summary()
    if args.export:
        validator.export_report(args.output)

    if validator.summary['has_errors'] > 0:
        return 1
    if validator.summary['has_warnings'] > 0:
        return 2
    return 0


def main() -> None:
    raise SystemExit(run_cli())


__all__ = [
    'BatchValidator',
    'build_parser',
    'main',
    'resolve_directories',
    'run_cli',
]
