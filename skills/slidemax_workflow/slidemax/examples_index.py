from __future__ import annotations

import argparse
import os
import re
import shlex
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from .config import EXTRA_EXAMPLE_PATHS_ENV, PROJECT_ROOT, SKILL_ROOT, get_example_dirs
from .project_management import ProjectManager
from .project_utils import CANVAS_FORMATS, find_all_projects, get_project_info
from .svg_quality import SVGTargetSummary, summarize_svg_target

CANONICAL_CLI = (PROJECT_ROOT / 'skills' / 'slidemax_workflow' / 'scripts' / 'slidemax.py').resolve()
SKILL_RESOURCES = [
    ('Workflow rules', Path('AGENTS.md')),
    ('Design guidelines', Path('references/docs/design_guidelines.md')),
    ('Canvas formats', Path('references/docs/canvas_formats.md')),
    ('Image prompt guidance', Path('references/docs/image_prompt_guidance.md')),
    ('Roles', Path('roles/AGENTS.md')),
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


@dataclass(frozen=True)
class ExampleTrustAssessment:
    """Trust status for a bundled example project."""

    tier: str
    reason_summary: str
    delivery_errors: List[str]
    delivery_warnings: List[str]
    svg_summary: SVGTargetSummary

    @property
    def is_curated(self) -> bool:
        return self.tier == 'curated'


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='python3 skills/slidemax_workflow/scripts/slidemax.py generate_examples_index',
        description='Regenerate README indexes for one or more examples roots.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
When to use:
  - Refresh examples indexes after adding, removing, or updating bundled example projects
  - Run without arguments to refresh the built-in examples roots discovered by the shared config

Examples:
  %(prog)s
  %(prog)s skills/slidemax_workflow/examples
  %(prog)s skills/slidemax_workflow/examples /tmp/custom_examples
''',
    )
    parser.add_argument(
        'examples_dirs',
        nargs='*',
        help='Examples root directories to refresh. Defaults to the configured built-in roots.',
    )
    return parser


def build_render_context(examples_path: Path) -> ExamplesRenderContext:
    resolved_examples_path = examples_path.resolve()
    resolved_project_root = PROJECT_ROOT.resolve()
    inside_repo = is_relative_to(resolved_examples_path, resolved_project_root)

    cli_path = CANONICAL_CLI

    if inside_repo:
        command_reference = relative_link(resolved_examples_path, cli_path)
        project_manager_command = shell_command(
            cli_path,
            'project_manager',
            'init',
            'my_project',
            '--format',
            'ppt169',
            base_dir=resolved_examples_path,
        )
        validate_command = shell_command(
            cli_path,
            'project_manager',
            'validate',
            './<project>',
            base_dir=resolved_examples_path,
        )
        update_command = shell_command(cli_path, 'generate_examples_index', base_dir=resolved_examples_path)
        resource_lines = [
            f"- [{label}]({relative_link(resolved_examples_path, SKILL_ROOT.resolve() / target)})"
            for label, target in SKILL_RESOURCES
        ]
        resource_note = None
    else:
        command_reference = str(cli_path)
        project_manager_command = shell_command(
            cli_path,
            'project_manager',
            'init',
            'my_project',
            '--format',
            'ppt169',
        )
        validate_command = shell_command(cli_path, 'project_manager', 'validate', './<project>')
        update_command = shell_command(cli_path, 'generate_examples_index', str(resolved_examples_path))
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
    projects_info.sort(key=project_sort_key)
    return projects_info


def group_projects_by_format(projects_info: Iterable[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for info in projects_info:
        grouped[info['format']].append(info)
    return grouped


def project_sort_key(info: Dict[str, Any]) -> tuple[int, int, str]:
    """Sort dated projects first and push unknown dates to the end."""

    raw_date = str(info.get('date') or '')
    project_name = str(info.get('dir_name') or info.get('name') or '')
    if re.fullmatch(r'\d{8}', raw_date):
        return (0, -int(raw_date), project_name.casefold())
    return (1, 0, project_name.casefold())


def _count_csv_items(raw_text: str) -> int:
    return len([item.strip() for item in raw_text.split(',') if item.strip()])


def summarize_delivery_errors(delivery_errors: Sequence[str]) -> List[str]:
    """Convert detailed validation errors into concise English summaries."""

    summaries: List[str] = []
    seen: set[str] = set()

    for message in delivery_errors:
        summary = ''
        if 'README.md' in message:
            summary = 'missing README.md.'
        elif message.startswith('Missing speaker notes for slide(s): '):
            slide_block = message.split(':', 1)[1].split('. Generate', 1)[0].strip()
            summary = f'missing speaker notes for {_count_csv_items(slide_block)} slide(s).'
        elif message.startswith('Speaker notes are only present in notes/total.md'):
            summary = 'notes are not split into per-slide files.'
        elif message.startswith('Missing finalized SVG file(s) under svg_final/: '):
            file_block = message.split(':', 1)[1].strip()
            summary = f'missing finalized SVG files for {_count_csv_items(file_block)} slide(s).'
        elif message.startswith('Missing exported PPTX file'):
            summary = 'missing exported PPTX.'
        elif message.startswith('No SVG slides were found under svg_output/'):
            summary = 'no slide SVG output found.'
        elif message.startswith('Stage ') and 'notes_split' in message:
            summary = 'notes_split is behind the exported assets.'
        elif message.startswith('Stage ') and 'finalized' in message:
            summary = 'finalized SVG assets are behind the exported PPTX.'
        else:
            summary = re.sub(r'\s+', ' ', message).strip()
            if summary and not summary.endswith('.'):
                summary += '.'

        if summary and summary not in seen:
            seen.add(summary)
            summaries.append(summary)

    return summaries


def assess_example_project(
    project_path: Path,
    *,
    project_manager: Optional[ProjectManager] = None,
    project_info: Optional[Dict[str, Any]] = None,
) -> ExampleTrustAssessment:
    """Assess whether a bundled example is safe to use as a canonical reference."""

    manager = project_manager or ProjectManager(base_dir=project_path.parent)
    info = project_info or get_project_info(str(project_path))
    expected_format = str(info.get('format') or '')
    if expected_format == 'unknown':
        expected_format = None

    delivery_ok, delivery_errors, delivery_warnings = manager.validate_project(project_path)
    svg_summary = summarize_svg_target(
        project_path,
        expected_format=expected_format,
        prefer_finalized=True,
    )

    reason_parts = summarize_delivery_errors(delivery_errors)
    if svg_summary.total == 0:
        reason_parts.append('svg_final is missing or empty.')
    elif svg_summary.errors > 0:
        reason_parts.append(f'svg_final compatibility errors: {svg_summary.errors}.')

    if delivery_ok and svg_summary.is_compatible:
        svg_quality_label = 'svg_final clean.' if svg_summary.is_clean else (
            f'svg_final passes compatibility with {svg_summary.warnings} warning(s).'
        )
        return ExampleTrustAssessment(
            tier='curated',
            reason_summary=f'passes delivery validation; {svg_quality_label}',
            delivery_errors=delivery_errors,
            delivery_warnings=delivery_warnings,
            svg_summary=svg_summary,
        )

    if not reason_parts:
        reason_parts.append('delivery validation is incomplete.')

    return ExampleTrustAssessment(
        tier='preview-only',
        reason_summary=' '.join(reason_parts).strip(),
        delivery_errors=delivery_errors,
        delivery_warnings=delivery_warnings,
        svg_summary=svg_summary,
    )


def build_examples_index(examples_path: Path, now: Optional[datetime] = None) -> ExamplesIndexResult:
    examples_path = examples_path.expanduser()
    if not examples_path.exists():
        raise FileNotFoundError(f'Examples directory does not exist: {examples_path}')

    now = now or datetime.now()
    context = build_render_context(examples_path)
    projects_info = collect_projects(examples_path)
    if not projects_info:
        raise ValueError(f'No valid projects found under: {examples_path}')

    project_manager = ProjectManager(base_dir=examples_path)
    project_entries: List[Dict[str, Any]] = []
    for info in projects_info:
        project_path = examples_path / str(info['dir_name'])
        enriched_info = dict(info)
        enriched_info['assessment'] = assess_example_project(
            project_path,
            project_manager=project_manager,
            project_info=info,
        )
        project_entries.append(enriched_info)

    by_format = group_projects_by_format(project_entries)
    total_svg_count = sum(info['svg_count'] for info in projects_info)
    curated_projects = [info for info in project_entries if info['assessment'].is_curated]
    preview_only_projects = [info for info in project_entries if not info['assessment'].is_curated]
    curated_by_format = group_projects_by_format(curated_projects)
    preview_by_format = group_projects_by_format(preview_only_projects)

    content: List[str] = []
    content.append('# SlideMax Example Index\n')
    content.append(f"> This file is generated automatically by `{context.command_reference}`\n")
    content.append(f"> Last updated: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")

    content.append('## Overview\n')
    content.append(f'- **Projects**: {len(project_entries)}')
    content.append(f'- **Curated reference projects**: {len(curated_projects)}')
    content.append(f'- **Preview-only projects**: {len(preview_only_projects)}')
    content.append(f'- **Canvas formats**: {len(by_format)}')
    content.append(f'- **SVG files**: {total_svg_count}')

    content.append('\n## Trust Policy\n')
    content.append('- Curated reference projects pass delivery validation and svg_final compatibility checks.')
    content.append('- Preview-only projects are kept for browsing, inspiration, or historical comparison and must not be used as a canonical workflow reference.')

    content.append('\n### Format distribution\n')
    for fmt_key in sorted(by_format.keys(), key=lambda key: len(by_format[key]), reverse=True):
        count = len(by_format[fmt_key])
        fmt_name = CANVAS_FORMATS.get(fmt_key, {}).get('name', fmt_key)
        content.append(f'- **{fmt_name}**: {count} projects')

    content.append('\n## Recently Updated\n')
    for info in projects_info[:5]:
        content.append(f"- **{info['name']}** ({info['format_name']}) - {info['date_formatted']}")

    content.append('\n## Curated Reference Projects\n')
    if not curated_projects:
        content.append('- No curated reference projects are available yet.')
    for fmt_key in FORMAT_ORDER:
        if fmt_key not in curated_by_format:
            continue

        fmt_info = CANVAS_FORMATS.get(fmt_key, {})
        fmt_name = fmt_info.get('name', fmt_key)
        dimensions = fmt_info.get('dimensions', '')
        content.append(f'\n### {fmt_name} ({dimensions})\n')

        projects_list = sorted(curated_by_format[fmt_key], key=project_sort_key)
        for info in projects_list:
            assessment = info['assessment']
            project_link = f"./{info['dir_name']}"
            line = f"- **[{info['name']}]({project_link})**"
            line += f" - {info['date_formatted']}"
            line += f" - {info['svg_count']} slides"
            line += f" - {assessment.reason_summary}"
            content.append(line)

    other_formats = set(curated_by_format.keys()) - set(FORMAT_ORDER)
    if other_formats:
        content.append('\n### Other formats\n')
        for fmt_key in sorted(other_formats):
            for info in sorted(curated_by_format[fmt_key], key=project_sort_key):
                assessment = info['assessment']
                project_link = f"./{info['dir_name']}"
                line = f"- **[{info['name']}]({project_link})**"
                line += f" ({info['format_name']}) - {info['date_formatted']}"
                line += f" - {info['svg_count']} slides"
                line += f" - {assessment.reason_summary}"
                content.append(line)

    content.append('\n## Preview-only Projects\n')
    if not preview_only_projects:
        content.append('- No preview-only projects are currently listed.')
    for fmt_key in FORMAT_ORDER:
        if fmt_key not in preview_by_format:
            continue

        fmt_info = CANVAS_FORMATS.get(fmt_key, {})
        fmt_name = fmt_info.get('name', fmt_key)
        dimensions = fmt_info.get('dimensions', '')
        content.append(f'\n### {fmt_name} ({dimensions})\n')

        projects_list = sorted(preview_by_format[fmt_key], key=project_sort_key)
        for info in projects_list:
            assessment = info['assessment']
            project_link = f"./{info['dir_name']}"
            line = f"- **[{info['name']}]({project_link})**"
            line += f" - {info['date_formatted']}"
            line += f" - {info['svg_count']} slides"
            line += f" - {assessment.reason_summary}"
            content.append(line)

    preview_other_formats = set(preview_by_format.keys()) - set(FORMAT_ORDER)
    if preview_other_formats:
        content.append('\n### Other formats\n')
        for fmt_key in sorted(preview_other_formats):
            for info in sorted(preview_by_format[fmt_key], key=project_sort_key):
                assessment = info['assessment']
                project_link = f"./{info['dir_name']}"
                line = f"- **[{info['name']}]({project_link})**"
                line += f" ({info['format_name']}) - {info['date_formatted']}"
                line += f" - {info['svg_count']} slides"
                line += f" - {assessment.reason_summary}"
                content.append(line)

    content.append('\n## Usage\n')
    content.append('### Preview a project\n')
    content.append('Each example project contains:\n')
    content.append('- `Design specification` markdown')
    content.append('- `svg_output/` - raw SVG output')
    content.append('- `svg_final/` - finalized SVG output')
    content.append('- `README.md` - required for curated reference projects\n')

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
    content.append('2. Include a complete `README.md` for new curated reference examples')
    content.append('3. Pass `project_manager validate` and keep `svg_final/` compatible with the SVG quality rules')
    content.append('4. Use the directory format `{project_name}_{format}_{YYYYMMDD}` for new examples')
    content.append('5. Legacy examples may use older naming conventions, but new additions should not\n')

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


def resolve_target_dirs(target_args: Sequence[str]) -> List[Path]:
    target_dirs = [Path(arg) for arg in target_args]
    if target_dirs:
        return target_dirs
    return get_example_dirs()


def run_cli(argv: Optional[Sequence[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(argv)
    target_dirs = resolve_target_dirs(args.examples_dirs)
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
    'CANONICAL_CLI',
    'SKILL_RESOURCES',
    'FORMAT_ORDER',
    'ExamplesRenderContext',
    'ExamplesIndexResult',
    'build_examples_index',
    'build_parser',
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
