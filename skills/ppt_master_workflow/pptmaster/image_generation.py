"""Shared image generation service for PPT Master."""

from __future__ import annotations

import argparse
import base64
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional

try:
    from PIL import Image as PILImage

    HAS_PIL = True
except ImportError:
    HAS_PIL = False


VALID_ASPECT_RATIOS = [
    "1:1",
    "1:4",
    "1:8",
    "2:3",
    "3:2",
    "3:4",
    "4:1",
    "4:3",
    "4:5",
    "5:4",
    "8:1",
    "9:16",
    "16:9",
    "21:9",
]

VALID_IMAGE_SIZES = ["512px", "1K", "2K", "4K"]

DEFAULT_PROVIDER = "gemini"
DEFAULT_TIMEOUT_SECONDS = 180

PROVIDER_ALIASES = {
    "gemini": "gemini",
    "google": "gemini",
    "openai": "openai-compatible",
    "openai-compatible": "openai-compatible",
    "openai_compatible": "openai-compatible",
    "doubao": "doubao",
    "seedance": "doubao",
}

DEFAULT_MODELS = {
    "gemini": "gemini-3.1-flash-image-preview",
    "openai-compatible": "gpt-image-1",
    "doubao": "doubao-seedream-4.5",
}

SIZE_TO_LONG_EDGE = {
    "512px": 512,
    "1K": 1024,
    "2K": 2048,
    "4K": 4096,
}

MODEL_MINIMUM_PIXELS = {
    "doubao": {
        "doubao-seedream-5": 3_686_400,
    },
}


class ImageGenerationError(RuntimeError):
    """Raised when image generation fails."""


@dataclass(frozen=True)
class ImageGenerationRequest:
    """Normalized request for generating a single image."""

    prompt: str
    negative_prompt: Optional[str] = None
    aspect_ratio: str = "1:1"
    image_size: str = "2K"
    output_dir: Optional[Path] = None
    filename: Optional[str] = None


@dataclass(frozen=True)
class ImageProviderConfig:
    """Resolved provider configuration."""

    provider: str
    model: str
    api_key: str
    base_url: Optional[str] = None
    endpoint: Optional[str] = None
    output_dir: Optional[Path] = None
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS


@dataclass(frozen=True)
class ImageGenerationResult:
    """Result metadata for a generated image."""

    path: Path
    provider: str
    model: str


def _first_env(*names: str) -> Optional[str]:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return None


def normalize_provider(provider: Optional[str]) -> str:
    raw = (provider or DEFAULT_PROVIDER).strip().lower()
    normalized = PROVIDER_ALIASES.get(raw)
    if not normalized:
        supported = ", ".join(sorted(set(PROVIDER_ALIASES.values())))
        raise ValueError(f"Unsupported provider '{provider}'. Supported: {supported}")
    return normalized


def normalize_image_size(image_size: str) -> str:
    normalized = image_size.strip()
    upper = normalized.upper()
    if upper in ("1K", "2K", "4K"):
        return upper
    if upper in ("512PX", "512"):
        return "512px"
    return normalized


def validate_request(request: ImageGenerationRequest) -> ImageGenerationRequest:
    image_size = normalize_image_size(request.image_size)
    if request.aspect_ratio not in VALID_ASPECT_RATIOS:
        raise ValueError(
            f"Invalid aspect ratio '{request.aspect_ratio}'. Valid: {VALID_ASPECT_RATIOS}"
        )
    if image_size not in VALID_IMAGE_SIZES:
        raise ValueError(f"Invalid image size '{request.image_size}'. Valid: {VALID_IMAGE_SIZES}")
    return ImageGenerationRequest(
        prompt=request.prompt,
        negative_prompt=request.negative_prompt,
        aspect_ratio=request.aspect_ratio,
        image_size=image_size,
        output_dir=request.output_dir,
        filename=request.filename,
    )


def _resolve_output_dir(cli_output_dir: Optional[str | Path]) -> Optional[Path]:
    if cli_output_dir:
        return Path(cli_output_dir).expanduser()
    env_output = _first_env("PPTMASTER_IMAGE_OUTPUT_DIR")
    return Path(env_output).expanduser() if env_output else None


def _slugify_prompt(prompt: str) -> str:
    safe = "".join(char for char in prompt if char.isalnum() or char in (" ", "_", "-"))
    safe = safe.strip().replace(" ", "_")[:60]
    return safe or "generated_image"


def resolve_output_path(
    prompt: str,
    output_dir: Optional[Path],
    filename: Optional[str],
    extension: str,
) -> Path:
    stem = Path(filename).stem if filename else _slugify_prompt(prompt)
    full_name = f"{stem}{extension}"
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir / full_name
    return Path(full_name)


def _report_resolution(path: Path) -> None:
    if not HAS_PIL:
        return
    try:
        with PILImage.open(path) as image:
            print(f"  Resolution:   {image.size[0]}x{image.size[1]}")
    except Exception:
        return


def _is_rate_limit_error(error: Exception) -> bool:
    error_text = str(error).lower()
    return (
        "429" in error_text
        or "rate" in error_text
        or "quota" in error_text
        or "resource_exhausted" in error_text
    )


def _parse_ratio(aspect_ratio: str) -> tuple[int, int]:
    width, height = aspect_ratio.split(":", 1)
    return int(width), int(height)


def _round_dimension(value: float) -> int:
    return max(64, int(round(value / 8.0) * 8))


def calculate_dimensions(aspect_ratio: str, image_size: str) -> tuple[int, int]:
    ratio_width, ratio_height = _parse_ratio(aspect_ratio)
    long_edge = SIZE_TO_LONG_EDGE[image_size]
    if ratio_width >= ratio_height:
        width = long_edge
        height = long_edge * ratio_height / ratio_width
    else:
        height = long_edge
        width = long_edge * ratio_width / ratio_height
    return _round_dimension(width), _round_dimension(height)


def resolve_provider_config(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    output_dir: Optional[str | Path] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    endpoint: Optional[str] = None,
    timeout_seconds: Optional[int] = None,
) -> ImageProviderConfig:
    normalized_provider = normalize_provider(provider or _first_env("PPTMASTER_IMAGE_PROVIDER"))
    resolved_output_dir = _resolve_output_dir(output_dir)
    resolved_timeout = timeout_seconds or int(_first_env("PPTMASTER_IMAGE_TIMEOUT") or DEFAULT_TIMEOUT_SECONDS)

    provider_model: Optional[str]
    provider_api_key: Optional[str]
    provider_base_url: Optional[str]
    provider_endpoint: Optional[str]

    if normalized_provider == "gemini":
        provider_model = model or _first_env("PPTMASTER_IMAGE_MODEL", "GEMINI_IMAGE_MODEL") or DEFAULT_MODELS[normalized_provider]
        provider_api_key = api_key or _first_env("PPTMASTER_IMAGE_API_KEY", "GEMINI_API_KEY")
        provider_base_url = base_url or _first_env("PPTMASTER_IMAGE_BASE_URL", "GEMINI_BASE_URL")
        provider_endpoint = endpoint or _first_env("PPTMASTER_IMAGE_ENDPOINT")
        if not provider_api_key:
            raise ValueError("Missing API key. Set GEMINI_API_KEY or PPTMASTER_IMAGE_API_KEY.")
    elif normalized_provider == "openai-compatible":
        provider_model = model or _first_env(
            "PPTMASTER_IMAGE_MODEL",
            "OPENAI_IMAGE_MODEL",
            "OPENAI_MODEL",
        ) or DEFAULT_MODELS[normalized_provider]
        provider_api_key = api_key or _first_env(
            "PPTMASTER_IMAGE_API_KEY",
            "OPENAI_IMAGE_API_KEY",
            "OPENAI_API_KEY",
        )
        provider_base_url = base_url or _first_env(
            "PPTMASTER_IMAGE_BASE_URL",
            "OPENAI_IMAGE_BASE_URL",
            "OPENAI_BASE_URL",
        )
        provider_endpoint = endpoint or _first_env(
            "PPTMASTER_IMAGE_ENDPOINT",
            "OPENAI_IMAGE_ENDPOINT",
        )
        if not provider_api_key:
            raise ValueError("Missing API key. Set OPENAI_IMAGE_API_KEY, OPENAI_API_KEY, or PPTMASTER_IMAGE_API_KEY.")
        if not provider_endpoint and not provider_base_url:
            raise ValueError("Missing base URL. Set OPENAI_IMAGE_BASE_URL, OPENAI_BASE_URL, or PPTMASTER_IMAGE_BASE_URL.")
    else:
        provider_model = model or _first_env("PPTMASTER_IMAGE_MODEL", "DOUBAO_IMAGE_MODEL") or DEFAULT_MODELS[normalized_provider]
        provider_api_key = api_key or _first_env("PPTMASTER_IMAGE_API_KEY", "DOUBAO_API_KEY", "ARK_API_KEY")
        provider_base_url = base_url or _first_env("PPTMASTER_IMAGE_BASE_URL", "DOUBAO_BASE_URL", "ARK_BASE_URL")
        provider_endpoint = endpoint or _first_env("PPTMASTER_IMAGE_ENDPOINT", "DOUBAO_IMAGE_ENDPOINT")
        if not provider_api_key:
            raise ValueError("Missing API key. Set DOUBAO_API_KEY, ARK_API_KEY, or PPTMASTER_IMAGE_API_KEY.")
        if not provider_endpoint and not provider_base_url:
            raise ValueError("Missing base URL. Set DOUBAO_BASE_URL, ARK_BASE_URL, or PPTMASTER_IMAGE_BASE_URL.")

    return ImageProviderConfig(
        provider=normalized_provider,
        model=provider_model,
        api_key=provider_api_key,
        base_url=provider_base_url,
        endpoint=provider_endpoint,
        output_dir=resolved_output_dir,
        timeout_seconds=resolved_timeout,
    )


def _build_sdk_base_url(config: ImageProviderConfig) -> str:
    if config.base_url:
        return config.base_url.rstrip("/")
    if not config.endpoint:
        raise ImageGenerationError("SDK generation requires base_url or endpoint.")
    normalized_endpoint = config.endpoint.rstrip("/")
    suffix = "/images/generations"
    if normalized_endpoint.endswith(suffix):
        return normalized_endpoint[: -len(suffix)]
    raise ImageGenerationError(
        "SDK generation requires base_url or an endpoint ending with '/images/generations'."
    )


def _sdk_canvas_size(request: ImageGenerationRequest) -> str:
    width, height = calculate_dimensions(request.aspect_ratio, request.image_size)
    return f"{width}x{height}"


def _resolve_minimum_pixels(config: ImageProviderConfig) -> Optional[int]:
    provider_requirements = MODEL_MINIMUM_PIXELS.get(config.provider, {})
    normalized_model = config.model.lower()
    for model_prefix, minimum_pixels in provider_requirements.items():
        if normalized_model.startswith(model_prefix):
            return minimum_pixels
    return None


def _validate_provider_constraints(
    config: ImageProviderConfig,
    request: ImageGenerationRequest,
) -> None:
    minimum_pixels = _resolve_minimum_pixels(config)
    if minimum_pixels is None:
        return

    width, height = calculate_dimensions(request.aspect_ratio, request.image_size)
    pixel_count = width * height
    if pixel_count >= minimum_pixels:
        return

    raise ImageGenerationError(
        f"Model {config.model} requires at least {minimum_pixels} pixels. "
        f"Current canvas is {width}x{height} ({pixel_count} pixels). "
        "Use a larger image_size or a less restrictive aspect ratio."
    )


def _final_prompt(request: ImageGenerationRequest) -> str:
    if not request.negative_prompt:
        return request.prompt
    return f"{request.prompt}\n\nNegative prompt: {request.negative_prompt}"


def _extract_response_data(response: Any) -> list[Any]:
    if isinstance(response, dict):
        data = response.get("data")
    elif hasattr(response, "data"):
        data = getattr(response, "data")
    elif hasattr(response, "model_dump"):
        dumped = response.model_dump()
        data = dumped.get("data")
    else:
        data = None

    if not data:
        raise ImageGenerationError("The provider response does not contain image data.")
    return list(data)


def _extract_item_value(item: Any, key: str) -> Any:
    if isinstance(item, dict):
        return item.get(key)
    if hasattr(item, key):
        return getattr(item, key)
    if hasattr(item, "model_dump"):
        dumped = item.model_dump()
        return dumped.get(key)
    return None


def _download_image_from_url(url: str, timeout_seconds: int) -> tuple[bytes, str]:
    import requests

    response = requests.get(url, timeout=timeout_seconds)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    extension = ".jpg" if "jpeg" in content_type else ".png"
    return response.content, extension


def _decode_response_image(response_data: Any, timeout_seconds: int) -> tuple[bytes, str]:
    data = _extract_response_data(response_data)
    first = data[0]

    b64_json = _extract_item_value(first, "b64_json")
    if b64_json:
        return base64.b64decode(b64_json), ".png"

    base64_value = _extract_item_value(first, "base64")
    if base64_value:
        return base64.b64decode(base64_value), ".png"

    url = _extract_item_value(first, "url")
    if url:
        return _download_image_from_url(url, timeout_seconds)

    raise ImageGenerationError(
        "Unsupported response schema from the provider. Expected 'b64_json', 'base64', or 'url'."
    )


def _save_generated_image(
    request: ImageGenerationRequest,
    config: ImageProviderConfig,
    image_bytes: bytes,
    extension: str,
) -> Path:
    output_path = resolve_output_path(
        prompt=request.prompt,
        output_dir=request.output_dir or config.output_dir,
        filename=request.filename,
        extension=extension,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True) if output_path.parent != Path(".") else None
    output_path.write_bytes(image_bytes)
    print(f"File saved to: {output_path}")
    _report_resolution(output_path)
    return output_path


def _generate_with_gemini(config: ImageProviderConfig, request: ImageGenerationRequest) -> Path:
    try:
        from google import genai
        from google.genai import types
    except ImportError as error:
        raise ImageGenerationError(
            "Gemini generation requires google-genai. Run: pip install google-genai Pillow"
        ) from error

    client_kwargs = {"api_key": config.api_key}
    if config.base_url:
        client_kwargs["http_options"] = {"base_url": config.base_url}
    client = genai.Client(**client_kwargs)

    config_kwargs = {
        "response_modalities": ["IMAGE"],
        "image_config": types.ImageConfig(
            aspect_ratio=request.aspect_ratio,
            image_size=request.image_size,
        ),
    }
    if "flash" in config.model.lower():
        config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_level="MINIMAL")

    prompt = _final_prompt(request)
    print(f"[Provider]     {config.provider}")
    print(f"[Model]        {config.model}")
    if config.base_url:
        print(f"[Base URL]     {config.base_url}")
    print(f"[Aspect Ratio] {request.aspect_ratio}")
    print(f"[Canvas Size]  {_sdk_canvas_size(request)}")
    print()
    print("  Generating with Gemini...", end="", flush=True)

    start_time = time.time()
    import threading

    stop_event = threading.Event()

    def heartbeat() -> None:
        while not stop_event.is_set():
            stop_event.wait(5)
            if not stop_event.is_set():
                elapsed = time.time() - start_time
                print(f" {elapsed:.0f}s...", end="", flush=True)

    heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
    heartbeat_thread.start()

    last_image_part = None
    chunk_count = 0

    for chunk in client.models.generate_content_stream(
        model=config.model,
        contents=[prompt],
        config=types.GenerateContentConfig(**config_kwargs),
    ):
        if chunk.parts is None:
            continue
        for part in chunk.parts:
            if part.inline_data is not None:
                chunk_count += 1
                last_image_part = part

    stop_event.set()
    heartbeat_thread.join(timeout=1)
    print(f" done ({time.time() - start_time:.1f}s, {chunk_count} chunk(s))")

    if last_image_part is None or last_image_part.inline_data is None:
        raise ImageGenerationError("No image was returned by the Gemini provider.")

    output_path = resolve_output_path(
        prompt=request.prompt,
        output_dir=request.output_dir or config.output_dir,
        filename=request.filename,
        extension=".png",
    )
    image = last_image_part.as_image()
    image.save(output_path)
    print(f"File saved to: {output_path}")
    _report_resolution(output_path)
    return output_path


def _generate_with_openai_sdk(config: ImageProviderConfig, request: ImageGenerationRequest) -> Path:
    try:
        from openai import OpenAI
    except ImportError as error:
        raise ImageGenerationError(
            "OpenAI-compatible SDK generation requires openai. Run: pip install openai Pillow"
        ) from error

    base_url = _build_sdk_base_url(config)
    width, height = calculate_dimensions(request.aspect_ratio, request.image_size)
    prompt = _final_prompt(request)

    print(f"[Provider]     {config.provider}")
    print(f"[Model]        {config.model}")
    print(f"[Base URL]     {base_url}")
    print(f"[Canvas Size]  {width}x{height}")
    print()

    client = OpenAI(api_key=config.api_key, base_url=base_url)
    response = client.images.generate(
        model=config.model,
        prompt=prompt,
        size=f"{width}x{height}",
        response_format="b64_json",
    )
    image_bytes, extension = _decode_response_image(response, config.timeout_seconds)
    return _save_generated_image(request, config, image_bytes, extension)


def _generate_with_doubao_sdk(config: ImageProviderConfig, request: ImageGenerationRequest) -> Path:
    try:
        from volcenginesdkarkruntime import Ark
    except ImportError as error:
        raise ImageGenerationError(
            "Doubao SDK generation requires volcengine-python-sdk[ark]. Run: pip install 'volcengine-python-sdk[ark]' Pillow"
        ) from error

    base_url = _build_sdk_base_url(config)
    prompt = _final_prompt(request)

    print(f"[Provider]     {config.provider}")
    print(f"[Model]        {config.model}")
    print(f"[Base URL]     {base_url}")
    print(f"[Canvas Size]  {_sdk_canvas_size(request)}")
    print()

    client = Ark(base_url=base_url, api_key=config.api_key)
    response = client.images.generate(
        model=config.model,
        prompt=prompt,
        sequential_image_generation="disabled",
        response_format="url",
        size=_sdk_canvas_size(request),
        stream=False,
        watermark=True,
    )
    image_bytes, extension = _decode_response_image(response, config.timeout_seconds)
    return _save_generated_image(request, config, image_bytes, extension)


PROVIDER_HANDLERS: Dict[str, Callable[[ImageProviderConfig, ImageGenerationRequest], Path]] = {
    "gemini": _generate_with_gemini,
    "openai-compatible": _generate_with_openai_sdk,
    "doubao": _generate_with_doubao_sdk,
}


def generate_image(
    request: ImageGenerationRequest,
    config: ImageProviderConfig,
    max_retries: int = 3,
) -> ImageGenerationResult:
    normalized_request = validate_request(request)
    _validate_provider_constraints(config, normalized_request)
    handler = PROVIDER_HANDLERS[config.provider]
    last_error: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        try:
            path = handler(config, normalized_request)
            return ImageGenerationResult(path=path, provider=config.provider, model=config.model)
        except Exception as error:
            last_error = error
            if attempt >= max_retries:
                break
            delay_seconds = 10 * (2**attempt) if _is_rate_limit_error(error) else 5
            print(f"Retrying in {delay_seconds}s after error: {error}")
            time.sleep(delay_seconds)

    raise ImageGenerationError(
        f"Failed after {max_retries + 1} attempt(s). Last error: {last_error}"
    ) from last_error



def generate_with_legacy_gemini(
    prompt: str,
    negative_prompt: Optional[str] = None,
    aspect_ratio: str = '1:1',
    image_size: str = '2K',
    output_dir: Optional[str | Path] = None,
    filename: Optional[str] = None,
    model: Optional[str] = None,
    max_retries: int = 3,
) -> str:
    request = ImageGenerationRequest(
        prompt=prompt,
        negative_prompt=negative_prompt,
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        output_dir=Path(output_dir).expanduser() if output_dir else None,
        filename=filename,
    )
    config = resolve_provider_config(
        provider='gemini',
        model=model or DEFAULT_MODELS['gemini'],
        output_dir=output_dir,
    )
    return str(generate_image(request, config, max_retries=max_retries).path)


def build_legacy_gemini_parser() -> argparse.ArgumentParser:
    return build_parser(
        description='Generate images with the Gemini provider (legacy Nano Banana wrapper).',
        default_provider='gemini',
        default_prompt='Nano Banana',
        include_provider_argument=False,
    )


def run_legacy_gemini_cli(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_legacy_gemini_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return run_cli(args, forced_provider='gemini')


def legacy_gemini_main() -> None:
    raise SystemExit(run_legacy_gemini_cli())


def available_providers() -> list[str]:
    return sorted(set(PROVIDER_ALIASES.values()))


def build_parser(
    *,
    description: str,
    default_provider: str = DEFAULT_PROVIDER,
    default_prompt: str = "Generate image",
    include_provider_argument: bool = True,
) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("prompt", nargs="?", default=default_prompt, help="The prompt for image generation.")
    parser.add_argument(
        "--negative-prompt",
        "--negative_prompt",
        "-n",
        dest="negative_prompt",
        default=None,
        help="Negative prompt.",
    )
    parser.add_argument(
        "--aspect-ratio",
        "--aspect_ratio",
        default="1:1",
        choices=VALID_ASPECT_RATIOS,
        help=f"Aspect ratio. Choices: {VALID_ASPECT_RATIOS}.",
    )
    parser.add_argument(
        "--image-size",
        "--image_size",
        default="2K",
        help=f"Image size. Choices: {VALID_IMAGE_SIZES}. Case-insensitive.",
    )
    parser.add_argument("--output", "-o", default=None, help="Output directory. Overrides PPTMASTER_IMAGE_OUTPUT_DIR.")
    parser.add_argument("--filename", "-f", default=None, help="Output filename without extension.")
    if include_provider_argument:
        parser.add_argument(
            "--provider",
            default=default_provider,
            choices=available_providers(),
            help="Image provider.",
        )
    else:
        parser.set_defaults(provider=default_provider)
    parser.add_argument("--model", "-m", default=None, help="Model name. Overrides env defaults.")
    parser.add_argument("--api-key", default=None, help="API key. Overrides provider env variables.")
    parser.add_argument("--base-url", default=None, help="Base URL for the provider.")
    parser.add_argument("--endpoint", default=None, help="Full endpoint that can be mapped back to a provider SDK base URL.")
    parser.add_argument("--timeout", type=int, default=None, help="Request timeout in seconds.")
    parser.add_argument("--max-retries", type=int, default=3, help="Maximum retry count.")
    parser.add_argument(
        "--list-providers",
        action="store_true",
        help="Print supported providers and exit.",
    )
    return parser


def run_cli(args: argparse.Namespace, *, forced_provider: Optional[str] = None) -> int:
    if args.list_providers:
        print("Supported providers:")
        for provider in available_providers():
            default_model = DEFAULT_MODELS.get(provider, "-")
            print(f"- {provider} (default model: {default_model})")
        return 0

    request = ImageGenerationRequest(
        prompt=args.prompt,
        negative_prompt=args.negative_prompt,
        aspect_ratio=args.aspect_ratio,
        image_size=args.image_size,
        output_dir=Path(args.output).expanduser() if args.output else None,
        filename=args.filename,
    )
    provider = forced_provider or args.provider
    config = resolve_provider_config(
        provider=provider,
        model=args.model,
        output_dir=args.output,
        api_key=args.api_key,
        base_url=args.base_url,
        endpoint=args.endpoint,
        timeout_seconds=args.timeout,
    )
    result = generate_image(request, config, max_retries=args.max_retries)
    print()
    print(f"Generated image with {result.provider}:{result.model}")
    print(result.path)
    return 0


def generate_legacy_gemini(
    prompt: str,
    negative_prompt: Optional[str] = None,
    aspect_ratio: str = "1:1",
    image_size: str = "2K",
    output_dir: Optional[str] = None,
    filename: Optional[str] = None,
    model: Optional[str] = None,
    max_retries: int = 3,
) -> str:
    request = ImageGenerationRequest(
        prompt=prompt,
        negative_prompt=negative_prompt,
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        output_dir=Path(output_dir).expanduser() if output_dir else None,
        filename=filename,
    )
    config = resolve_provider_config(
        provider="gemini",
        model=model or DEFAULT_MODELS["gemini"],
        output_dir=output_dir,
    )
    return str(generate_image(request, config, max_retries=max_retries).path)


def build_smoke_test_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a live smoke test against an image provider.")
    parser.add_argument("--provider", required=True, help="Provider name.")
    parser.add_argument("--prompt", default="Minimal geometric business background", help="Smoke test prompt.")
    parser.add_argument("--aspect-ratio", "--aspect_ratio", default="16:9", help="Aspect ratio.")
    parser.add_argument("--image-size", "--image_size", default="1K", help="Image size.")
    parser.add_argument("--output", "-o", required=True, help="Output directory.")
    parser.add_argument("--filename", "-f", default="smoke_test", help="Output filename stem.")
    parser.add_argument("--model", "-m", default=None, help="Model override.")
    parser.add_argument("--max-retries", type=int, default=0, help="Maximum retry count.")
    return parser


def run_smoke_test_cli(args: argparse.Namespace) -> int:
    config = resolve_provider_config(provider=args.provider, model=args.model, output_dir=args.output)
    request = ImageGenerationRequest(
        prompt=args.prompt,
        aspect_ratio=args.aspect_ratio,
        image_size=args.image_size,
        output_dir=Path(args.output),
        filename=args.filename,
    )
    result = generate_image(request, config, max_retries=args.max_retries)
    print(f"Smoke test output: {result.path}")
    return 0


__all__ = [
    "DEFAULT_MODELS",
    "DEFAULT_PROVIDER",
    "ImageGenerationError",
    "ImageGenerationRequest",
    "ImageGenerationResult",
    "ImageProviderConfig",
    "VALID_ASPECT_RATIOS",
    "VALID_IMAGE_SIZES",
    "available_providers",
    "build_parser",
    "build_smoke_test_parser",
    "calculate_dimensions",
    "generate_image",
    "generate_legacy_gemini",
    "normalize_provider",
    "resolve_provider_config",
    "run_cli",
    "run_smoke_test_cli",
]
