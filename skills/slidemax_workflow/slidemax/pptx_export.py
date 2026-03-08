"""Shared export orchestration for the PPTX CLI entrypoint."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .config import CANVAS_FORMATS
from .exporters.pptx_assets import (
    PNG_RENDERER,
    convert_svg_to_png,
    detect_format_from_svg,
    find_notes_files,
    find_svg_files,
    get_pixel_dimensions,
    get_png_renderer_info,
    get_slide_dimensions,
    get_viewbox_dimensions,
)
from .exporters.pptx_openxml import (
    create_notes_slide_rels_xml,
    create_notes_slide_xml,
    create_slide_rels_xml,
    create_slide_xml_with_svg,
    markdown_to_plain_text,
)
from .exporters.pptx_runtime import (
    NativeSvgExportDependencies,
    NativeSvgExportRequest,
    export_presentation,
)
from .notes_splitter import check_svg_note_mapping, parse_total_md, split_notes
from .project_utils import get_project_info

try:
    from pptx import Presentation
except ImportError:
    Presentation = None

try:
    from .pptx_animations import TRANSITIONS, create_transition_xml
except ImportError:
    TRANSITIONS = {}
    create_transition_xml = None

DEFAULT_TRANSITION_CHOICES = ['fade', 'push', 'wipe', 'split', 'reveal', 'cover', 'random']


@dataclass(frozen=True)
class PptxExportRequest:
    """Typed export request parsed from CLI arguments."""

    project_path: Path
    output: Optional[str]
    source: str
    canvas_format: Optional[str]
    quiet: bool
    use_compat_mode: bool
    transition: Optional[str]
    transition_duration: float
    auto_advance: Optional[float]
    enable_notes: bool


@dataclass(frozen=True)
class PptxExportContext:
    """Resolved export inputs ready for the low-level exporter."""

    project_path: Path
    project_name: str
    output_path: Path
    svg_files: List[Path]
    source_dir_name: str
    canvas_format: Optional[str]
    verbose: bool
    notes: Dict[str, str]
    enable_notes: bool
    use_compat_mode: bool
    transition: Optional[str]
    transition_duration: float
    auto_advance: Optional[float]


def build_transition_choices() -> List[str]:
    if TRANSITIONS:
        return list(TRANSITIONS.keys())
    return list(DEFAULT_TRANSITION_CHOICES)


def build_cli_parser() -> argparse.ArgumentParser:
    """Build the canonical CLI parser using repository defaults."""

    return build_parser(CANVAS_FORMATS, build_transition_choices())


def build_parser(canvas_formats: Dict[str, dict], transition_choices: Sequence[str]) -> argparse.ArgumentParser:
    """Build the CLI parser for PPTX export entrypoints."""

    parser = argparse.ArgumentParser(
        description="SlideMax - SVG to PPTX exporter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
    %(prog)s skills/slidemax_workflow/examples/demo_project_intro_ppt169_20251211 -s final
    %(prog)s skills/slidemax_workflow/examples/demo_project_intro_ppt169_20251211 --no-compat
    %(prog)s skills/slidemax_workflow/examples/demo_project_intro_ppt169_20251211 --transition fade

SVG source (-s):
    output   - svg_output
    final    - svg_final
    <name>   - any project subdirectory

Transition choices:
    {', '.join(transition_choices)}
        """,
    )
    parser.add_argument("project_path", type=str, help="Project directory path")
    parser.add_argument("-o", "--output", type=str, default=None, help="Output PPTX path")
    parser.add_argument(
        "-s",
        "--source",
        type=str,
        default="output",
        help="SVG source directory alias or project subdirectory",
    )
    parser.add_argument(
        "-f",
        "--format",
        type=str,
        choices=list(canvas_formats.keys()),
        default=None,
        help="Force a canvas format",
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="Reduce console output")
    parser.add_argument(
        "--no-compat",
        action="store_true",
        help="Disable Office compatibility mode",
    )
    parser.add_argument(
        "-t",
        "--transition",
        type=str,
        choices=list(transition_choices),
        default=None,
        help="Slide transition name",
    )
    parser.add_argument(
        "--transition-duration",
        type=float,
        default=0.5,
        help="Transition duration in seconds",
    )
    parser.add_argument(
        "--auto-advance",
        type=float,
        default=None,
        help="Auto-advance interval in seconds",
    )
    parser.add_argument(
        "--no-notes",
        action="store_true",
        help="Disable speaker notes embedding",
    )
    return parser


def request_from_args(args: argparse.Namespace) -> PptxExportRequest:
    """Convert parsed CLI arguments into a typed request."""

    return PptxExportRequest(
        project_path=Path(args.project_path),
        output=args.output,
        source=args.source,
        canvas_format=args.format,
        quiet=args.quiet,
        use_compat_mode=not args.no_compat,
        transition=args.transition,
        transition_duration=args.transition_duration,
        auto_advance=args.auto_advance,
        enable_notes=not args.no_notes,
    )


def resolve_context(
    request: PptxExportRequest,
    get_project_info_func: Callable[[str], Dict],
    find_svg_files_func: Callable[[Path, str], Tuple[List[Path], str]] = find_svg_files,
    find_notes_files_func: Callable[[Path, Optional[List[Path]]], Dict[str, str]] = find_notes_files,
) -> PptxExportContext:
    """Resolve a high-level export request into concrete export inputs."""

    if not request.project_path.exists():
        raise FileNotFoundError(f"Path does not exist: {request.project_path}")

    try:
        project_info = get_project_info_func(str(request.project_path))
        project_name = project_info.get("name", request.project_path.name)
        detected_format = project_info.get("format")
    except Exception:
        project_name = request.project_path.name
        detected_format = None

    canvas_format = request.canvas_format
    if canvas_format is None and detected_format and detected_format != "unknown":
        canvas_format = detected_format

    svg_files, source_dir_name = find_svg_files_func(request.project_path, request.source)
    if not svg_files:
        raise FileNotFoundError("No SVG files found for export")

    if request.output:
        output_path = Path(request.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = request.project_path / f"{project_name}_{timestamp}.pptx"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    notes: Dict[str, str] = {}
    if request.enable_notes:
        notes = hydrate_notes_for_export(
            request.project_path,
            svg_files,
            find_notes_files_func=find_notes_files_func,
        )

    return PptxExportContext(
        project_path=request.project_path,
        project_name=project_name,
        output_path=output_path,
        svg_files=svg_files,
        source_dir_name=source_dir_name,
        canvas_format=canvas_format,
        verbose=not request.quiet,
        notes=notes,
        enable_notes=request.enable_notes,
        use_compat_mode=request.use_compat_mode,
        transition=request.transition,
        transition_duration=request.transition_duration,
        auto_advance=request.auto_advance,
    )


def hydrate_notes_for_export(
    project_path: Path,
    svg_files: List[Path],
    *,
    find_notes_files_func: Callable[[Path, Optional[List[Path]]], Dict[str, str]] = find_notes_files,
    parse_total_md_func: Callable[[Path, Optional[List[str]], bool], Dict[str, str]] = parse_total_md,
    split_notes_func: Callable[[Dict[str, str], Path, bool], bool] = split_notes,
) -> Dict[str, str]:
    """Return export-ready notes, auto-splitting notes/total.md when needed."""

    existing_notes = find_notes_files_func(project_path, svg_files)
    if existing_notes:
        return existing_notes

    total_md_path = project_path / 'notes' / 'total.md'
    if not total_md_path.exists():
        return {}

    svg_stems = [svg_path.stem for svg_path in svg_files]
    parsed_notes = parse_total_md_func(total_md_path, svg_stems, False)
    if not parsed_notes:
        return {}

    all_match, _missing_notes = check_svg_note_mapping(svg_files, parsed_notes)
    if not all_match:
        return parsed_notes

    split_notes_func(parsed_notes, project_path / 'notes', False)
    refreshed_notes = find_notes_files_func(project_path, svg_files)
    return refreshed_notes or parsed_notes


def print_context_summary(context: PptxExportContext) -> None:
    """Print a concise export summary."""

    print("SlideMax - SVG to PPTX exporter")
    print("=" * 50)
    print(f"  Project path: {context.project_path}")
    print(f"  SVG source:   {context.source_dir_name}")
    print(f"  Output file:  {context.output_path}")
    print()


def ensure_pptx_dependency() -> bool:
    """Return whether python-pptx is available for export."""

    if Presentation is None:
        print('Error: missing python-pptx library')
        print('Run: pip install python-pptx')
        return False
    return True


def resolve_transition_name(transition: Optional[str]) -> Optional[str]:
    """Resolve the display name for a transition key."""

    if not TRANSITIONS:
        return transition
    return TRANSITIONS.get(transition, {}).get('name', transition)


def build_native_svg_dependencies(
    *,
    presentation_factory=None,
    transition_name_resolver: Optional[Callable[[Optional[str]], Optional[str]]] = None,
    transition_xml_builder=None,
) -> NativeSvgExportDependencies:
    """Build the canonical dependency bundle for native SVG PPTX export."""

    return NativeSvgExportDependencies(
        presentation_factory=(Presentation if presentation_factory is None else presentation_factory),
        get_png_renderer_info=get_png_renderer_info,
        png_renderer=PNG_RENDERER,
        detect_format_from_svg=detect_format_from_svg,
        get_viewbox_dimensions=get_viewbox_dimensions,
        get_slide_dimensions=get_slide_dimensions,
        get_pixel_dimensions=get_pixel_dimensions,
        canvas_formats=CANVAS_FORMATS,
        resolve_transition_name=(resolve_transition_name if transition_name_resolver is None else transition_name_resolver),
        transition_xml_builder=(create_transition_xml if transition_xml_builder is None else transition_xml_builder),
        convert_svg_to_png=convert_svg_to_png,
        create_slide_xml_with_svg=create_slide_xml_with_svg,
        create_slide_rels_xml=create_slide_rels_xml,
        markdown_to_plain_text=markdown_to_plain_text,
        create_notes_slide_xml=create_notes_slide_xml,
        create_notes_slide_rels_xml=create_notes_slide_rels_xml,
    )


def create_pptx_with_native_svg(
    svg_files: List[Path],
    output_path: Path,
    canvas_format: Optional[str] = None,
    verbose: bool = True,
    transition: Optional[str] = None,
    transition_duration: float = 0.5,
    auto_advance: Optional[float] = None,
    use_compat_mode: bool = True,
    notes: Optional[dict] = None,
    enable_notes: bool = True,
) -> bool:
    """Create a PPTX file with native SVG content."""

    if not ensure_pptx_dependency():
        return False

    request = NativeSvgExportRequest(
        svg_files=svg_files,
        output_path=output_path,
        canvas_format=canvas_format,
        verbose=verbose,
        transition=transition,
        transition_duration=transition_duration,
        auto_advance=auto_advance,
        use_compat_mode=use_compat_mode,
        notes=notes,
        enable_notes=enable_notes,
    )
    dependencies = build_native_svg_dependencies()
    return export_presentation(request, dependencies)


def run_export(
    request: PptxExportRequest,
    get_project_info_func: Callable[[str], Dict],
    create_pptx: Callable[..., bool],
    find_svg_files_func: Callable[[Path, str], Tuple[List[Path], str]] = find_svg_files,
    find_notes_files_func: Callable[[Path, Optional[List[Path]]], Dict[str, str]] = find_notes_files,
) -> int:
    """Resolve context and invoke the low-level PPTX exporter."""

    context = resolve_context(
        request,
        get_project_info_func=get_project_info_func,
        find_svg_files_func=find_svg_files_func,
        find_notes_files_func=find_notes_files_func,
    )

    if context.verbose:
        print_context_summary(context)

    success = create_pptx(
        context.svg_files,
        context.output_path,
        canvas_format=context.canvas_format,
        verbose=context.verbose,
        transition=context.transition,
        transition_duration=context.transition_duration,
        auto_advance=context.auto_advance,
        use_compat_mode=context.use_compat_mode,
        notes=context.notes,
        enable_notes=context.enable_notes,
    )
    return 0 if success else 1


def run_cli(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_cli_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    request = request_from_args(args)
    try:
        return run_export(
            request,
            get_project_info_func=get_project_info,
            create_pptx=create_pptx_with_native_svg,
        )
    except FileNotFoundError as exc:
        print(f'Error: {exc}')
        return 1


def main() -> None:
    raise SystemExit(run_cli())


__all__ = [
    'DEFAULT_TRANSITION_CHOICES',
    'PptxExportContext',
    'PptxExportRequest',
    'build_parser',
    'build_cli_parser',
    'build_native_svg_dependencies',
    'build_transition_choices',
    'create_pptx_with_native_svg',
    'ensure_pptx_dependency',
    'hydrate_notes_for_export',
    'main',
    'print_context_summary',
    'request_from_args',
    'resolve_context',
    'resolve_transition_name',
    'run_cli',
    'run_export',
]
