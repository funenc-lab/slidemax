"""Shared project management service for PPT Master."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .config import WORKSPACE_DIR
from .project_utils import (
    CANVAS_FORMATS,
    get_project_info as get_project_info_common,
    normalize_canvas_format,
    validate_project_structure,
    validate_svg_viewbox,
)


@dataclass(frozen=True)
class ProjectInfoSummary:
    """Minimal project info summary for CLI output."""

    name: str
    path: str
    exists: bool
    svg_count: int
    has_spec: bool
    canvas_format: str
    create_date: str

    def as_dict(self) -> Dict[str, object]:
        return {
            'name': self.name,
            'path': self.path,
            'exists': self.exists,
            'svg_count': self.svg_count,
            'has_spec': self.has_spec,
            'canvas_format': self.canvas_format,
            'create_date': self.create_date,
        }


class ProjectManager:
    """Create, validate, and inspect PPT Master projects."""

    CANVAS_FORMATS = CANVAS_FORMATS

    def __init__(self, base_dir: str | Path = WORKSPACE_DIR) -> None:
        self.base_dir = Path(base_dir)

    def init_project(
        self,
        project_name: str,
        canvas_format: str = 'ppt169',
        *,
        base_dir: Optional[str | Path] = None,
    ) -> str:
        """Initialize a new project directory structure."""

        base_path = Path(base_dir) if base_dir else self.base_dir
        normalized_format = normalize_canvas_format(canvas_format)
        if normalized_format not in self.CANVAS_FORMATS:
            available = ', '.join(sorted(self.CANVAS_FORMATS.keys()))
            raise ValueError(
                f"Unsupported canvas format: {canvas_format} "
                f"(available: {available}; common alias: xhs -> xiaohongshu)"
            )

        date_str = datetime.now().strftime('%Y%m%d')
        project_dir_name = f'{project_name}_{normalized_format}_{date_str}'
        project_path = base_path / project_dir_name

        if project_path.exists():
            raise FileExistsError(f'Project directory already exists: {project_path}')

        project_path.mkdir(parents=True, exist_ok=True)
        (project_path / 'svg_output').mkdir(exist_ok=True)
        (project_path / 'svg_final').mkdir(exist_ok=True)
        (project_path / 'images').mkdir(exist_ok=True)
        (project_path / 'notes').mkdir(exist_ok=True)
        (project_path / 'templates').mkdir(exist_ok=True)

        readme_path = project_path / 'README.md'
        readme_path.write_text(
            (
                f'# {project_name}\n\n'
                f'- Canvas format: {normalized_format}\n'
                f'- Created: {date_str}\n\n'
                '## Directories\n\n'
                '- `svg_output/`: raw SVG output\n'
                '- `svg_final/`: finalized SVG output\n'
                '- `images/`: image assets\n'
                '- `notes/`: speaker notes\n'
                '- `templates/`: project-local templates\n'
            ),
            encoding='utf-8',
        )

        canvas_info = self.CANVAS_FORMATS[normalized_format]
        print(f'Project directory created: {project_path}')
        print(f"Canvas format: {canvas_info['name']} ({canvas_info['dimensions']})")
        return str(project_path)

    def validate_project(self, project_path: str | Path) -> Tuple[bool, List[str], List[str]]:
        """Validate a project's structure and SVG viewBox consistency."""

        project_path_obj = Path(project_path)
        is_valid, errors, warnings = validate_project_structure(str(project_path_obj))

        if project_path_obj.exists() and project_path_obj.is_dir():
            info = get_project_info_common(str(project_path_obj))
            if info.get('svg_files'):
                svg_files = [project_path_obj / 'svg_output' / filename for filename in info['svg_files']]
                expected_format = info.get('format')
                if expected_format == 'unknown':
                    expected_format = None
                warnings.extend(validate_svg_viewbox(svg_files, expected_format))

        return is_valid, errors, warnings

    def get_project_info(self, project_path: str | Path) -> Dict[str, object]:
        """Return summarized project metadata."""

        shared = get_project_info_common(str(project_path))
        summary = ProjectInfoSummary(
            name=str(shared.get('name', Path(project_path).name)),
            path=str(shared.get('path', str(project_path))),
            exists=bool(shared.get('exists', False)),
            svg_count=int(shared.get('svg_count', 0)),
            has_spec=bool(shared.get('has_spec', False)),
            canvas_format=str(shared.get('format_name', 'Unknown format')),
            create_date=str(shared.get('date_formatted', 'Unknown date')),
        )
        return summary.as_dict()


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for the project manager."""

    parser = argparse.ArgumentParser(
        description='PPT Master project manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s init my_project --format ppt169
  %(prog)s validate workspace/my_project_ppt169_20260308
  %(prog)s info workspace/my_project_ppt169_20260308
''',
    )
    subparsers = parser.add_subparsers(dest='command')

    init_parser = subparsers.add_parser('init', help='Create a new project')
    init_parser.add_argument('project_name', help='Project name')
    init_parser.add_argument('--format', default='ppt169', dest='canvas_format', help='Canvas format')
    init_parser.add_argument('--dir', default=str(WORKSPACE_DIR), dest='base_dir', help='Base directory')

    validate_parser = subparsers.add_parser('validate', help='Validate an existing project')
    validate_parser.add_argument('project_path', help='Project path')

    info_parser = subparsers.add_parser('info', help='Show project info')
    info_parser.add_argument('project_path', help='Project path')

    return parser


def run_cli(argv: Optional[Sequence[str]] = None) -> int:
    """Execute the CLI entrypoint for project management."""

    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if not args.command:
        parser.print_help()
        return 1

    manager = ProjectManager()

    if args.command == 'init':
        try:
            project_path = manager.init_project(
                args.project_name,
                args.canvas_format,
                base_dir=args.base_dir,
            )
            print(f'[OK] Project created: {project_path}')
            print('\nNext steps:')
            print('1. Create and save the design specification markdown file')
            print('2. Put SVG files into the svg_output/ directory')
            return 0
        except Exception as exc:
            print(f'[ERROR] Creation failed: {exc}')
            return 1

    if args.command == 'validate':
        is_valid, errors, warnings = manager.validate_project(args.project_path)
        print(f'\nProject validation: {args.project_path}')
        print('=' * 60)

        if errors:
            print('\n[ERROR] Errors:')
            for error in errors:
                print(f'  - {error}')

        if warnings:
            print('\n[WARN] Warnings:')
            for warning in warnings:
                print(f'  - {warning}')

        if is_valid and not warnings:
            print('\n[OK] Project structure is complete with no issues')
            return 0
        if is_valid:
            print('\n[OK] Project structure is valid with recommendations')
            return 0

        print('\n[ERROR] Project structure is invalid; please fix the reported errors')
        return 1

    if args.command == 'info':
        info = manager.get_project_info(args.project_path)
        print(f"\nProject info: {info['name']}")
        print('=' * 60)
        print(f"Path: {info['path']}")
        print(f"Exists: {'yes' if info['exists'] else 'no'}")
        print(f"SVG files: {info['svg_count']}")
        print(f"Design spec: {'present' if info['has_spec'] else 'missing'}")
        print(f"Canvas format: {info['canvas_format']}")
        print(f"Created: {info['create_date']}")
        return 0

    print(f"[ERROR] Unknown command: {args.command}")
    return 1


def main() -> None:
    raise SystemExit(run_cli())


__all__ = [
    'ProjectInfoSummary',
    'ProjectManager',
    'build_parser',
    'main',
    'run_cli',
]
