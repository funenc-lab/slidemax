from __future__ import annotations

import os
import shlex
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from slidemax.config import EXTRA_EXAMPLE_PATHS_ENV, PROJECT_ROOT, SKILL_ROOT, get_example_dirs
from slidemax.project_utils import CANVAS_FORMATS, find_all_projects, get_project_info

CANONICAL_COMMANDS_DIR = (PROJECT_ROOT / 'skills' / 'slidemax_workflow' / 'commands').resolve()
SKILL_RESOURCES = [
    ('Workflow rules', Path('AGENTS.md')),
    ('Docs index', Path('docs/README.md')),
    ('Workflow tutorial', Path('docs/workflow_tutorial.md')),
    ('Design guidelines', Path('docs/design_guidelines.md')),
    ('Canvas formats', Path('docs/canvas_formats.md')),
    ('Roles', Path('roles/README.md')),
    ('Chart templates', Path('templates/charts/README.md')),
]
FORMAT_ORDER = ['ppt169', 'ppt43', 'wechat', 'xiaohongshu', 'moments', 'story', 'banner', 'a4']


@dataclass(frozen=True)
class ExamplesRenderContext:
    command_reference: str
    project_manager_command: str
    validate_command: str
    update_command: str
    resource_lines: List[str]
    resource_note: Optional[str]
    inside_repo: bool


@dataclass(frozen=True)
class ExamplesIndexResult:
    examples_path: Path
    content: str
    project_count: int
    total_svg_count: int


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def relative_link(base_dir: Path, target: Path) -> str:
    return Path(os.path.relpath(target, base_dir)).as_posix()


def shell_command(python_file: Path, *args: str, base_dir: Optional[Path] = None) -> str:
    command_target = python_file
    if base_dir is not None:
        command_target = Path(relative_link(base_dir, python_file))

    parts = ['python3', shlex.quote(command_target.as_posix())]
    parts.extend(shlex.quote(arg) for arg in args)
    return ' '.join(parts)


def build_render_context(examples_path: Path) -> ExamplesRenderContext:
    resolved_examples_path = examples_path.resolve()
    resolved_project_root = PROJECT_ROOT.resolve()
    inside_repo = is_relative_to(resolved_examples_path, resolved_project_root)

    generator_path = CANONICAL_COMMANDS_DIR / 'generate_examples_index.py'
    project_manager_path = CANONICAL_COMMANDS_DIR / 'project_manager.py'

    if inside_repo:
        command_reference = relative_link(resolved_examples_path, generator_path)
        project_manager_command = shell_command(
            project_manager_path,
            'init',
            'my_project',
            '--format',
            'ppt169',
            base_dir=resolved_examples_path,
        )
        validate_command = shell_command(
            project_manager_path,
            'validate',
            './<project>',
            base_dir=resolved_examples_path,
        )
        update_command = shell_command(generator_path, base_dir=resolved_examples_path)
        resource_lines = [
            f"- [{label}]({relative_link(resolved_examples_path, SKILL_ROOT.resolve() / target)})"
            for label, target in SKILL_RESOURCES
        ]
        resource_note = None
    else:
        command_reference = str(generator_path)
        project_manager_command = shell_command(
            project_manager_path,
            'init',
            'my_project',
            '--format',
            'ppt169',
        )
        validate_command = shell_command(project_manager_path, 'validate', './<project>')
        update_command = shell_command(generator_path, str(resolved_examples_path))
        resource_lines = [
            f"- {label}: `{(SKILL_ROOT.resolve() / target).resolve()}`"
            for label, target in SKILL_RESOURCES
        ]
        resource_note = (
            '> This examples root is outside the repository, so canonical repository paths '
            'are shown below.\n'
        )

    return ExamplesRenderContext(
        command_reference=command_reference,
        project_manager_command=project_manager_command,
        validate_command=validate_command,
        update_command=update_command,
        resource_lines=resource_lines,
        resource_note=resource_note,
        inside_repo=inside_repo,
    )


def collect_projects(examples_path: Path) -> List[Dict[str, Any]]:
    projects = find_all_projects(str(examples_path))
    projects_info = [get_project_info(str(project_path)) for project_path in projects]
    projects_info.sort(key=lambda item: item['date'], reverse=True)
    return projects_info


def group_projects_by_format(projects_info: Iterable[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for info in projects_info:
        grouped[info['format']].append(info)
    return grouped


def build_examples_index(examples_path: Path, now: Optional[datetime] = None) -> ExamplesIndexResult:
    examples_path = examples_path.expanduser()
    if not examples_path.exists():
        raise FileNotFoundError(f'Examples directory does not exist: {examples_path}')

    now = now or datetime.now()
    context = build_render_context(examples_path)
    projects_info = collect_projects(examples_path)
    if not projects_info:
        raise ValueError(f'No valid projects found under: {examples_path}')

    by_format = group_projects_by_format(projects_info)
    total_svg_count = sum(info['svg_count'] for info in projects_info)

    content: List[str] = []
    content.append('# SlideMax Example Index\n')
    content.append(f"> This file is generated automatically by `{context.command_reference}`\n")
    content.append(f"> Last updated: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")

    content.append('## Overview\n')
    content.append(f'- **Projects**: {len(projects_info)}')
    content.append(f'- **Canvas formats**: {len(by_format)}')
    content.append(f'- **SVG files**: {total_svg_count}')

    content.append('\n### Format distribution\n')
    for fmt_key in sorted(by_format.keys(), key=lambda key: len(by_format[key]), reverse=True):
        count = len(by_format[fmt_key])
        fmt_name = CANVAS_FORMATS.get(fmt_key, {}).get('name', fmt_key)
        content.append(f'- **{fmt_name}**: {count} projects')

    content.append('\n## Recently Updated\n')
    for info in projects_info[:5]:
        content.append(f"- **{info['name']}** ({info['format_name']}) - {info['date_formatted']}")

    content.append('\n## Project List\n')
    for fmt_key in FORMAT_ORDER:
        if fmt_key not in by_format:
            continue

        fmt_info = CANVAS_FORMATS.get(fmt_key, {})
        fmt_name = fmt_info.get('name', fmt_key)
        dimensions = fmt_info.get('dimensions', '')
        content.append(f'\n### {fmt_name} ({dimensions})\n')

        projects_list = sorted(by_format[fmt_key], key=lambda item: item['date'], reverse=True)
        for info in projects_list:
            project_link = f"./{info['dir_name']}"
            line = f"- **[{info['name']}]({project_link})**"
            line += f" - {info['date_formatted']}"
            line += f" - {info['svg_count']} slides"
            content.append(line)

    other_formats = set(by_format.keys()) - set(FORMAT_ORDER)
    if other_formats:
        content.append('\n### Other formats\n')
        for fmt_key in sorted(other_formats):
            for info in sorted(by_format[fmt_key], key=lambda item: item['date'], reverse=True):
                project_link = f"./{info['dir_name']}"
                line = f"- **[{info['name']}]({project_link})**"
                line += f" ({info['format_name']}) - {info['date_formatted']}"
                line += f" - {info['svg_count']} slides"
                content.append(line)

    content.append('\n## Usage\n')
    content.append('### Preview a project\n')
    content.append('Each example project usually contains:\n')
    content.append('- `README.md` - project overview')
    content.append('- `Design specification` markdown')
    content.append('- `svg_output/` - raw SVG output\n')

    content.append('**Method 1: HTTP server (recommended)**\n')
    content.append('```bash')
    content.append('python3 -m http.server --directory ./<project_name>/svg_output 8000')
    content.append('# Open http://localhost:8000')
    content.append('```\n')

    content.append('**Method 2: Open an SVG directly**\n')
    content.append('```bash')
    content.append('open ./<project_name>/svg_output/slide_01_cover.svg')
    content.append('```\n')

    content.append('### Create a new project\n')
    content.append('Follow the structure of an existing project, or use the project manager command:\n')
    content.append('```bash')
    content.append(context.project_manager_command)
    content.append('```\n')

    content.append('## Contribution\n')
    content.append('Contributions are welcome in this examples root.\n')
    content.append('### Project requirements\n')
    content.append('1. Follow the standard project structure')
    content.append('2. Include a complete `README.md` and design specification')
    content.append('3. Keep SVG files aligned with the technical constraints')
    content.append('4. Use the directory format `{project_name}_{format}_{YYYYMMDD}`\n')

    content.append('### Workflow\n')
    if context.inside_repo:
        content.append('1. Create the project inside the current examples root')
    else:
        content.append('1. Create the project inside this external examples root')
    content.append(f'2. Validate the project: `{context.validate_command}`')
    content.append(f'3. Refresh the index: `{context.update_command}`')
    content.append('4. Submit the change for review\n')

    content.append('## Related Resources\n')
    if context.resource_note:
        content.append(context.resource_note.rstrip())
    content.extend(context.resource_lines)
    content.append('')
    content.append('---\n')
    content.append(f'*Generated on {now.strftime("%Y-%m-%d %H:%M:%S")} by SlideMax*')

    return ExamplesIndexResult(
        examples_path=examples_path,
        content='\n'.join(content),
        project_count=len(projects_info),
        total_svg_count=total_svg_count,
    )


def generate_examples_index(examples_dir: str = 'examples') -> str:
    return build_examples_index(Path(examples_dir)).content


def resolve_target_dirs(argv: Sequence[str]) -> List[Path]:
    target_dirs = [Path(arg) for arg in argv if not arg.startswith('--')]
    if target_dirs:
        return target_dirs
    return get_example_dirs()


def run_cli(argv: Optional[Sequence[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    target_dirs = resolve_target_dirs(argv)
    extra_example_dirs = get_example_dirs(include_default=False)

    print('=' * 80)
    print('SlideMax - Examples index generator')
    print('=' * 80 + '\n')

    if extra_example_dirs and not argv:
        print(f'[INFO] Extra example roots from {EXTRA_EXAMPLE_PATHS_ENV}:')
        for path in extra_example_dirs:
            print(f'  - {path}')
        print()

    generated_count = 0
    for examples_path in target_dirs:
        try:
            print(f'[SCAN] Scanning directory: {examples_path}')
            result = build_examples_index(Path(examples_path))
        except (FileNotFoundError, ValueError) as exc:
            print(f'\n[ERROR] {exc}')
            continue

        output_file = Path(examples_path) / 'README.md'
        try:
            output_file.write_text(result.content, encoding='utf-8')
            print(f'\n[OK] Index file generated: {output_file}')
            print(f'   Lines: {len(result.content.splitlines())}')
            print(f'   Projects indexed: {result.project_count}')
            generated_count += 1
        except OSError as exc:
            print(f'\n[ERROR] Failed to write README: {exc}')

    return 0 if generated_count else 1


def main() -> None:
    raise SystemExit(run_cli())


__all__ = [
    'CANONICAL_COMMANDS_DIR',
    'SKILL_RESOURCES',
    'FORMAT_ORDER',
    'ExamplesRenderContext',
    'ExamplesIndexResult',
    'build_examples_index',
    'build_render_context',
    'collect_projects',
    'generate_examples_index',
    'group_projects_by_format',
    'is_relative_to',
    'main',
    'relative_link',
    'resolve_target_dirs',
    'run_cli',
    'shell_command',
]
