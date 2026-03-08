"""Runtime helpers for PPTX export orchestration."""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class ExportGeometry:
    """Resolved geometry for PPTX export."""

    canvas_format: Optional[str]
    custom_pixels: Optional[Tuple[int, int]]
    width_emu: int
    height_emu: int
    pixel_width: int
    pixel_height: int


@dataclass(frozen=True)
class ExportSession:
    """Temporary filesystem layout for PPTX export."""

    temp_dir: Path
    base_pptx: Path
    extract_dir: Path
    media_dir: Path


@dataclass(frozen=True)
class SlideAsset:
    """Resolved media names for a slide."""

    slide_num: int
    svg_filename: str
    png_filename: str
    png_rid: str
    svg_rid: str


@dataclass(frozen=True)
class SlideExportResult:
    """Per-slide export result."""

    slide_has_png: bool
    notes_content: str


@dataclass(frozen=True)
class CompatibilityState:
    """Resolved compatibility mode state."""

    use_compat_mode: bool
    renderer_name: Optional[str]
    renderer_status: str
    renderer_hint: Optional[str]


@dataclass(frozen=True)
class NativeSvgExportRequest:
    """High-level request for exporting a presentation from SVG slides."""

    svg_files: List[Path]
    output_path: Path
    canvas_format: Optional[str] = None
    verbose: bool = True
    transition: Optional[str] = None
    transition_duration: float = 0.5
    auto_advance: Optional[float] = None
    use_compat_mode: bool = True
    notes: Optional[Dict[str, str]] = None
    enable_notes: bool = True


@dataclass(frozen=True)
class NativeSvgExportDependencies:
    """Injected dependencies for native SVG presentation export."""

    presentation_factory: Callable[[], object]
    get_png_renderer_info: Callable[[], Tuple[Optional[str], str, Optional[str]]]
    png_renderer: Optional[str]
    detect_format_from_svg: Callable[[Path], Optional[str]]
    get_viewbox_dimensions: Callable[[Path], Optional[Tuple[int, int]]]
    get_slide_dimensions: Callable[[str, Optional[Tuple[int, int]]], Tuple[int, int]]
    get_pixel_dimensions: Callable[[str, Optional[Tuple[int, int]]], Tuple[int, int]]
    canvas_formats: Dict[str, dict]
    resolve_transition_name: Callable[[Optional[str]], Optional[str]]
    transition_xml_builder: Optional[Callable[..., str]]
    convert_svg_to_png: Callable[..., bool]
    create_slide_xml_with_svg: Callable[..., str]
    create_slide_rels_xml: Callable[..., str]
    markdown_to_plain_text: Callable[[str], str]
    create_notes_slide_xml: Callable[[int, str], str]
    create_notes_slide_rels_xml: Callable[[int], str]


TransitionBuilder = Optional[Callable[..., str]]


def resolve_compatibility(
    use_compat_mode: bool,
    renderer_name: Optional[str],
    renderer_status: str,
    renderer_hint: Optional[str],
    png_renderer: Optional[str],
) -> CompatibilityState:
    """Normalize compatibility mode based on available renderers."""

    if use_compat_mode and png_renderer is None:
        print("Warning: no PNG renderer installed, compatibility mode disabled")
        if renderer_hint:
            print(f"  {renderer_hint}")
        print("  Falling back to pure SVG mode")
        use_compat_mode = False

    return CompatibilityState(
        use_compat_mode=use_compat_mode,
        renderer_name=renderer_name,
        renderer_status=renderer_status,
        renderer_hint=renderer_hint,
    )


def resolve_geometry(
    svg_files: List[Path],
    canvas_format: Optional[str],
    verbose: bool,
    detect_format_from_svg: Callable[[Path], Optional[str]],
    get_viewbox_dimensions: Callable[[Path], Optional[Tuple[int, int]]],
    get_slide_dimensions: Callable[[str, Optional[Tuple[int, int]]], Tuple[int, int]],
    get_pixel_dimensions: Callable[[str, Optional[Tuple[int, int]]], Tuple[int, int]],
    canvas_formats: Dict[str, dict],
) -> ExportGeometry:
    """Resolve export geometry from explicit format or SVG metadata."""

    custom_pixels: Optional[Tuple[int, int]] = None
    resolved_canvas_format = canvas_format

    if resolved_canvas_format is None:
        resolved_canvas_format = detect_format_from_svg(svg_files[0])
        if resolved_canvas_format and verbose:
            format_name = canvas_formats.get(resolved_canvas_format, {}).get("name", resolved_canvas_format)
            print(f"  Detected canvas format: {format_name}")

    if resolved_canvas_format is None:
        custom_pixels = get_viewbox_dimensions(svg_files[0])
        if custom_pixels and verbose:
            print(f"  Using SVG viewBox dimensions: {custom_pixels[0]} x {custom_pixels[1]} px")

    if resolved_canvas_format is None and custom_pixels is None:
        resolved_canvas_format = "ppt169"
        if verbose:
            print("  Using default format: PPT 16:9")

    width_emu, height_emu = get_slide_dimensions(resolved_canvas_format or "ppt169", custom_pixels)
    pixel_width, pixel_height = get_pixel_dimensions(resolved_canvas_format or "ppt169", custom_pixels)
    return ExportGeometry(
        canvas_format=resolved_canvas_format,
        custom_pixels=custom_pixels,
        width_emu=width_emu,
        height_emu=height_emu,
        pixel_width=pixel_width,
        pixel_height=pixel_height,
    )


def print_export_summary(
    geometry: ExportGeometry,
    svg_count: int,
    compatibility: CompatibilityState,
    transition: Optional[str],
    transition_name: Optional[str],
    enable_notes: bool,
    notes: Optional[Dict[str, str]],
) -> None:
    """Print export configuration summary."""

    print(f"  Slide size: {geometry.pixel_width} x {geometry.pixel_height} px")
    print(f"  SVG files: {svg_count}")
    if compatibility.use_compat_mode:
        print("  Compatibility mode: enabled (PNG + SVG)")
        print(f"  PNG renderer: {compatibility.renderer_name} {compatibility.renderer_status}")
    else:
        print("  Compatibility mode: disabled (pure SVG)")
    if transition:
        print(f"  Transition: {transition_name or transition}")
    if enable_notes and notes:
        print(f"  Speaker notes: {len(notes)} slide(s)")
    elif enable_notes:
        print("  Speaker notes: enabled (no note files found)")
    else:
        print("  Speaker notes: disabled")
    print()


def create_session(
    presentation_factory: Callable[[], object],
    svg_count: int,
    width_emu: int,
    height_emu: int,
) -> ExportSession:
    """Create the temporary PPTX workspace and base presentation."""

    temp_dir = Path(tempfile.mkdtemp())
    base_pptx = temp_dir / "base.pptx"
    extract_dir = temp_dir / "pptx_content"

    presentation = presentation_factory()
    presentation.slide_width = width_emu
    presentation.slide_height = height_emu
    blank_layout = presentation.slide_layouts[6]
    for _ in range(svg_count):
        presentation.slides.add_slide(blank_layout)
    presentation.save(str(base_pptx))

    with zipfile.ZipFile(base_pptx, "r") as archive:
        archive.extractall(extract_dir)

    media_dir = extract_dir / "ppt" / "media"
    media_dir.mkdir(exist_ok=True)
    return ExportSession(
        temp_dir=temp_dir,
        base_pptx=base_pptx,
        extract_dir=extract_dir,
        media_dir=media_dir,
    )


def cleanup_session(session: ExportSession) -> None:
    """Remove temporary export files."""

    shutil.rmtree(session.temp_dir, ignore_errors=True)


def build_slide_asset(slide_num: int, use_compat_mode: bool) -> SlideAsset:
    """Create deterministic file names and relationship ids for a slide."""

    return SlideAsset(
        slide_num=slide_num,
        svg_filename=f"image{slide_num}.svg",
        png_filename=f"image{slide_num}.png",
        png_rid="rId2",
        svg_rid="rId3" if use_compat_mode else "rId2",
    )


def write_notes_for_slide(
    session: ExportSession,
    rels_path: Path,
    slide_num: int,
    notes_text: str,
    create_notes_slide_xml: Callable[[int, str], str],
    create_notes_slide_rels_xml: Callable[[int], str],
) -> None:
    """Write notes XML and wire it into the slide relationships."""

    notes_slides_dir = session.extract_dir / "ppt" / "notesSlides"
    notes_slides_dir.mkdir(exist_ok=True)

    notes_xml_path = notes_slides_dir / f"notesSlide{slide_num}.xml"
    notes_xml_path.write_text(create_notes_slide_xml(slide_num, notes_text), encoding="utf-8")

    notes_rels_dir = notes_slides_dir / "_rels"
    notes_rels_dir.mkdir(exist_ok=True)
    notes_rels_path = notes_rels_dir / f"notesSlide{slide_num}.xml.rels"
    notes_rels_path.write_text(create_notes_slide_rels_xml(slide_num), encoding="utf-8")

    slide_rels_content = rels_path.read_text(encoding="utf-8")
    notes_rel = (
        '  <Relationship Id="rId10" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide" '
        f'Target="../notesSlides/notesSlide{slide_num}.xml"/>'
    )
    rels_path.write_text(
        slide_rels_content.replace("</Relationships>", notes_rel + "\n</Relationships>"),
        encoding="utf-8",
    )


def update_content_types(
    extract_dir: Path,
    any_png_generated: bool,
    enable_notes: bool,
    slide_count: int,
) -> None:
    """Update PPTX content types for SVG, PNG and notes slides."""

    content_types_path = extract_dir / "[Content_Types].xml"
    content_types = content_types_path.read_text(encoding="utf-8")

    defaults_to_add = []
    if 'Extension="svg"' not in content_types:
        defaults_to_add.append('  <Default Extension="svg" ContentType="image/svg+xml"/>')
    if any_png_generated and 'Extension="png"' not in content_types:
        defaults_to_add.append('  <Default Extension="png" ContentType="image/png"/>')

    if defaults_to_add:
        content_types = content_types.replace("</Types>", "\n".join(defaults_to_add) + "\n</Types>")

    if enable_notes:
        for slide_num in range(1, slide_count + 1):
            override = (
                f'  <Override PartName="/ppt/notesSlides/notesSlide{slide_num}.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"/>'
            )
            if override not in content_types:
                content_types = content_types.replace("</Types>", override + "\n</Types>")

    content_types_path.write_text(content_types, encoding="utf-8")


def export_slide(
    session: ExportSession,
    svg_path: Path,
    asset: SlideAsset,
    geometry: ExportGeometry,
    compatibility: CompatibilityState,
    transition: Optional[str],
    transition_duration: float,
    auto_advance: Optional[float],
    enable_notes: bool,
    notes_mapping: Dict[str, str],
    transition_xml_builder: TransitionBuilder,
    convert_svg_to_png: Callable[..., bool],
    create_slide_xml_with_svg: Callable[..., str],
    create_slide_rels_xml: Callable[..., str],
    markdown_to_plain_text: Callable[[str], str],
    create_notes_slide_xml: Callable[[int, str], str],
    create_notes_slide_rels_xml: Callable[[int], str],
    verbose: bool = False,
    index: int = 1,
    total: int = 1,
) -> SlideExportResult:
    """Export a single SVG slide into the extracted PPTX tree."""

    shutil.copy(svg_path, session.media_dir / asset.svg_filename)

    slide_has_png = False
    active_svg_rid = asset.svg_rid
    if compatibility.use_compat_mode:
        png_path = session.media_dir / asset.png_filename
        png_success = convert_svg_to_png(
            svg_path,
            png_path,
            width=geometry.pixel_width,
            height=geometry.pixel_height,
        )
        if png_success:
            slide_has_png = True
        else:
            if verbose:
                print(f"  [{index}/{total}] {svg_path.name} - PNG fallback failed, using pure SVG")
            active_svg_rid = "rId2"

    slide_xml_path = session.extract_dir / "ppt" / "slides" / f"slide{asset.slide_num}.xml"
    slide_xml = create_slide_xml_with_svg(
        asset.slide_num,
        png_rid=asset.png_rid,
        svg_rid=active_svg_rid,
        width_emu=geometry.width_emu,
        height_emu=geometry.height_emu,
        transition=transition,
        transition_duration=transition_duration,
        auto_advance=auto_advance,
        use_compat_mode=(compatibility.use_compat_mode and slide_has_png),
        transition_xml_builder=transition_xml_builder,
    )
    slide_xml_path.write_text(slide_xml, encoding="utf-8")

    rels_dir = session.extract_dir / "ppt" / "slides" / "_rels"
    rels_dir.mkdir(exist_ok=True)
    rels_path = rels_dir / f"slide{asset.slide_num}.xml.rels"
    rels_xml = create_slide_rels_xml(
        png_rid=asset.png_rid,
        png_filename=asset.png_filename,
        svg_rid=active_svg_rid,
        svg_filename=asset.svg_filename,
        use_compat_mode=(compatibility.use_compat_mode and slide_has_png),
    )
    rels_path.write_text(rels_xml, encoding="utf-8")

    notes_content = ""
    if enable_notes:
        notes_content = notes_mapping.get(svg_path.stem, "")
        notes_text = markdown_to_plain_text(notes_content) if notes_content else ""
        write_notes_for_slide(
            session=session,
            rels_path=rels_path,
            slide_num=asset.slide_num,
            notes_text=notes_text,
            create_notes_slide_xml=create_notes_slide_xml,
            create_notes_slide_rels_xml=create_notes_slide_rels_xml,
        )

    return SlideExportResult(slide_has_png=slide_has_png, notes_content=notes_content)


def export_slides(
    request: NativeSvgExportRequest,
    session: ExportSession,
    geometry: ExportGeometry,
    compatibility: CompatibilityState,
    dependencies: NativeSvgExportDependencies,
) -> Tuple[int, bool]:
    """Export all slides into the extracted PPTX tree."""

    success_count = 0
    any_png_generated = False
    notes_mapping = request.notes or {}
    total = len(request.svg_files)

    for index, svg_path in enumerate(request.svg_files, 1):
        asset = build_slide_asset(index, compatibility.use_compat_mode)
        try:
            result = export_slide(
                session=session,
                svg_path=svg_path,
                asset=asset,
                geometry=geometry,
                compatibility=compatibility,
                transition=request.transition,
                transition_duration=request.transition_duration,
                auto_advance=request.auto_advance,
                enable_notes=request.enable_notes,
                notes_mapping=notes_mapping,
                transition_xml_builder=dependencies.transition_xml_builder,
                convert_svg_to_png=dependencies.convert_svg_to_png,
                create_slide_xml_with_svg=dependencies.create_slide_xml_with_svg,
                create_slide_rels_xml=dependencies.create_slide_rels_xml,
                markdown_to_plain_text=dependencies.markdown_to_plain_text,
                create_notes_slide_xml=dependencies.create_notes_slide_xml,
                create_notes_slide_rels_xml=dependencies.create_notes_slide_rels_xml,
                verbose=request.verbose,
                index=index,
                total=total,
            )
            any_png_generated = any_png_generated or result.slide_has_png

            if request.verbose:
                print_slide_result(
                    svg_path=svg_path,
                    result=result,
                    compatibility=compatibility,
                    enable_notes=request.enable_notes,
                    index=index,
                    total=total,
                )

            success_count += 1
        except Exception as exc:
            if request.verbose:
                print(f"  [{index}/{total}] {svg_path.name} - Error: {exc}")

    return success_count, any_png_generated


def export_presentation(
    request: NativeSvgExportRequest,
    dependencies: NativeSvgExportDependencies,
) -> bool:
    """Export a complete presentation from SVG inputs."""

    if not request.svg_files:
        print("Error: no SVG files found")
        return False

    renderer_name, renderer_status, renderer_hint = dependencies.get_png_renderer_info()
    compatibility = resolve_compatibility(
        use_compat_mode=request.use_compat_mode,
        renderer_name=renderer_name,
        renderer_status=renderer_status,
        renderer_hint=renderer_hint,
        png_renderer=dependencies.png_renderer,
    )

    geometry = resolve_geometry(
        svg_files=request.svg_files,
        canvas_format=request.canvas_format,
        verbose=request.verbose,
        detect_format_from_svg=dependencies.detect_format_from_svg,
        get_viewbox_dimensions=dependencies.get_viewbox_dimensions,
        get_slide_dimensions=dependencies.get_slide_dimensions,
        get_pixel_dimensions=dependencies.get_pixel_dimensions,
        canvas_formats=dependencies.canvas_formats,
    )

    if request.verbose:
        print_export_summary(
            geometry=geometry,
            svg_count=len(request.svg_files),
            compatibility=compatibility,
            transition=request.transition,
            transition_name=dependencies.resolve_transition_name(request.transition),
            enable_notes=request.enable_notes,
            notes=request.notes,
        )

    session = create_session(
        presentation_factory=dependencies.presentation_factory,
        svg_count=len(request.svg_files),
        width_emu=geometry.width_emu,
        height_emu=geometry.height_emu,
    )

    try:
        success_count, any_png_generated = export_slides(
            request=request,
            session=session,
            geometry=geometry,
            compatibility=compatibility,
            dependencies=dependencies,
        )
        update_content_types(
            extract_dir=session.extract_dir,
            any_png_generated=any_png_generated,
            enable_notes=request.enable_notes,
            slide_count=len(request.svg_files),
        )
        repack_pptx(session.extract_dir, request.output_path)

        if request.verbose:
            print_export_completion(
                output_path=request.output_path,
                success_count=success_count,
                total_count=len(request.svg_files),
                compatibility=compatibility,
                any_png_generated=any_png_generated,
                png_renderer=dependencies.png_renderer,
            )

        return success_count == len(request.svg_files)
    finally:
        cleanup_session(session)


def print_slide_result(
    svg_path: Path,
    result: SlideExportResult,
    compatibility: CompatibilityState,
    enable_notes: bool,
    index: int,
    total: int,
) -> None:
    """Print a per-slide export summary."""

    mode_str = " (PNG+SVG)" if (compatibility.use_compat_mode and result.slide_has_png) else " (SVG)"
    notes_str = " +Notes" if (enable_notes and bool(result.notes_content)) else ""
    print(f"  [{index}/{total}] {svg_path.name}{mode_str}{notes_str}")


def print_export_completion(
    output_path: Path,
    success_count: int,
    total_count: int,
    compatibility: CompatibilityState,
    any_png_generated: bool,
    png_renderer: Optional[str],
) -> None:
    """Print the final export summary."""

    print()
    print(f"[Done] Saved: {output_path}")
    print(f"  Success: {success_count}, Failed: {total_count - success_count}")
    if compatibility.use_compat_mode and any_png_generated:
        print("  Mode: Office compatibility mode")
        if png_renderer == "svglib" and compatibility.renderer_hint:
            print(f"  [Hint] {compatibility.renderer_hint}")


def repack_pptx(extract_dir: Path, output_path: Path) -> None:
    """Repack the extracted PPTX tree into the final file."""

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for file_path in extract_dir.rglob("*"):
            if file_path.is_file():
                archive.write(file_path, file_path.relative_to(extract_dir))
