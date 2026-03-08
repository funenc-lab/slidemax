"""Shared stock image source registry, manifest helpers, and CLI orchestration for PPT Master."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

MANIFEST_VERSION = 1
DEFAULT_STOCK_DIRNAME = "stock"
STOCK_ROOT_ENV = "PPTMASTER_STOCK_ROOT_DIR"
SUPPORTED_PROVIDERS = ("unsplash", "pexels", "pixabay")


class StockSourceError(RuntimeError):
    """Raised when stock source registration fails."""


@dataclass(frozen=True)
class StockProvider:
    """Registry entry for a supported stock provider."""

    name: str
    display_name: str
    homepage_url: str
    license_name: str
    license_url: str
    commercial_use_allowed: bool
    attribution_required: bool
    restriction_notes: str
    verification_note: str


@dataclass(frozen=True)
class StockImageRecord:
    """Manifest record for a stock image saved into a project."""

    filename: str
    local_path: str
    source_type: str = "stock"
    source_provider: str = ""
    source_id: Optional[str] = None
    source_url: str = ""
    download_url: Optional[str] = None
    creator_name: Optional[str] = None
    creator_url: Optional[str] = None
    license_name: str = ""
    license_url: str = ""
    commercial_use_allowed: bool = False
    attribution_required: bool = False
    restriction_notes: str = ""
    verification_note: str = ""
    downloaded_at: str = ""
    keywords: List[str] = field(default_factory=list)
    notes: Optional[str] = None


@dataclass(frozen=True)
class RegisterStockRequest:
    project_dir: Path
    provider_name: str
    source_url: str
    source_id: Optional[str] = None
    download_url: Optional[str] = None
    local_file: Optional[Path] = None
    local_path: Optional[Path] = None
    filename: Optional[str] = None
    creator_name: Optional[str] = None
    creator_url: Optional[str] = None
    license_name: Optional[str] = None
    license_url: Optional[str] = None
    commercial_use_allowed: Optional[bool] = None
    attribution_required: Optional[bool] = None
    restriction_notes: Optional[str] = None
    verification_note: Optional[str] = None
    keywords: Optional[str] = None
    notes: Optional[str] = None


@dataclass(frozen=True)
class DownloadStockRequest:
    project_dir: Path
    provider_name: str
    source_url: str
    download_url: str
    source_id: Optional[str] = None
    filename: Optional[str] = None
    creator_name: Optional[str] = None
    creator_url: Optional[str] = None
    license_name: Optional[str] = None
    license_url: Optional[str] = None
    commercial_use_allowed: Optional[bool] = None
    attribution_required: Optional[bool] = None
    restriction_notes: Optional[str] = None
    verification_note: Optional[str] = None
    keywords: Optional[str] = None
    notes: Optional[str] = None
    timeout_seconds: int = 60


PROVIDER_REGISTRY: Dict[str, StockProvider] = {
    "unsplash": StockProvider(
        name="unsplash",
        display_name="Unsplash",
        homepage_url="https://unsplash.com",
        license_name="Unsplash License",
        license_url="https://unsplash.com/license",
        commercial_use_allowed=True,
        attribution_required=False,
        restriction_notes=(
            "Do not sell images without significant modification. "
            "Do not compile images to replicate a similar or competing service. "
            "Review brand, artwork, and identifiable person restrictions before use."
        ),
        verification_note="Verify the current license terms on the official license page before release.",
    ),
    "pexels": StockProvider(
        name="pexels",
        display_name="Pexels",
        homepage_url="https://www.pexels.com",
        license_name="Pexels License",
        license_url="https://www.pexels.com/license/",
        commercial_use_allowed=True,
        attribution_required=False,
        restriction_notes=(
            "Do not sell unaltered copies. Do not imply endorsement by depicted people or brands. "
            "Do not redistribute content on another stock or wallpaper platform."
        ),
        verification_note="Verify the current license terms on the official license page before release.",
    ),
    "pixabay": StockProvider(
        name="pixabay",
        display_name="Pixabay",
        homepage_url="https://pixabay.com",
        license_name="Pixabay Content License",
        license_url="https://pixabay.com/service/license-summary/",
        commercial_use_allowed=True,
        attribution_required=False,
        restriction_notes=(
            "Do not sell or distribute the content on a standalone basis. "
            "Review trademark, brand, artwork, and personality rights before use."
        ),
        verification_note="Only the full content license is legally binding. Review the official terms before release.",
    ),
}


def now_utc_iso() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_provider(name: str) -> str:
    """Normalize and validate a provider name."""

    normalized = (name or "").strip().lower()
    if normalized not in PROVIDER_REGISTRY:
        supported = ", ".join(sorted(PROVIDER_REGISTRY))
        raise ValueError(f"Unsupported stock provider '{name}'. Supported: {supported}")
    return normalized


def get_provider(name: str) -> StockProvider:
    """Return provider metadata for a supported provider."""

    return PROVIDER_REGISTRY[normalize_provider(name)]


def list_providers() -> List[StockProvider]:
    """Return all supported providers in sorted order."""

    return [PROVIDER_REGISTRY[name] for name in sorted(PROVIDER_REGISTRY)]


def provider_choices() -> List[str]:
    """Return provider names for CLI choices."""

    return [provider.name for provider in list_providers()]


def stock_dir(project_dir: Path) -> Path:
    """Return the stock asset directory for a project."""

    override = os.environ.get(STOCK_ROOT_ENV)
    if override:
        configured = Path(override).expanduser()
        if configured.is_absolute():
            return configured
        return Path(project_dir) / configured
    return Path(project_dir) / "images" / DEFAULT_STOCK_DIRNAME


def manifest_path(project_dir: Path) -> Path:
    """Return the manifest path for a project."""

    return stock_dir(project_dir) / "manifest.json"


def ensure_stock_dir(project_dir: Path) -> Path:
    """Create the stock directory for a project if needed."""

    directory = stock_dir(project_dir)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _default_manifest() -> dict:
    return {
        "version": MANIFEST_VERSION,
        "updated_at": None,
        "images": [],
    }


def load_manifest(project_dir: Path) -> dict:
    """Load the stock manifest or return an empty manifest structure."""

    path = manifest_path(project_dir)
    if not path.exists():
        return _default_manifest()
    data = json.loads(path.read_text(encoding="utf-8"))
    if "images" not in data or not isinstance(data["images"], list):
        raise StockSourceError(f"Invalid manifest format: {path}")
    if "version" not in data:
        data["version"] = MANIFEST_VERSION
    return data


def save_manifest(project_dir: Path, manifest: dict) -> Path:
    """Persist the stock manifest to disk."""

    path = manifest_path(project_dir)
    ensure_stock_dir(project_dir)
    manifest["version"] = MANIFEST_VERSION
    manifest["updated_at"] = now_utc_iso()
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _relative_to_project(project_dir: Path, path: Path) -> str:
    return path.resolve().relative_to(project_dir.resolve()).as_posix()


def _copy_local_file(project_dir: Path, local_file: Path, filename: Optional[str]) -> Path:
    source = local_file.expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Local file not found: {local_file}")

    destination_dir = ensure_stock_dir(project_dir)
    destination_name = filename or source.name
    destination = destination_dir / destination_name
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return destination


def _resolve_existing_local_path(project_dir: Path, local_path: Path) -> Path:
    candidate = local_path.expanduser()
    if not candidate.is_absolute():
        candidate = Path(project_dir) / candidate
    candidate = candidate.resolve()
    if not candidate.is_file():
        raise FileNotFoundError(f"Local path not found: {local_path}")
    if project_dir.resolve() not in candidate.parents and candidate != project_dir.resolve():
        raise StockSourceError("Existing local_path must be inside the project directory.")
    return candidate


def _normalize_keywords(raw_keywords: Optional[str]) -> List[str]:
    if not raw_keywords:
        return []
    return [item.strip() for item in raw_keywords.split(",") if item.strip()]


def _filename_from_url(url: str, fallback: str = "downloaded_image") -> str:
    from urllib.parse import urlparse

    parsed = urlparse(url)
    candidate = Path(parsed.path).name
    return candidate or fallback


def download_to_stock(
    project_dir: Path,
    url: str,
    filename: Optional[str] = None,
    timeout_seconds: int = 60,
) -> Path:
    """Download a stock image into the project stock directory."""

    import requests

    destination_dir = ensure_stock_dir(project_dir)
    resolved_filename = filename or _filename_from_url(url)
    destination = destination_dir / resolved_filename

    response = requests.get(url, timeout=timeout_seconds)
    response.raise_for_status()
    destination.write_bytes(response.content)
    return destination


def build_record(
    *,
    project_dir: Path,
    provider_name: str,
    source_url: str,
    local_file: Optional[Path] = None,
    local_path: Optional[Path] = None,
    filename: Optional[str] = None,
    source_id: Optional[str] = None,
    download_url: Optional[str] = None,
    creator_name: Optional[str] = None,
    creator_url: Optional[str] = None,
    license_name: Optional[str] = None,
    license_url: Optional[str] = None,
    commercial_use_allowed: Optional[bool] = None,
    attribution_required: Optional[bool] = None,
    restriction_notes: Optional[str] = None,
    verification_note: Optional[str] = None,
    keywords: Optional[str] = None,
    notes: Optional[str] = None,
) -> StockImageRecord:
    """Build a stock image record from CLI-style inputs."""

    project_dir = Path(project_dir).resolve()
    provider = get_provider(provider_name)

    if not source_url:
        raise ValueError("source_url is required for stock image registration.")
    if bool(local_file) == bool(local_path):
        raise ValueError("Provide exactly one of local_file or local_path.")

    if local_file:
        final_local_path = _copy_local_file(project_dir, Path(local_file), filename)
    else:
        final_local_path = _resolve_existing_local_path(project_dir, Path(local_path))

    relative_local_path = _relative_to_project(project_dir, final_local_path)
    resolved_filename = final_local_path.name

    return StockImageRecord(
        filename=resolved_filename,
        local_path=relative_local_path,
        source_provider=provider.name,
        source_id=source_id,
        source_url=source_url,
        download_url=download_url,
        creator_name=creator_name,
        creator_url=creator_url,
        license_name=license_name or provider.license_name,
        license_url=license_url or provider.license_url,
        commercial_use_allowed=(
            provider.commercial_use_allowed if commercial_use_allowed is None else commercial_use_allowed
        ),
        attribution_required=(
            provider.attribution_required if attribution_required is None else attribution_required
        ),
        restriction_notes=restriction_notes or provider.restriction_notes,
        verification_note=verification_note or provider.verification_note,
        downloaded_at=now_utc_iso(),
        keywords=_normalize_keywords(keywords),
        notes=notes,
    )


def upsert_record(project_dir: Path, record: StockImageRecord) -> Path:
    """Upsert a stock image record into the project manifest."""

    manifest = load_manifest(project_dir)
    record_dict = asdict(record)
    images = manifest["images"]

    for index, current in enumerate(images):
        if current.get("local_path") == record.local_path:
            images[index] = record_dict
            break
    else:
        images.append(record_dict)

    return save_manifest(project_dir, manifest)


def str_to_bool(value: str) -> bool:
    """Parse a permissive CLI boolean token."""

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"Invalid boolean value: {value}")


def print_supported_providers(output: Callable[[str], None] = print) -> None:
    """Print provider metadata in a stable CLI-friendly format."""

    output("Supported stock providers:")
    for provider in list_providers():
        output(f"- {provider.name}: {provider.license_name} ({provider.license_url})")


def add_shared_record_arguments(parser: argparse.ArgumentParser) -> None:
    """Attach shared registration arguments to a CLI parser."""

    parser.add_argument("project_dir", nargs="?", help="Project directory.")
    parser.add_argument("--provider", choices=provider_choices(), help="Stock provider.")
    parser.add_argument("--source-url", dest="source_url", help="Original provider page URL.")
    parser.add_argument("--source-id", dest="source_id", default=None, help="Provider-specific image ID.")
    parser.add_argument("--filename", dest="filename", default=None, help="Target filename inside images/stock/.")
    parser.add_argument("--creator-name", dest="creator_name", default=None, help="Creator or photographer name.")
    parser.add_argument("--creator-url", dest="creator_url", default=None, help="Creator profile URL.")
    parser.add_argument("--license-name", dest="license_name", default=None, help="License name override.")
    parser.add_argument("--license-url", dest="license_url", default=None, help="License URL override.")
    parser.add_argument(
        "--commercial-use-allowed",
        dest="commercial_use_allowed",
        type=str_to_bool,
        default=None,
        help="Override provider commercial-use flag (true/false).",
    )
    parser.add_argument(
        "--attribution-required",
        dest="attribution_required",
        type=str_to_bool,
        default=None,
        help="Override provider attribution flag (true/false).",
    )
    parser.add_argument("--restriction-notes", dest="restriction_notes", default=None, help="Restriction summary.")
    parser.add_argument("--verification-note", dest="verification_note", default=None, help="Verification note.")
    parser.add_argument("--keywords", dest="keywords", default=None, help="Comma-separated keywords.")
    parser.add_argument("--notes", dest="notes", default=None, help="Free-form notes.")
    parser.add_argument("--list-providers", action="store_true", help="List supported stock providers and exit.")


def build_register_parser() -> argparse.ArgumentParser:
    """Build the parser for the stock registration CLI."""

    parser = argparse.ArgumentParser(description="Register a stock image into images/stock/manifest.json.")
    add_shared_record_arguments(parser)
    parser.add_argument("--download-url", dest="download_url", default=None, help="Recorded download URL.")
    parser.add_argument(
        "--local-file",
        dest="local_file",
        default=None,
        help="External local file to copy into the project.",
    )
    parser.add_argument(
        "--local-path",
        dest="local_path",
        default=None,
        help="Existing project-local file path to register.",
    )
    return parser


def build_download_parser() -> argparse.ArgumentParser:
    """Build the parser for the download-and-register CLI."""

    parser = argparse.ArgumentParser(description="Download a stock image and register it into images/stock/manifest.json.")
    add_shared_record_arguments(parser)
    parser.add_argument("--download-url", dest="download_url", help="Direct download URL.")
    parser.add_argument("--timeout", type=int, default=60, help="Download timeout in seconds.")
    return parser


def validate_required_fields(
    project_dir: Optional[str],
    provider: Optional[str],
    source_url: Optional[str],
    *,
    download_url: Optional[str] = None,
    require_download_url: bool = False,
) -> None:
    """Validate the required CLI fields for stock registration workflows."""

    if not project_dir:
        raise ValueError("project_dir is required unless --list-providers is used.")
    if not provider:
        raise ValueError("--provider is required.")
    if not source_url:
        raise ValueError("--source-url is required.")
    if require_download_url and not download_url:
        raise ValueError("--download-url is required.")


def register_request_from_args(args: argparse.Namespace) -> RegisterStockRequest:
    """Convert parsed register CLI args into a typed request."""

    validate_required_fields(args.project_dir, args.provider, args.source_url)
    return RegisterStockRequest(
        project_dir=Path(args.project_dir),
        provider_name=args.provider,
        source_url=args.source_url,
        source_id=args.source_id,
        download_url=args.download_url,
        local_file=Path(args.local_file) if args.local_file else None,
        local_path=Path(args.local_path) if args.local_path else None,
        filename=args.filename,
        creator_name=args.creator_name,
        creator_url=args.creator_url,
        license_name=args.license_name,
        license_url=args.license_url,
        commercial_use_allowed=args.commercial_use_allowed,
        attribution_required=args.attribution_required,
        restriction_notes=args.restriction_notes,
        verification_note=args.verification_note,
        keywords=args.keywords,
        notes=args.notes,
    )


def download_request_from_args(args: argparse.Namespace) -> DownloadStockRequest:
    """Convert parsed download CLI args into a typed request."""

    validate_required_fields(
        args.project_dir,
        args.provider,
        args.source_url,
        download_url=args.download_url,
        require_download_url=True,
    )
    return DownloadStockRequest(
        project_dir=Path(args.project_dir),
        provider_name=args.provider,
        source_url=args.source_url,
        download_url=args.download_url,
        source_id=args.source_id,
        filename=args.filename,
        creator_name=args.creator_name,
        creator_url=args.creator_url,
        license_name=args.license_name,
        license_url=args.license_url,
        commercial_use_allowed=args.commercial_use_allowed,
        attribution_required=args.attribution_required,
        restriction_notes=args.restriction_notes,
        verification_note=args.verification_note,
        keywords=args.keywords,
        notes=args.notes,
        timeout_seconds=args.timeout,
    )


def register_stock_image(request: RegisterStockRequest) -> Tuple[StockImageRecord, Path]:
    """Register an existing stock image into the project manifest."""

    record = build_record(
        project_dir=request.project_dir,
        provider_name=request.provider_name,
        source_url=request.source_url,
        local_file=request.local_file,
        local_path=request.local_path,
        filename=request.filename,
        source_id=request.source_id,
        download_url=request.download_url,
        creator_name=request.creator_name,
        creator_url=request.creator_url,
        license_name=request.license_name,
        license_url=request.license_url,
        commercial_use_allowed=request.commercial_use_allowed,
        attribution_required=request.attribution_required,
        restriction_notes=request.restriction_notes,
        verification_note=request.verification_note,
        keywords=request.keywords,
        notes=request.notes,
    )
    manifest = upsert_record(request.project_dir, record)
    return record, manifest


def download_and_register_stock_image(request: DownloadStockRequest) -> Tuple[Path, StockImageRecord, Path]:
    """Download a stock image, then register it into the project manifest."""

    downloaded_file = download_to_stock(
        request.project_dir,
        request.download_url,
        request.filename,
        request.timeout_seconds,
    )
    record = build_record(
        project_dir=request.project_dir,
        provider_name=request.provider_name,
        source_url=request.source_url,
        local_path=downloaded_file.relative_to(request.project_dir),
        filename=downloaded_file.name,
        source_id=request.source_id,
        download_url=request.download_url,
        creator_name=request.creator_name,
        creator_url=request.creator_url,
        license_name=request.license_name,
        license_url=request.license_url,
        commercial_use_allowed=request.commercial_use_allowed,
        attribution_required=request.attribution_required,
        restriction_notes=request.restriction_notes,
        verification_note=request.verification_note,
        keywords=request.keywords,
        notes=request.notes,
    )
    manifest = upsert_record(request.project_dir, record)
    return downloaded_file, record, manifest


def execute_register_command(
    args: argparse.Namespace,
    *,
    output_fn=print,
    provider_printer=print_supported_providers,
    request_builder=register_request_from_args,
    register_handler=register_stock_image,
) -> int:
    """Execute parsed stock registration arguments with injectable handlers."""

    if args.list_providers:
        provider_printer()
        return 0

    record, manifest = register_handler(request_builder(args))
    output_fn(f"Registered stock image: {record.local_path}")
    output_fn(f"Manifest updated: {manifest}")
    return 0


def execute_download_command(
    args: argparse.Namespace,
    *,
    output_fn=print,
    provider_printer=print_supported_providers,
    request_builder=download_request_from_args,
    download_handler=download_and_register_stock_image,
) -> int:
    """Execute parsed stock download arguments with injectable handlers."""

    if args.list_providers:
        provider_printer()
        return 0

    downloaded_file, _record, manifest = download_handler(request_builder(args))
    output_fn(f"Downloaded stock image: {downloaded_file}")
    output_fn(f"Manifest updated: {manifest}")
    return 0


def run_register_cli(argv: Optional[Sequence[str]] = None, *, executor=execute_register_command) -> int:
    """CLI entrypoint for stock image registration."""

    parser = build_register_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return executor(args)


def run_download_cli(argv: Optional[Sequence[str]] = None, *, executor=execute_download_command) -> int:
    """CLI entrypoint for stock image download and registration."""

    parser = build_download_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return executor(args)


def register_main() -> int:
    return run_register_cli()


def download_main() -> int:
    return run_download_cli()


__all__ = [
    "DEFAULT_STOCK_DIRNAME",
    "DownloadStockRequest",
    "MANIFEST_VERSION",
    "PROVIDER_REGISTRY",
    "RegisterStockRequest",
    "STOCK_ROOT_ENV",
    "SUPPORTED_PROVIDERS",
    "StockImageRecord",
    "StockProvider",
    "StockSourceError",
    "add_shared_record_arguments",
    "build_download_parser",
    "build_record",
    "build_register_parser",
    "download_and_register_stock_image",
    "download_main",
    "download_request_from_args",
    "execute_download_command",
    "execute_register_command",
    "download_to_stock",
    "ensure_stock_dir",
    "get_provider",
    "list_providers",
    "load_manifest",
    "manifest_path",
    "normalize_provider",
    "print_supported_providers",
    "provider_choices",
    "register_main",
    "register_request_from_args",
    "register_stock_image",
    "run_download_cli",
    "run_register_cli",
    "save_manifest",
    "stock_dir",
    "str_to_bool",
    "upsert_record",
    "validate_required_fields",
]
