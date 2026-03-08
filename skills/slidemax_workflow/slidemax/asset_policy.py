"""Asset policy routing built on top of provenance and watermark risk signals."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, List, Optional, Sequence

from .image_source_metadata import read_source_metadata
from .watermark_detection import WatermarkDetectionResult, detect_watermark_risk

SUPPORTED_ACTIONS = ("allow", "register", "reacquire", "regenerate", "review", "block")
SUPPORTED_FAIL_LEVELS = ("suspicious", "blocked")


@dataclass(frozen=True)
class AssetPolicyDecision:
    """Policy decision for a single image asset."""

    image_path: str
    sidecar_path: str
    metadata_present: bool
    source_type: Optional[str]
    provider: Optional[str]
    model: Optional[str]
    watermark_status: str
    detector: str
    confidence: float
    recommended_action: str
    reasons: List[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def recommend_action(detection: WatermarkDetectionResult) -> str:
    """Map watermark risk signals to the next workflow action."""

    if detection.status == "blocked":
        if detection.source_type == "generated":
            return "regenerate"
        if detection.source_type == "stock":
            return "reacquire"
        return "block"

    if detection.status == "suspicious":
        if not detection.metadata_present:
            return "register"
        if detection.source_type == "stock":
            return "reacquire"
        if detection.source_type == "generated" and detection.provider:
            return "regenerate"
        if detection.source_type == "user_upload":
            return "review"
        return "review"

    if detection.metadata_present:
        return "allow"
    return "register"


def audit_image_asset(image_path: str | Path) -> AssetPolicyDecision:
    """Audit an image and return the policy decision for downstream automation."""

    path = Path(image_path)
    detection = detect_watermark_risk(path, metadata=read_source_metadata(path))
    action = recommend_action(detection)
    return AssetPolicyDecision(
        image_path=detection.image_path,
        sidecar_path=detection.sidecar_path,
        metadata_present=detection.metadata_present,
        source_type=detection.source_type,
        provider=detection.provider,
        model=detection.model,
        watermark_status=detection.status,
        detector=detection.detector,
        confidence=detection.confidence,
        recommended_action=action,
        reasons=detection.reasons,
    )


def _should_fail(decisions: Sequence[AssetPolicyDecision], fail_on: Optional[str]) -> bool:
    if fail_on is None:
        return False
    if fail_on == "blocked":
        return any(decision.watermark_status == "blocked" for decision in decisions)
    return any(decision.watermark_status in {"suspicious", "blocked"} for decision in decisions)


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for asset policy auditing."""

    parser = argparse.ArgumentParser(description="Audit image assets for provenance and watermark policy routing.")
    parser.add_argument("image_paths", nargs="+", type=Path, help="Image paths to audit.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    parser.add_argument(
        "--fail-on",
        choices=SUPPORTED_FAIL_LEVELS,
        default=None,
        help="Return exit code 2 when the watermark status reaches the selected level.",
    )
    return parser


def _print_text(decision: AssetPolicyDecision) -> None:
    print(f"Image: {decision.image_path}")
    print(f"Sidecar: {decision.sidecar_path}")
    print(f"Metadata present: {decision.metadata_present}")
    print(f"Watermark status: {decision.watermark_status}")
    print(f"Recommended action: {decision.recommended_action}")
    for reason in decision.reasons:
        print(f"- {reason}")


def run_cli(argv: Optional[Sequence[str]] = None) -> int:
    """Execute the asset policy audit CLI."""

    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    decisions = [audit_image_asset(path) for path in args.image_paths]
    if args.json:
        payload: Any
        if len(decisions) == 1:
            payload = decisions[0].as_dict()
        else:
            payload = [decision.as_dict() for decision in decisions]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for index, decision in enumerate(decisions):
            if index:
                print()
            _print_text(decision)

    return 2 if _should_fail(decisions, args.fail_on) else 0


def main() -> int:
    return run_cli()


__all__ = [
    "AssetPolicyDecision",
    "SUPPORTED_ACTIONS",
    "SUPPORTED_FAIL_LEVELS",
    "audit_image_asset",
    "build_parser",
    "main",
    "recommend_action",
    "run_cli",
]
