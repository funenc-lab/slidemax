from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Sequence

ALPHA_THRESHOLD = 0.002
MAX_ALPHA = 0.99
LOGO_VALUE = 255.0
DEFAULT_OUTPUT_SUFFIX = '_unwatermarked'
DEFAULT_LARGE_LOGO_SIZE = 96
DEFAULT_SMALL_LOGO_SIZE = 48
DEFAULT_LARGE_MARGIN = 64
DEFAULT_SMALL_MARGIN = 32
ASSETS_DIR = Path(__file__).resolve().parent / 'assets'
BACKGROUND_MAP = {
    DEFAULT_SMALL_LOGO_SIZE: ASSETS_DIR / 'bg_48.png',
    DEFAULT_LARGE_LOGO_SIZE: ASSETS_DIR / 'bg_96.png',
}


@dataclass(frozen=True)
class WatermarkConfig:
    logo_size: int
    margin_right: int
    margin_bottom: int


@dataclass(frozen=True)
class WatermarkPosition:
    x: int
    y: int
    width: int
    height: int


def require_numpy() -> Any:
    try:
        import numpy as np_module
    except ModuleNotFoundError as exc:
        raise RuntimeError('numpy is required for watermark removal. Install it with: pip install numpy') from exc
    return np_module


def require_pillow_image() -> Any:
    try:
        from PIL import Image as image_module
    except ModuleNotFoundError as exc:
        raise RuntimeError('Pillow is required for watermark removal. Install it with: pip install Pillow') from exc
    return image_module


class GeminiWatermarkRemover:
    """Remove Gemini watermark overlays from generated images."""

    def __init__(self, *, assets_dir: Path = ASSETS_DIR) -> None:
        self.assets_dir = assets_dir
        self.background_map = {
            DEFAULT_SMALL_LOGO_SIZE: assets_dir / 'bg_48.png',
            DEFAULT_LARGE_LOGO_SIZE: assets_dir / 'bg_96.png',
        }

    @staticmethod
    def detect_watermark_config(width: int, height: int) -> WatermarkConfig:
        if width > 1024 and height > 1024:
            return WatermarkConfig(
                logo_size=DEFAULT_LARGE_LOGO_SIZE,
                margin_right=DEFAULT_LARGE_MARGIN,
                margin_bottom=DEFAULT_LARGE_MARGIN,
            )
        return WatermarkConfig(
            logo_size=DEFAULT_SMALL_LOGO_SIZE,
            margin_right=DEFAULT_SMALL_MARGIN,
            margin_bottom=DEFAULT_SMALL_MARGIN,
        )

    @staticmethod
    def calculate_watermark_position(
        width: int,
        height: int,
        config: WatermarkConfig,
    ) -> WatermarkPosition:
        x = width - config.margin_right - config.logo_size
        y = height - config.margin_bottom - config.logo_size
        if x < 0 or y < 0:
            raise ValueError(
                'Image is too small for the expected watermark placement '
                f'(width={width}, height={height}, logo_size={config.logo_size}).'
            )
        return WatermarkPosition(x=x, y=y, width=config.logo_size, height=config.logo_size)

    @staticmethod
    def calculate_alpha_map(background_image: Any) -> Any:
        np_module = require_numpy()
        background_array = np_module.array(background_image.convert('RGB'), dtype=np_module.float32)
        max_channel = np_module.max(background_array, axis=2)
        return max_channel / 255.0

    def resolve_background_path(self, config: WatermarkConfig) -> Path:
        background_path = self.background_map.get(config.logo_size)
        if background_path is None:
            raise ValueError(f'Unsupported logo size: {config.logo_size}')
        if not background_path.exists():
            raise FileNotFoundError(f'Watermark background asset is missing: {background_path}')
        return background_path

    @staticmethod
    def remove_watermark(image: Any, alpha_map: Any, position: WatermarkPosition) -> Any:
        np_module = require_numpy()
        image_module = require_pillow_image()
        image_array = np_module.array(image.convert('RGBA'), dtype=np_module.float32)
        region = image_array[position.y:position.y + position.height, position.x:position.x + position.width, :3]
        alpha = np_module.clip(alpha_map[: position.height, : position.width], 0.0, MAX_ALPHA)
        active_mask = alpha >= ALPHA_THRESHOLD

        if np_module.any(active_mask):
            alpha_expanded = alpha[..., None]
            restored = (region - alpha_expanded * LOGO_VALUE) / (1.0 - alpha_expanded)
            region[:] = np_module.where(active_mask[..., None], np_module.clip(restored, 0.0, 255.0), region)

        return image_module.fromarray(image_array.astype(np_module.uint8))

    @staticmethod
    def build_output_path(input_path: Path, output_path: Optional[Path] = None) -> Path:
        if output_path is not None:
            return output_path
        suffix = input_path.suffix or '.png'
        return input_path.with_name(f'{input_path.stem}{DEFAULT_OUTPUT_SUFFIX}{suffix}')

    def process_image(
        self,
        input_path: Path,
        output_path: Optional[Path] = None,
        *,
        verbose: bool = True,
    ) -> Path:
        image_module = require_pillow_image()
        output_file = self.build_output_path(input_path, output_path)

        with image_module.open(input_path) as source_image:
            width, height = source_image.size
            config = self.detect_watermark_config(width, height)
            position = self.calculate_watermark_position(width, height, config)

            if verbose:
                print(f'  Image size: {width} x {height}')
                print(f'  Watermark size: {config.logo_size} x {config.logo_size}')
                print(f'  Watermark position: ({position.x}, {position.y})')

            background_path = self.resolve_background_path(config)
            with image_module.open(background_path) as background_image:
                alpha_map = self.calculate_alpha_map(background_image)

            result = self.remove_watermark(source_image, alpha_map, position)

        if output_file.suffix.lower() in ('.jpg', '.jpeg'):
            result = result.convert('RGB')

        output_file.parent.mkdir(parents=True, exist_ok=True)
        result.save(output_file)
        return output_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Remove Gemini watermark overlays from generated images.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s workspace/demo/images/bg_01.png
  %(prog)s image.jpg -o image_clean.jpg

Notes:
  - Detects 96px watermark on large images and 48px watermark on smaller images.
  - Supports PNG, JPG, and JPEG files.
  - Uses the _unwatermarked suffix when no output path is provided.
''',
    )
    parser.add_argument('input', type=Path, help='Input image path')
    parser.add_argument('-o', '--output', type=Path, default=None, help='Output image path')
    parser.add_argument('-q', '--quiet', action='store_true', help='Disable progress logs')
    return parser


def execute_parsed_command(
    args: argparse.Namespace,
    *,
    output_fn=print,
    remover_factory=GeminiWatermarkRemover,
) -> int:
    """Execute parsed CLI arguments with injectable dependencies for testing."""

    if not args.input.exists():
        output_fn(f'[ERROR] File does not exist: {args.input}')
        return 1

    verbose = not args.quiet
    remover = remover_factory()

    if verbose:
        output_fn('PPT Master - Gemini watermark remover')
        output_fn('=' * 40)
        output_fn(f'  Input file: {args.input}')

    try:
        output_path = remover.process_image(args.input, args.output, verbose=verbose)
    except Exception as exc:
        output_fn(f'[ERROR] Watermark removal failed: {exc}')
        return 1

    if verbose:
        output_fn('')
        output_fn(f'[DONE] Saved: {output_path}')
    return 0


def run_cli(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return execute_parsed_command(args)


def main() -> None:
    raise SystemExit(run_cli())


__all__ = [
    'ALPHA_THRESHOLD',
    'ASSETS_DIR',
    'BACKGROUND_MAP',
    'DEFAULT_LARGE_LOGO_SIZE',
    'DEFAULT_LARGE_MARGIN',
    'DEFAULT_OUTPUT_SUFFIX',
    'DEFAULT_SMALL_LOGO_SIZE',
    'DEFAULT_SMALL_MARGIN',
    'execute_parsed_command',
    'GeminiWatermarkRemover',
    'LOGO_VALUE',
    'MAX_ALPHA',
    'WatermarkConfig',
    'WatermarkPosition',
    'build_parser',
    'main',
    'require_numpy',
    'require_pillow_image',
    'run_cli',
]
