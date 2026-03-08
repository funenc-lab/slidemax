"""Image source metadata helpers for provenance-aware asset workflows."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional, Sequence

METADATA_VERSION = 1
SOURCE_METADATA_SUFFIX = ".source.json"
SUPPORTED_SOURCE_TYPES = ("generated", "stock", "user_upload", "unknown")


@dataclass(frozen=True)
class ImageSourceMetadata:
    """Structured provenance metadata stored next to an image asset."""

    version: int = METADATA_VERSION
    local_path: str = ""
    source_type: str = "unknown"
    provider: Optional[str] = None
    model: Optional[str] = None
    asset_id: Optional[str] = None
    origin_url: Optional[str] = None
    license_name: Optional[str] = None
    license_url: Optional[str] = None
    creator_name: Optional[str] = None
    creator_url: Optional[str] = None
    prompt: Optional[str] = None
    negative_prompt: Optional[str] = None
    created_at: str = ""
    notes: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def now_utc_iso() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_source_type(source_type: Optional[str]) -> str:
    """Normalize and validate a source type token."""

    normalized = (source_type or "unknown").strip().lower()
    if normalized not in SUPPORTED_SOURCE_TYPES:
        supported = ", ".join(SUPPORTED_SOURCE_TYPES)
        raise ValueError(f"Unsupported source_type '{source_type}'. Supported: {supported}")
    return normalized


def _normalize_optional_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_tags(tags: Optional[Sequence[str] | str]) -> List[str]:
    if tags is None:
        return []
    if isinstance(tags, str):
        raw_values = [segment.strip() for segment in tags.split(",")]
    else:
        raw_values = [str(segment).strip() for segment in tags]
    return [value for value in raw_values if value]


def build_sidecar_path(image_path: str | Path) -> Path:
    """Return the sidecar metadata path for an image."""

    path = Path(image_path)
    return path.with_name(f"{path.name}{SOURCE_METADATA_SUFFIX}")


def _metadata_kwargs(
    *,
    image_path: str | Path,
    local_path: Optional[str] = None,
    source_type: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    asset_id: Optional[str] = None,
    origin_url: Optional[str] = None,
    license_name: Optional[str] = None,
    license_url: Optional[str] = None,
    creator_name: Optional[str] = None,
    creator_url: Optional[str] = None,
    prompt: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    created_at: Optional[str] = None,
    notes: Optional[str] = None,
    tags: Optional[Sequence[str] | str] = None,
) -> dict[str, Any]:
    return {
        "version": METADATA_VERSION,
        "local_path": local_path or str(Path(image_path)),
        "source_type": normalize_source_type(source_type),
        "provider": _normalize_optional_text(provider.lower()) if provider else None,
        "model": _normalize_optional_text(model),
        "asset_id": _normalize_optional_text(asset_id),
        "origin_url": _normalize_optional_text(origin_url),
        "license_name": _normalize_optional_text(license_name),
        "license_url": _normalize_optional_text(license_url),
        "creator_name": _normalize_optional_text(creator_name),
        "creator_url": _normalize_optional_text(creator_url),
        "prompt": _normalize_optional_text(prompt),
        "negative_prompt": _normalize_optional_text(negative_prompt),
        "created_at": _normalize_optional_text(created_at) or now_utc_iso(),
        "notes": _normalize_optional_text(notes),
        "tags": _normalize_tags(tags),
    }


def metadata_from_dict(data: dict[str, Any]) -> ImageSourceMetadata:
    """Build metadata from an untrusted dict payload."""

    return ImageSourceMetadata(
        version=int(data.get("version", METADATA_VERSION)),
        local_path=str(data.get("local_path") or ""),
        source_type=normalize_source_type(data.get("source_type")),
        provider=_normalize_optional_text(data.get("provider")),
        model=_normalize_optional_text(data.get("model")),
        asset_id=_normalize_optional_text(data.get("asset_id")),
        origin_url=_normalize_optional_text(data.get("origin_url")),
        license_name=_normalize_optional_text(data.get("license_name")),
        license_url=_normalize_optional_text(data.get("license_url")),
        creator_name=_normalize_optional_text(data.get("creator_name")),
        creator_url=_normalize_optional_text(data.get("creator_url")),
        prompt=_normalize_optional_text(data.get("prompt")),
        negative_prompt=_normalize_optional_text(data.get("negative_prompt")),
        created_at=_normalize_optional_text(data.get("created_at")) or now_utc_iso(),
        notes=_normalize_optional_text(data.get("notes")),
        tags=_normalize_tags(data.get("tags")),
    )


def build_generated_image_metadata(
    image_path: str | Path,
    *,
    provider: str,
    model: Optional[str],
    prompt: str,
    negative_prompt: Optional[str] = None,
    origin_url: Optional[str] = None,
    local_path: Optional[str] = None,
    notes: Optional[str] = None,
    tags: Optional[Sequence[str] | str] = None,
) -> ImageSourceMetadata:
    """Build metadata for an AI-generated image."""

    return metadata_from_dict(
        _metadata_kwargs(
            image_path=image_path,
            local_path=local_path,
            source_type="generated",
            provider=provider,
            model=model,
            origin_url=origin_url,
            prompt=prompt,
            negative_prompt=negative_prompt,
            notes=notes,
            tags=tags,
        )
    )


def build_stock_image_metadata(
    image_path: str | Path,
    *,
    provider: str,
    origin_url: str,
    asset_id: Optional[str] = None,
    license_name: Optional[str] = None,
    license_url: Optional[str] = None,
    creator_name: Optional[str] = None,
    creator_url: Optional[str] = None,
    local_path: Optional[str] = None,
    notes: Optional[str] = None,
    tags: Optional[Sequence[str] | str] = None,
) -> ImageSourceMetadata:
    """Build metadata for a stock image asset."""

    return metadata_from_dict(
        _metadata_kwargs(
            image_path=image_path,
            local_path=local_path,
            source_type="stock",
            provider=provider,
            asset_id=asset_id,
            origin_url=origin_url,
            license_name=license_name,
            license_url=license_url,
            creator_name=creator_name,
            creator_url=creator_url,
            notes=notes,
            tags=tags,
        )
    )


def read_source_metadata(image_path: str | Path) -> Optional[ImageSourceMetadata]:
    """Read sidecar metadata for an image if present."""

    sidecar_path = build_sidecar_path(image_path)
    if not sidecar_path.exists():
        return None
    payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid metadata format: {sidecar_path}")
    return metadata_from_dict(payload)


def write_source_metadata(image_path: str | Path, metadata: ImageSourceMetadata) -> Path:
    """Persist metadata next to the image asset and return the sidecar path."""

    sidecar_path = build_sidecar_path(image_path)
    sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    sidecar_path.write_text(json.dumps(metadata.as_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return sidecar_path


def upsert_source_metadata(
    image_path: str | Path,
    *,
    source_type: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    asset_id: Optional[str] = None,
    origin_url: Optional[str] = None,
    license_name: Optional[str] = None,
    license_url: Optional[str] = None,
    creator_name: Optional[str] = None,
    creator_url: Optional[str] = None,
    prompt: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    created_at: Optional[str] = None,
    notes: Optional[str] = None,
    tags: Optional[Sequence[str] | str] = None,
    local_path: Optional[str] = None,
) -> ImageSourceMetadata:
    """Create or update sidecar metadata while preserving unspecified fields."""

    existing = read_source_metadata(image_path)
    merged = dict(existing.as_dict()) if existing else {}
    merged.update(
        {
            key: value
            for key, value in _metadata_kwargs(
                image_path=image_path,
                local_path=local_path,
                source_type=source_type or (existing.source_type if existing else "unknown"),
                provider=provider if provider is not None else (existing.provider if existing else None),
                model=model if model is not None else (existing.model if existing else None),
                asset_id=asset_id if asset_id is not None else (existing.asset_id if existing else None),
                origin_url=origin_url if origin_url is not None else (existing.origin_url if existing else None),
                license_name=license_name if license_name is not None else (existing.license_name if existing else None),
                license_url=license_url if license_url is not None else (existing.license_url if existing else None),
                creator_name=creator_name if creator_name is not None else (existing.creator_name if existing else None),
                creator_url=creator_url if creator_url is not None else (existing.creator_url if existing else None),
                prompt=prompt if prompt is not None else (existing.prompt if existing else None),
                negative_prompt=negative_prompt if negative_prompt is not None else (existing.negative_prompt if existing else None),
                created_at=created_at if created_at is not None else (existing.created_at if existing else None),
                notes=notes if notes is not None else (existing.notes if existing else None),
                tags=tags if tags is not None else (existing.tags if existing else None),
            ).items()
            if value is not None or key in {"version", "local_path", "source_type", "created_at", "tags"}
        }
    )
    metadata = metadata_from_dict(merged)
    write_source_metadata(image_path, metadata)
    return metadata


def write_generated_image_metadata(
    image_path: str | Path,
    *,
    provider: str,
    model: Optional[str],
    prompt: str,
    negative_prompt: Optional[str] = None,
    origin_url: Optional[str] = None,
    local_path: Optional[str] = None,
    notes: Optional[str] = None,
    tags: Optional[Sequence[str] | str] = None,
) -> Path:
    """Write generated-image provenance metadata and return the sidecar path."""

    metadata = build_generated_image_metadata(
        image_path,
        provider=provider,
        model=model,
        prompt=prompt,
        negative_prompt=negative_prompt,
        origin_url=origin_url,
        local_path=local_path,
        notes=notes,
        tags=tags,
    )
    return write_source_metadata(image_path, metadata)


def write_stock_image_metadata(
    image_path: str | Path,
    *,
    provider: str,
    origin_url: str,
    asset_id: Optional[str] = None,
    license_name: Optional[str] = None,
    license_url: Optional[str] = None,
    creator_name: Optional[str] = None,
    creator_url: Optional[str] = None,
    local_path: Optional[str] = None,
    notes: Optional[str] = None,
    tags: Optional[Sequence[str] | str] = None,
) -> Path:
    """Write stock-image provenance metadata and return the sidecar path."""

    metadata = build_stock_image_metadata(
        image_path,
        provider=provider,
        origin_url=origin_url,
        asset_id=asset_id,
        license_name=license_name,
        license_url=license_url,
        creator_name=creator_name,
        creator_url=creator_url,
        local_path=local_path,
        notes=notes,
        tags=tags,
    )
    return write_source_metadata(image_path, metadata)


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for manual source metadata registration."""

    parser = argparse.ArgumentParser(description="Register or inspect image source metadata sidecars.")
    parser.add_argument("image_path", type=Path, help="Image file path.")
    parser.add_argument("--show", action="store_true", help="Print metadata instead of writing it.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    parser.add_argument("--source-type", choices=SUPPORTED_SOURCE_TYPES, default=None, help="Source type.")
    parser.add_argument("--provider", default=None, help="Source provider.")
    parser.add_argument("--model", default=None, help="Model or variant name.")
    parser.add_argument("--asset-id", default=None, help="Provider-side asset identifier.")
    parser.add_argument("--origin-url", default=None, help="Original source URL.")
    parser.add_argument("--license-name", default=None, help="License name.")
    parser.add_argument("--license-url", default=None, help="License URL.")
    parser.add_argument("--creator-name", default=None, help="Creator or photographer name.")
    parser.add_argument("--creator-url", default=None, help="Creator profile URL.")
    parser.add_argument("--prompt", default=None, help="Prompt used for image generation.")
    parser.add_argument("--negative-prompt", default=None, help="Negative prompt used for image generation.")
    parser.add_argument("--notes", default=None, help="Free-form notes.")
    parser.add_argument("--tags", default=None, help="Comma-separated tags.")
    parser.add_argument("--created-at", default=None, help="Explicit creation timestamp.")
    parser.add_argument("--local-path", default=None, help="Logical local path stored in metadata.")
    return parser


def _format_show_payload(image_path: Path, metadata: Optional[ImageSourceMetadata]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "image_path": str(image_path),
        "sidecar_path": str(build_sidecar_path(image_path)),
        "metadata_present": metadata is not None,
    }
    if metadata is not None:
        payload["metadata"] = metadata.as_dict()
    return payload


def run_cli(argv: Optional[Sequence[str]] = None) -> int:
    """Execute the source metadata CLI entrypoint."""

    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.show:
        metadata = read_source_metadata(args.image_path)
        payload = _format_show_payload(args.image_path, metadata)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"Image: {payload['image_path']}")
            print(f"Sidecar: {payload['sidecar_path']}")
            print(f"Metadata present: {payload['metadata_present']}")
        return 0 if metadata is not None else 1

    metadata = upsert_source_metadata(
        args.image_path,
        source_type=args.source_type,
        provider=args.provider,
        model=args.model,
        asset_id=args.asset_id,
        origin_url=args.origin_url,
        license_name=args.license_name,
        license_url=args.license_url,
        creator_name=args.creator_name,
        creator_url=args.creator_url,
        prompt=args.prompt,
        negative_prompt=args.negative_prompt,
        created_at=args.created_at,
        notes=args.notes,
        tags=args.tags,
        local_path=args.local_path,
    )
    sidecar_path = build_sidecar_path(args.image_path)
    if args.json:
        print(json.dumps({"sidecar_path": str(sidecar_path), "metadata": metadata.as_dict()}, ensure_ascii=False, indent=2))
    else:
        print(f"Registered image source metadata: {sidecar_path}")
    return 0


def main() -> int:
    return run_cli()


__all__ = [
    "METADATA_VERSION",
    "SOURCE_METADATA_SUFFIX",
    "SUPPORTED_SOURCE_TYPES",
    "ImageSourceMetadata",
    "build_generated_image_metadata",
    "build_parser",
    "build_sidecar_path",
    "build_stock_image_metadata",
    "main",
    "metadata_from_dict",
    "normalize_source_type",
    "now_utc_iso",
    "read_source_metadata",
    "run_cli",
    "upsert_source_metadata",
    "write_generated_image_metadata",
    "write_source_metadata",
    "write_stock_image_metadata",
]
