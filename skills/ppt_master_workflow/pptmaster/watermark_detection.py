"""Provider-aware watermark risk detection for image assets."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, List, Optional

from .image_source_metadata import ImageSourceMetadata, build_sidecar_path, read_source_metadata
from .watermark_removal import GeminiWatermarkRemover, require_pillow_image

BLOCKED_GENERATED_PROVIDERS = {"gemini"}
SUPPORTED_DETECTION_STATUSES = ("clean", "suspicious", "blocked")


@dataclass(frozen=True)
class WatermarkDetectionResult:
    """Structured result for watermark risk assessment."""

    image_path: str
    sidecar_path: str
    metadata_present: bool
    status: str
    detector: str
    confidence: float
    reasons: List[str] = field(default_factory=list)
    source_type: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    expected_region: Optional[dict[str, int]] = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _build_expected_gemini_region(image_path: Path) -> Optional[dict[str, int]]:
    try:
        image_module = require_pillow_image()
        with image_module.open(image_path) as image:
            width, height = image.size
        config = GeminiWatermarkRemover.detect_watermark_config(width, height)
        position = GeminiWatermarkRemover.calculate_watermark_position(width, height, config)
        return {
            "x": position.x,
            "y": position.y,
            "width": position.width,
            "height": position.height,
            "logo_size": config.logo_size,
        }
    except Exception:
        return None


def _build_result(
    image_path: Path,
    *,
    metadata: Optional[ImageSourceMetadata],
    status: str,
    detector: str,
    confidence: float,
    reasons: List[str],
    expected_region: Optional[dict[str, int]] = None,
) -> WatermarkDetectionResult:
    return WatermarkDetectionResult(
        image_path=str(image_path),
        sidecar_path=str(build_sidecar_path(image_path)),
        metadata_present=metadata is not None,
        status=status,
        detector=detector,
        confidence=confidence,
        reasons=reasons,
        source_type=metadata.source_type if metadata else None,
        provider=metadata.provider if metadata else None,
        model=metadata.model if metadata else None,
        expected_region=expected_region,
    )


def detect_watermark_risk(
    image_path: str | Path,
    *,
    metadata: Optional[ImageSourceMetadata] = None,
) -> WatermarkDetectionResult:
    """Assess watermark risk using provenance-aware policy rules."""

    path = Path(image_path)
    resolved_metadata = metadata if metadata is not None else read_source_metadata(path)

    if resolved_metadata is None:
        return _build_result(
            path,
            metadata=None,
            status="suspicious",
            detector="metadata_presence",
            confidence=0.45,
            reasons=[
                "No image source metadata sidecar was found.",
                "Register provenance before allowing the asset into an automated workflow.",
            ],
        )

    if resolved_metadata.source_type == "generated" and resolved_metadata.provider in BLOCKED_GENERATED_PROVIDERS:
        reasons = [
            f"Generated asset provider '{resolved_metadata.provider}' is covered by a blocked watermark policy.",
            "Replace or regenerate the asset instead of editing the watermark away.",
        ]
        expected_region = _build_expected_gemini_region(path) if resolved_metadata.provider == "gemini" else None
        if expected_region is not None:
            reasons.append(
                "A known Gemini watermark footprint can be derived from the current image dimensions."
            )
        return _build_result(
            path,
            metadata=resolved_metadata,
            status="blocked",
            detector="provider_rule",
            confidence=0.98,
            reasons=reasons,
            expected_region=expected_region,
        )

    if resolved_metadata.source_type == "stock":
        if resolved_metadata.asset_id and resolved_metadata.origin_url and resolved_metadata.license_name:
            return _build_result(
                path,
                metadata=resolved_metadata,
                status="clean",
                detector="stock_provenance",
                confidence=0.82,
                reasons=[
                    "Stock asset provenance is complete enough for automated reuse.",
                    "Provider, asset identifier, origin URL, and license metadata are present.",
                ],
            )
        return _build_result(
            path,
            metadata=resolved_metadata,
            status="suspicious",
            detector="stock_provenance",
            confidence=0.68,
            reasons=[
                "Stock asset metadata is incomplete.",
                "Reacquire the official source file before use in delivery assets.",
            ],
        )

    if resolved_metadata.source_type == "user_upload":
        return _build_result(
            path,
            metadata=resolved_metadata,
            status="suspicious",
            detector="user_upload_review",
            confidence=0.55,
            reasons=[
                "User-uploaded assets require manual provenance review.",
                "No provider-backed source policy can safely clear this asset automatically.",
            ],
        )

    if resolved_metadata.source_type == "generated":
        if resolved_metadata.provider:
            return _build_result(
                path,
                metadata=resolved_metadata,
                status="clean",
                detector="provider_rule",
                confidence=0.70,
                reasons=[
                    f"Generated asset provider '{resolved_metadata.provider}' does not match a blocked watermark rule.",
                    "The asset remains traceable through stored provider metadata.",
                ],
            )
        return _build_result(
            path,
            metadata=resolved_metadata,
            status="suspicious",
            detector="provider_rule",
            confidence=0.57,
            reasons=[
                "Generated asset metadata is missing the provider name.",
                "Manual review is required before the asset can be routed safely.",
            ],
        )

    return _build_result(
        path,
        metadata=resolved_metadata,
        status="suspicious",
        detector="fallback_rule",
        confidence=0.40,
        reasons=[
            f"Unsupported or unknown source_type '{resolved_metadata.source_type}'.",
            "Manual review is required.",
        ],
    )


__all__ = [
    "BLOCKED_GENERATED_PROVIDERS",
    "SUPPORTED_DETECTION_STATUSES",
    "WatermarkDetectionResult",
    "detect_watermark_risk",
]
