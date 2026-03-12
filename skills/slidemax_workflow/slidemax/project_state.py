"""Project stage state helpers for SlideMax workflow projects."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

STATE_FILE_NAME = "project_state.json"
STATE_SCHEMA_VERSION = 1

STAGE_ORDER: Sequence[str] = (
    "project_initialized",
    "strategy_ready",
    "images_ready",
    "svg_ready",
    "notes_ready",
    "notes_split",
    "finalized",
    "exported",
    "validated",
)

REQUIRED_PATHS: Sequence[str] = (
    "README.md",
    "svg_output",
    "svg_final",
    "images",
    "notes",
    "templates",
)

SPEC_FILENAMES: Sequence[str] = (
    "design_specification.md",
    "设计规范与内容大纲.md",
    "设计规范.md",
)


def _utc_now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def project_state_path(project_path: Path) -> Path:
    """Return the canonical project state path."""

    return project_path / STATE_FILE_NAME


def _list_svg_stems(project_path: Path, directory_name: str) -> List[str]:
    directory = project_path / directory_name
    if not directory.exists():
        return []
    return sorted(path.stem for path in directory.glob("*.svg"))


def _list_note_stems(project_path: Path) -> List[str]:
    notes_dir = project_path / "notes"
    if not notes_dir.exists():
        return []
    return sorted(path.stem for path in notes_dir.glob("*.md") if path.name != "total.md")


def _list_project_images(project_path: Path) -> List[str]:
    images_dir = project_path / "images"
    if not images_dir.exists():
        return []

    matches: List[str] = []
    for path in images_dir.rglob("*"):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}:
            matches.append(str(path.relative_to(project_path)))
    return sorted(matches)


def _find_design_spec(project_path: Path) -> Optional[str]:
    for filename in SPEC_FILENAMES:
        path = project_path / filename
        if path.exists():
            return filename
    return None


def _artifact_signature(signals: Dict[str, object]) -> Dict[str, object]:
    return {
        "svg_output": list(signals["svg_output_stems"]),
        "svg_final": list(signals["svg_final_stems"]),
        "notes_split": list(signals["note_stems"]),
        "notes_total_exists": bool(signals["notes_total_exists"]),
        "pptx_files": list(signals["pptx_files"]),
        "design_spec": signals["design_spec"],
    }


def load_project_state(project_path: Path) -> Dict[str, object]:
    """Load an existing state file, returning an empty payload on failure."""

    state_path = project_state_path(project_path)
    if not state_path.exists():
        return {}

    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    if not isinstance(payload, dict):
        return {}
    return payload


def write_project_state(project_path: Path, payload: Dict[str, object]) -> Path:
    """Persist the project state file."""

    state_path = project_state_path(project_path)
    state_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return state_path


def _detect_signals(project_path: Path) -> Dict[str, object]:
    existing_paths = {item.name for item in project_path.iterdir()} if project_path.exists() and project_path.is_dir() else set()
    design_spec = _find_design_spec(project_path)
    project_images = _list_project_images(project_path)
    image_prompts = project_path / "images" / "image_prompts.md"
    stock_manifest = project_path / "images" / "stock" / "manifest.json"

    return {
        "project_exists": project_path.exists() and project_path.is_dir(),
        "existing_paths": existing_paths,
        "design_spec": design_spec,
        "svg_output_stems": _list_svg_stems(project_path, "svg_output"),
        "svg_final_stems": _list_svg_stems(project_path, "svg_final"),
        "note_stems": _list_note_stems(project_path),
        "notes_total_exists": (project_path / "notes" / "total.md").exists(),
        "pptx_files": sorted(path.name for path in project_path.glob("*.pptx")),
        "project_images": project_images,
        "image_prompts_exists": image_prompts.exists(),
        "stock_manifest_exists": stock_manifest.exists(),
    }


def _build_stage_map(
    project_path: Path,
    signals: Dict[str, object],
    *,
    last_validation: Optional[Dict[str, object]],
) -> Tuple[List[Dict[str, str]], List[str], List[str]]:
    svg_output_stems = list(signals["svg_output_stems"])
    svg_final_stems = set(signals["svg_final_stems"])
    note_stems = set(signals["note_stems"])
    notes_total_exists = bool(signals["notes_total_exists"])
    pptx_files = list(signals["pptx_files"])
    design_spec = signals["design_spec"]
    images_ready = bool(signals["project_images"] or signals["image_prompts_exists"] or signals["stock_manifest_exists"])

    missing_paths = [name for name in REQUIRED_PATHS if name not in signals["existing_paths"]]
    notes_split_complete = bool(svg_output_stems) and set(svg_output_stems).issubset(note_stems)
    finalized_complete = bool(svg_output_stems) and set(svg_output_stems).issubset(svg_final_stems)

    validation_signature = _artifact_signature(signals)
    validation_is_fresh = bool(
        last_validation
        and last_validation.get("status") == "passed"
        and last_validation.get("artifact_signature") == validation_signature
    )

    stages: List[Dict[str, str]] = []
    blocking_issues: List[str] = []
    warnings: List[str] = []

    if not signals["project_exists"]:
        blocking_issues.append(f"Project path does not exist: {project_path}")

    if missing_paths:
        blocking_issues.append("Project is missing required path(s): " + ", ".join(sorted(missing_paths)))

    if pptx_files and not finalized_complete:
        blocking_issues.append("Stage 'exported' is ahead of 'finalized'; regenerate finalized SVG assets.")

    if pptx_files and not notes_split_complete:
        blocking_issues.append("Stage 'exported' is ahead of 'notes_split'; split per-slide notes before export.")

    if svg_final_stems and not svg_output_stems:
        blocking_issues.append("Stage 'finalized' is ahead of 'svg_ready'; raw SVG output is missing.")

    if note_stems and not svg_output_stems:
        blocking_issues.append("Stage 'notes_split' is ahead of 'svg_ready'; raw SVG output is missing.")

    if svg_output_stems and not notes_total_exists and not note_stems:
        warnings.append("Slides exist under svg_output/ but notes/total.md has not been created yet.")

    if notes_total_exists and not notes_split_complete:
        warnings.append("notes/total.md exists, but per-slide notes have not been fully split yet.")

    if svg_output_stems and not finalized_complete and not pptx_files:
        warnings.append("Slide SVG files exist, but finalized SVG output is not complete yet.")

    if not design_spec:
        warnings.append("No design specification file was found yet.")

    stages.append(
        {
            "name": "project_initialized",
            "status": "completed" if not missing_paths and signals["project_exists"] else "pending",
            "detail": "Project skeleton exists." if not missing_paths and signals["project_exists"] else "Create the project skeleton first.",
        }
    )
    stages.append(
        {
            "name": "strategy_ready",
            "status": "completed" if design_spec else "pending",
            "detail": f"Using {design_spec}." if design_spec else "Add a design specification markdown file.",
        }
    )
    stages.append(
        {
            "name": "images_ready",
            "status": "completed" if images_ready else "pending",
            "detail": "Image prompts or project-local images are present." if images_ready else "No image plan or local images detected yet.",
        }
    )
    stages.append(
        {
            "name": "svg_ready",
            "status": "completed" if svg_output_stems else "pending",
            "detail": f"Found {len(svg_output_stems)} raw slide SVG file(s)." if svg_output_stems else "Generate slide SVG files into svg_output/.",
        }
    )
    stages.append(
        {
            "name": "notes_ready",
            "status": "completed" if notes_total_exists else "pending",
            "detail": "notes/total.md exists." if notes_total_exists else "Create notes/total.md for the generated slides.",
        }
    )
    stages.append(
        {
            "name": "notes_split",
            "status": "completed" if notes_split_complete else "pending",
            "detail": "Per-slide notes cover every slide." if notes_split_complete else "Run total_md_split after notes/total.md is ready.",
        }
    )
    stages.append(
        {
            "name": "finalized",
            "status": "completed" if finalized_complete else "pending",
            "detail": "svg_final/ covers every raw slide." if finalized_complete else "Run finalize_svg to populate svg_final/.",
        }
    )
    stages.append(
        {
            "name": "exported",
            "status": "completed" if pptx_files else "pending",
            "detail": f"Found {len(pptx_files)} PPTX file(s)." if pptx_files else "Run svg_to_pptx -s final to export the deck.",
        }
    )
    stages.append(
        {
            "name": "validated",
            "status": "completed" if validation_is_fresh else "pending",
            "detail": "Delivery validation is current." if validation_is_fresh else "Run project_manager validate after export artifacts stop changing.",
        }
    )

    return stages, blocking_issues, warnings


def _select_current_stage(stages: Sequence[Dict[str, str]]) -> str:
    completed = [stage["name"] for stage in stages if stage["status"] == "completed"]
    if not completed:
        return "project_initialized"
    return completed[-1]


def _next_step(stages: Sequence[Dict[str, str]], blocking_issues: Sequence[str]) -> str:
    if blocking_issues:
        return "Resolve the blocking audit issues before moving to the next stage."

    for stage in stages:
        if stage["status"] != "completed":
            return stage["detail"]
    return "Project is ready for delivery."


def build_project_state(
    project_path: Path,
    *,
    last_command_name: Optional[str] = None,
    validation_result: Optional[Dict[str, object]] = None,
) -> Dict[str, object]:
    """Build a machine-readable project state payload from current project artifacts."""

    existing_state = load_project_state(project_path)
    signals = _detect_signals(project_path)
    artifact_signature = _artifact_signature(signals)

    last_validation = existing_state.get("last_validation")
    if validation_result is not None:
        last_validation = {
            "status": validation_result["status"],
            "validated_at": _utc_now(),
            "errors": int(validation_result.get("errors", 0)),
            "warnings": int(validation_result.get("warnings", 0)),
            "artifact_signature": artifact_signature,
        }

    stages, blocking_issues, warnings = _build_stage_map(
        project_path,
        signals,
        last_validation=last_validation if isinstance(last_validation, dict) else None,
    )

    last_command = existing_state.get("last_command") if isinstance(existing_state.get("last_command"), dict) else {}
    if last_command_name:
        last_command = {
            "name": last_command_name,
            "executed_at": _utc_now(),
        }

    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "project_path": str(project_path),
        "current_stage": _select_current_stage(stages),
        "next_step": _next_step(stages, blocking_issues),
        "blocking_issues": blocking_issues,
        "warnings": warnings,
        "stages": stages,
        "artifacts": {
            "design_spec": signals["design_spec"],
            "svg_output_count": len(signals["svg_output_stems"]),
            "svg_final_count": len(signals["svg_final_stems"]),
            "notes_split_count": len(signals["note_stems"]),
            "notes_total_exists": bool(signals["notes_total_exists"]),
            "pptx_count": len(signals["pptx_files"]),
            "project_image_count": len(signals["project_images"]),
        },
        "last_command": last_command,
        "last_validation": last_validation if isinstance(last_validation, dict) else None,
    }


__all__ = [
    "STATE_FILE_NAME",
    "STAGE_ORDER",
    "build_project_state",
    "load_project_state",
    "project_state_path",
    "write_project_state",
]
