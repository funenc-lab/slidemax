"""Shared project management service for SlideMax."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .config import WORKSPACE_DIR
from .exporters.pptx_assets import find_notes_files, get_png_renderer_info
from .image_generation import (
    ImageGenerationRequest,
    generate_image,
    provider_sdk_dependency_status,
    resolve_provider_config,
)
from .notes_splitter import parse_total_md
from .pptx_export import Presentation
from .project_utils import (
    CANVAS_FORMATS,
    get_project_info as get_project_info_common,
    normalize_canvas_format,
    validate_project_structure,
    validate_svg_viewbox,
)
from .project_state import build_project_state, write_project_state
from .svg_quality import SVGQualityChecker


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


@dataclass(frozen=True)
class PreflightCheck:
    """Single preflight or doctor check result."""

    name: str
    status: str
    message: str


def _find_svg_files(project_path: Path, directory_name: str) -> List[Path]:
    """Return SVG files from a project subdirectory."""

    svg_dir = project_path / directory_name
    if not svg_dir.exists():
        return []
    return sorted(svg_dir.glob('*.svg'))


class ProjectManager:
    """Create, validate, and inspect SlideMax projects."""

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
        state_payload = build_project_state(
            project_path,
            last_command_name='project_manager init',
        )
        write_project_state(project_path, state_payload)
        print(f'Project directory created: {project_path}')
        print(f"Canvas format: {canvas_info['name']} ({canvas_info['dimensions']})")
        return str(project_path)

    def validate_project(self, project_path: str | Path) -> Tuple[bool, List[str], List[str]]:
        """Validate a project's delivery readiness and SVG viewBox consistency."""

        project_path_obj = Path(project_path)
        is_valid, errors, warnings = validate_project_structure(str(project_path_obj))
        svg_files = _find_svg_output_files(project_path_obj)

        if project_path_obj.exists() and project_path_obj.is_dir():
            info = get_project_info_common(str(project_path_obj))
            expected_format = info.get('format')
            if expected_format == 'unknown':
                expected_format = None
            delivery_errors, delivery_warnings = _collect_delivery_errors(
                project_path_obj,
                svg_files,
                expected_format=expected_format,
            )
            errors.extend(delivery_errors)
            warnings.extend(delivery_warnings)

        return len(errors) == 0 and is_valid, errors, warnings

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


def _resolve_requested_provider(provider: Optional[str]) -> Optional[str]:
    if provider:
        return provider
    if os.environ.get('SLIDEMAX_IMAGE_PROVIDER'):
        return os.environ['SLIDEMAX_IMAGE_PROVIDER']
    if os.environ.get('DOUBAO_API_KEY') or os.environ.get('DOUBAO_IMAGE_MODEL'):
        return 'doubao'
    if os.environ.get('OPENAI_IMAGE_API_KEY') or os.environ.get('OPENAI_API_KEY'):
        return 'openai-compatible'
    if os.environ.get('GEMINI_API_KEY'):
        return 'gemini'
    return None


def _collect_notes_check(project_path: Path) -> PreflightCheck:
    notes_dir = project_path / 'notes'
    total_md_path = notes_dir / 'total.md'
    svg_stems = [path.stem for path in sorted((project_path / 'svg_output').glob('*.svg'))]
    split_notes = [path for path in notes_dir.glob('*.md') if path.name != 'total.md'] if notes_dir.exists() else []
    split_stems = {path.stem for path in split_notes}

    if not svg_stems:
        return PreflightCheck(
            name='notes_status',
            status='ok',
            message='No slide SVG files exist yet; notes coverage check is not applicable.',
        )

    if total_md_path.exists() and svg_stems and not split_notes:
        return PreflightCheck(
            name='notes_status',
            status='warning',
            message='total.md is present but split note files have not been generated yet.',
        )

    if svg_stems and set(svg_stems).issubset(split_stems):
        return PreflightCheck(
            name='notes_status',
            status='ok',
            message=f'Found {len(svg_stems)} slide note file(s) matching svg_output/.',
        )

    if total_md_path.exists():
        return PreflightCheck(
            name='notes_status',
            status='warning',
            message='total.md exists, but slide note files do not fully cover current SVG slides.',
        )

    return PreflightCheck(
        name='notes_status',
        status='warning',
        message='No notes/total.md or per-slide note files were found.',
    )


def _collect_template_check(project_path: Path) -> PreflightCheck:
    templates_dir = project_path / 'templates'
    template_svgs = sorted(templates_dir.glob('*.svg')) if templates_dir.exists() else []
    if not template_svgs:
        return PreflightCheck(
            name='template_svg_quality',
            status='ok',
            message='No template SVG files were found under templates/; skipping template validation.',
        )

    checker = SVGQualityChecker()
    failed_templates: List[str] = []
    for template_path in template_svgs:
        result = checker.check_file(str(template_path))
        if not result['passed']:
            failed_templates.append(template_path.name)

    if failed_templates:
        return PreflightCheck(
            name='template_svg_quality',
            status='error',
            message=f'Template SVG validation failed for: {", ".join(failed_templates)}',
        )

    return PreflightCheck(
        name='template_svg_quality',
        status='ok',
        message=f'Validated {len(template_svgs)} template SVG file(s).',
    )


def _find_svg_output_files(project_path: Path) -> List[Path]:
    """Return current raw SVG slides for validation flows."""

    return _find_svg_files(project_path, 'svg_output')


def _collect_delivery_slide_errors(project_path: Path, svg_files: List[Path]) -> List[str]:
    """Validate that raw slide SVG output exists before delivery checks continue."""

    if not (project_path / 'svg_output').exists():
        return []

    if svg_files:
        return []

    return ['No SVG slides were found under svg_output/. Generate slide SVG files before delivery validation.']


def _collect_delivery_notes_result(project_path: Path, svg_files: List[Path]) -> Tuple[List[str], List[str]]:
    """Validate that speaker notes cover every current slide."""

    warnings: List[str] = []
    if not svg_files:
        return [], warnings

    notes_map = find_notes_files(project_path, svg_files)
    missing_stems = [svg_path.stem for svg_path in svg_files if svg_path.stem not in notes_map]
    if not missing_stems:
        return [], warnings

    total_md_path = project_path / 'notes' / 'total.md'
    if total_md_path.exists():
        parsed_notes = parse_total_md(total_md_path, [svg_path.stem for svg_path in svg_files], False)
        missing_from_total = [svg_path.stem for svg_path in svg_files if svg_path.stem not in parsed_notes]
        if not missing_from_total:
            return [
                'Speaker notes are only present in notes/total.md. '
                'Run `python3 skills/slidemax_workflow/scripts/slidemax.py total_md_split <project-path>` '
                'to generate explicit per-slide note files before delivery.'
            ], warnings

    return [
        'Missing speaker notes for slide(s): '
        + ', '.join(missing_stems)
        + '. Generate per-slide notes or provide a complete notes/total.md.'
    ], warnings


def _collect_delivery_svg_final_errors(
    project_path: Path,
    svg_files: List[Path],
    *,
    expected_format: Optional[str],
) -> List[str]:
    """Validate that finalized SVG output exists for every current slide."""

    if not svg_files:
        return []

    svg_final_dir = project_path / 'svg_final'
    if not svg_final_dir.exists():
        return ['Missing svg_final/ directory required for finalized delivery assets.']

    finalized_stems = {svg_path.stem for svg_path in svg_final_dir.glob('*.svg')}
    missing_stems = [svg_path.stem for svg_path in svg_files if svg_path.stem not in finalized_stems]
    if missing_stems:
        return [
            'Missing finalized SVG file(s) under svg_final/: '
            + ', '.join(f'{stem}.svg' for stem in missing_stems)
        ]

    current_finalized_files = [svg_final_dir / f'{svg_path.stem}.svg' for svg_path in svg_files]
    viewbox_warnings = validate_svg_viewbox(current_finalized_files, expected_format)
    if not viewbox_warnings:
        return []

    return [f'Finalized SVG validation failed: {warning}' for warning in viewbox_warnings]


def _collect_delivery_pptx_errors(project_path: Path, svg_files: List[Path]) -> List[str]:
    """Validate that a PPTX export exists for projects with slide output."""

    if not svg_files:
        return []

    pptx_files = sorted(project_path.glob('*.pptx'))
    if pptx_files:
        return []

    return ['Missing exported PPTX file (*.pptx) in the project root.']


def _collect_delivery_errors(
    project_path: Path,
    svg_files: List[Path],
    *,
    expected_format: Optional[str],
) -> Tuple[List[str], List[str]]:
    """Collect strict delivery validation results for `validate`."""

    errors: List[str] = []
    warnings: List[str] = []

    errors.extend(_collect_delivery_slide_errors(project_path, svg_files))
    note_errors, note_warnings = _collect_delivery_notes_result(project_path, svg_files)
    errors.extend(note_errors)
    warnings.extend(note_warnings)
    errors.extend(
        _collect_delivery_svg_final_errors(
            project_path,
            svg_files,
            expected_format=expected_format,
        )
    )
    errors.extend(_collect_delivery_pptx_errors(project_path, svg_files))
    return errors, warnings


def _collect_preflight_project_structure_check(project_path: Path) -> PreflightCheck:
    """Validate only the project skeleton needed for preflight flows."""

    if not project_path.exists():
        return PreflightCheck(
            name='project_structure',
            status='error',
            message=f'Project path does not exist: {project_path}',
        )

    if not project_path.is_dir():
        return PreflightCheck(
            name='project_structure',
            status='error',
            message=f'Project path is not a directory: {project_path}',
        )

    required_paths = [
        project_path / 'README.md',
        project_path / 'svg_output',
        project_path / 'svg_final',
        project_path / 'images',
        project_path / 'notes',
        project_path / 'templates',
    ]
    missing_paths = [path.name for path in required_paths if not path.exists()]
    if missing_paths:
        return PreflightCheck(
            name='project_structure',
            status='error',
            message='Missing required project path(s): ' + ', '.join(missing_paths),
        )

    return PreflightCheck(
        name='project_structure',
        status='ok',
        message='Project structure looks complete.',
    )


def build_preflight_checks(
    project_path: Optional[str | Path] = None,
    *,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> List[PreflightCheck]:
    """Build the canonical doctor/preflight checks for a project or environment."""

    checks: List[PreflightCheck] = []

    checks.append(
        PreflightCheck(
            name='python_pptx',
            status='ok' if Presentation is not None else 'error',
            message='python-pptx is available.' if Presentation is not None else 'python-pptx is missing. Run: pip install python-pptx',
        )
    )

    checks.append(
        PreflightCheck(
            name='requests',
            status='ok' if importlib.util.find_spec('requests') is not None else 'warning',
            message=(
                'requests is available.'
                if importlib.util.find_spec('requests') is not None
                else 'requests is missing. Install it with: pip install requests or pip install -r requirements.txt'
            ),
        )
    )

    checks.append(
        PreflightCheck(
            name='pillow',
            status='ok' if importlib.util.find_spec('PIL') is not None else 'warning',
            message=(
                'Pillow is available.'
                if importlib.util.find_spec('PIL') is not None
                else 'Pillow is not installed. Image generation still works, but local resolution inspection is disabled. Install it with: pip install Pillow'
            ),
        )
    )

    renderer_name, renderer_detail, renderer_hint = get_png_renderer_info()
    if renderer_name:
        checks.append(
            PreflightCheck(
                name='png_renderer',
                status='ok',
                message=f'PNG renderer ready: {renderer_name} {renderer_detail}'.strip(),
            )
        )
    else:
        checks.append(
            PreflightCheck(
                name='png_renderer',
                status='warning',
                message=renderer_hint or 'No PNG renderer is installed.',
            )
        )

    requested_provider = _resolve_requested_provider(provider)
    if requested_provider:
        dependency_ready, dependency_message = provider_sdk_dependency_status(requested_provider)
        checks.append(
            PreflightCheck(
                name='image_provider_sdk',
                status='ok' if dependency_ready else 'error',
                message=dependency_message,
            )
        )
        try:
            config = resolve_provider_config(provider=requested_provider, model=model)
            checks.append(
                PreflightCheck(
                    name='image_provider',
                    status='ok',
                    message=f'provider={config.provider}, model={config.model}, base_url={config.base_url or config.endpoint or "<default>"}',
                )
            )
        except Exception as exc:
            checks.append(
                PreflightCheck(
                    name='image_provider',
                    status='error',
                    message=str(exc),
                )
            )

    if project_path is None:
        return checks

    project_path_obj = Path(project_path)
    checks.append(_collect_preflight_project_structure_check(project_path_obj))
    checks.append(_collect_template_check(project_path_obj))
    checks.append(_collect_notes_check(project_path_obj))

    return checks


def run_preflight_smoke_test(
    *,
    provider: str,
    model: Optional[str],
    output_dir: str | Path,
    prompt: str = 'Minimal geometric business background',
    aspect_ratio: str = '16:9',
    image_size: str = '1K',
    filename: str = 'doctor_smoke_test',
    max_retries: int = 0,
) -> Path:
    """Run a live provider smoke test and return the generated asset path."""

    config = resolve_provider_config(provider=provider, model=model, output_dir=output_dir)
    request = ImageGenerationRequest(
        prompt=prompt,
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        output_dir=Path(output_dir),
        filename=filename,
    )
    result = generate_image(request, config, max_retries=max_retries)
    return result.path


def _serialize_preflight_checks(checks: List[PreflightCheck]) -> List[Dict[str, str]]:
    return [
        {'name': check.name, 'status': check.status, 'message': check.message}
        for check in checks
    ]


def _build_preflight_report(
    *,
    project_path: Optional[str],
    provider: Optional[str],
    model: Optional[str],
    checks: List[PreflightCheck],
    smoke_result: Optional[Dict[str, str]],
    status: str,
) -> Dict[str, object]:
    return {
        'status': status,
        'generated_at': datetime.utcnow().isoformat(timespec='seconds') + 'Z',
        'project_path': project_path,
        'provider': provider,
        'model': model,
        'checks': _serialize_preflight_checks(checks),
        'smoke_test': smoke_result,
    }


def _write_preflight_report(output_path: str | Path, payload: Dict[str, object]) -> Path:
    resolved_path = Path(output_path)
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return resolved_path


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for the project manager."""

    parser = argparse.ArgumentParser(
        prog='python3 skills/slidemax_workflow/scripts/slidemax.py project_manager',
        description='SlideMax project manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
When to use:
  - init: create a new workspace project before any SVG, notes, or image assets are written
  - info: inspect an existing project quickly
  - audit: inspect workflow stage progression and detect blocking gaps between stages
  - doctor: run preflight checks before generation or provider setup
  - validate: enforce the final delivery gate before claiming completion

Examples:
  %(prog)s init my_project --format ppt169
  %(prog)s audit workspace/my_project_ppt169_20260308
  %(prog)s validate workspace/my_project_ppt169_20260308
  %(prog)s info workspace/my_project_ppt169_20260308
  %(prog)s doctor workspace/my_project_ppt169_20260308 --provider doubao --model doubao-seedream-5
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

    audit_parser = subparsers.add_parser('audit', help='Audit workflow stage progression')
    audit_parser.add_argument('project_path', help='Project path')

    doctor_parser = subparsers.add_parser('doctor', help='Run environment and project preflight checks')
    doctor_parser.add_argument('project_path', nargs='?', default=None, help='Optional project path')
    doctor_parser.add_argument('--provider', default=None, help='Image provider to validate')
    doctor_parser.add_argument('--model', default=None, help='Image model override to validate')
    doctor_parser.add_argument('--smoke-test', action='store_true', help='Run a live provider smoke test after static checks')
    doctor_parser.add_argument('--smoke-output', default='tmp/slidemax_smoke', help='Output directory for smoke test artifacts')
    doctor_parser.add_argument('--smoke-prompt', default='Minimal geometric business background', help='Prompt used for the smoke test')
    doctor_parser.add_argument('--smoke-aspect-ratio', dest='smoke_aspect_ratio', default='16:9', help='Aspect ratio used for the smoke test')
    doctor_parser.add_argument('--smoke-image-size', dest='smoke_image_size', default='1K', help='Image size used for the smoke test')
    doctor_parser.add_argument('--json-output', default=None, help='Optional path to write a machine-readable preflight report')

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
        state_payload = build_project_state(
            Path(args.project_path),
            last_command_name='project_manager validate',
            validation_result={
                'status': 'passed' if is_valid else 'failed',
                'errors': len(errors),
                'warnings': len(warnings),
            },
        )
        write_project_state(Path(args.project_path), state_payload)
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
            print('\n[OK] Delivery validation passed with no issues')
            return 0
        if is_valid:
            print('\n[OK] Delivery validation passed with recommendations')
            return 0

        print('\n[ERROR] Delivery validation failed; please fix the reported errors')
        return 1

    if args.command == 'info':
        info = manager.get_project_info(args.project_path)
        state_payload = build_project_state(Path(args.project_path))
        print(f"\nProject info: {info['name']}")
        print('=' * 60)
        print(f"Path: {info['path']}")
        print(f"Exists: {'yes' if info['exists'] else 'no'}")
        print(f"SVG files: {info['svg_count']}")
        print(f"Design spec: {'present' if info['has_spec'] else 'missing'}")
        print(f"Canvas format: {info['canvas_format']}")
        print(f"Created: {info['create_date']}")
        print(f"Current stage: {state_payload['current_stage']}")
        print(f"Next step: {state_payload['next_step']}")
        return 0

    if args.command == 'audit':
        project_path = Path(args.project_path)
        state_payload = build_project_state(
            project_path,
            last_command_name='project_manager audit',
        )
        write_project_state(project_path, state_payload)

        print(f'\nProject audit: {project_path}')
        print('=' * 60)
        print(f"Current stage: {state_payload['current_stage']}")
        print(f"Next step: {state_payload['next_step']}")

        print('\nStages:')
        for stage in state_payload['stages']:
            status_token = 'OK' if stage['status'] == 'completed' else 'PENDING'
            print(f"  - [{status_token}] {stage['name']}: {stage['detail']}")

        if state_payload['blocking_issues']:
            print('\nBlocking issues:')
            for issue in state_payload['blocking_issues']:
                print(f'  - {issue}')

        if state_payload['warnings']:
            print('\nWarnings:')
            for warning in state_payload['warnings']:
                print(f'  - {warning}')

        if state_payload['blocking_issues']:
            print('\n[ERROR] Audit found blocking workflow issues')
            return 1

        print('\n[OK] Audit completed')
        return 0

    if args.command == 'doctor':
        checks = build_preflight_checks(
            project_path=args.project_path,
            provider=args.provider,
            model=args.model,
        )
        print('\nPPT preflight checks')
        print('=' * 60)
        has_errors = False
        smoke_result: Optional[Dict[str, str]] = None
        for check in checks:
            print(f'- {check.name}: {check.status} - {check.message}')
            if check.status == 'error':
                has_errors = True

        if args.smoke_test:
            if not args.provider:
                smoke_result = {'status': 'error', 'message': '--provider is required when --smoke-test is enabled'}
                print('- smoke_test: error - --provider is required when --smoke-test is enabled')
                has_errors = True
            else:
                try:
                    smoke_path = run_preflight_smoke_test(
                        provider=args.provider,
                        model=args.model,
                        output_dir=args.smoke_output,
                        prompt=args.smoke_prompt,
                        aspect_ratio=args.smoke_aspect_ratio,
                        image_size=args.smoke_image_size,
                    )
                    smoke_result = {'status': 'ok', 'path': str(smoke_path)}
                    print(f'- smoke_test: ok - generated {smoke_path}')
                except Exception as exc:
                    smoke_result = {'status': 'error', 'message': str(exc)}
                    print(f'- smoke_test: error - {exc}')
                    has_errors = True

        report_status = 'error' if has_errors else 'ok'
        if args.json_output:
            report_payload = _build_preflight_report(
                project_path=args.project_path,
                provider=args.provider,
                model=args.model,
                checks=checks,
                smoke_result=smoke_result,
                status=report_status,
            )
            report_path = _write_preflight_report(args.json_output, report_payload)
            print(f'- json_output: ok - wrote {report_path}')

        if has_errors:
            print('\n[ERROR] Preflight found blocking issues')
            return 1

        print('\n[OK] Preflight completed')
        return 0

    print(f"[ERROR] Unknown command: {args.command}")
    return 1


def main() -> None:
    raise SystemExit(run_cli())


__all__ = [
    'PreflightCheck',
    'ProjectInfoSummary',
    'build_preflight_checks',
    'run_preflight_smoke_test',
    'ProjectManager',
    'build_parser',
    'main',
    'run_cli',
]
