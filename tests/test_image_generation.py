import base64
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PROJECT_ROOT / "skills" / "ppt_master_workflow"
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from pptmaster.image_generation import (
    DEFAULT_MODELS,
    ImageGenerationError,
    ImageGenerationRequest,
    build_parser,
    calculate_dimensions,
    generate_image,
    resolve_provider_config,
)

PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGNgYAAAAAIAAeIhvDMAAAAASUVORK5CYII="
)


class _FakeDownloadResponse:
    def __init__(self, content: bytes, content_type: str = "image/png"):
        self.content = content
        self.headers = {"content-type": content_type}

    def raise_for_status(self):
        return None


class ImageGenerationTestCase(unittest.TestCase):
    def test_resolve_provider_config_for_doubao_uses_specific_env(self):
        with mock.patch.dict(
            os.environ,
            {
                "PPTMASTER_IMAGE_PROVIDER": "doubao",
                "DOUBAO_API_KEY": "secret",
                "DOUBAO_BASE_URL": "https://doubao.example/api/v3",
            },
            clear=False,
        ):
            config = resolve_provider_config()

        self.assertEqual(config.provider, "doubao")
        self.assertEqual(config.api_key, "secret")
        self.assertEqual(config.base_url, "https://doubao.example/api/v3")
        self.assertEqual(config.model, "doubao-seedream-4.5")
        self.assertEqual(DEFAULT_MODELS["doubao"], "doubao-seedream-4.5")
        self.assertFalse(hasattr(config, "transport"))

    def test_parser_rejects_transport_argument(self):
        parser = build_parser(description="test", include_provider_argument=True)
        with self.assertRaises(SystemExit):
            parser.parse_args(
                [
                    "prompt",
                    "--provider",
                    "gemini",
                    "--transport",
                    "sdk",
                ]
            )

    def test_parser_accepts_dash_and_underscore_aliases(self):
        parser = build_parser(description="test", include_provider_argument=True)
        args = parser.parse_args(
            [
                "prompt",
                "--provider",
                "gemini",
                "--aspect_ratio",
                "16:9",
                "--image_size",
                "2K",
                "--negative_prompt",
                "watermark",
            ]
        )
        self.assertEqual(args.aspect_ratio, "16:9")
        self.assertEqual(args.image_size, "2K")
        self.assertEqual(args.negative_prompt, "watermark")

    def test_calculate_dimensions_preserves_aspect_ratio_direction(self):
        width, height = calculate_dimensions("16:9", "2K")
        self.assertGreater(width, height)
        self.assertEqual(width, 2048)
        self.assertEqual(height, 1152)

        width, height = calculate_dimensions("9:16", "2K")
        self.assertLess(width, height)
        self.assertEqual(width, 1152)
        self.assertEqual(height, 2048)

    def test_generate_image_rejects_doubao_seedream5_small_canvas(self):
        config = resolve_provider_config(
            provider="doubao",
            api_key="secret",
            base_url="https://ark.example/api/v3",
            model="doubao-seedream-5-0-260128",
        )

        with self.assertRaises(ImageGenerationError) as error_context:
            generate_image(
                ImageGenerationRequest(
                    prompt="nebula train",
                    aspect_ratio="16:9",
                    image_size="1K",
                ),
                config,
                max_retries=0,
            )

        self.assertIn("3686400", str(error_context.exception))
        self.assertIn("larger image_size", str(error_context.exception))

    def test_generate_image_uses_doubao_sdk(self):
        captured = {}

        class FakeArk:
            def __init__(self, *, base_url, api_key):
                captured["base_url"] = base_url
                captured["api_key"] = api_key
                self.images = types.SimpleNamespace(generate=self.generate)

            def generate(self, **kwargs):
                captured["kwargs"] = kwargs
                return types.SimpleNamespace(data=[types.SimpleNamespace(url="https://cdn.example/generated.png")])

        fake_module = types.ModuleType("volcenginesdkarkruntime")
        fake_module.Ark = FakeArk

        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(sys.modules, {"volcenginesdkarkruntime": fake_module}):
            with mock.patch("requests.get", return_value=_FakeDownloadResponse(PNG_BYTES)) as mocked_get:
                config = resolve_provider_config(
                    provider="doubao",
                    api_key="secret",
                    base_url="https://ark.example/api/v3",
                    model="doubao-seedream-5-0-260128",
                    output_dir=tmp,
                )
                result = generate_image(
                    ImageGenerationRequest(
                        prompt="nebula train",
                        aspect_ratio="16:9",
                        image_size="4K",
                        output_dir=Path(tmp),
                        filename="sdk_doubao",
                    ),
                    config,
                    max_retries=0,
                )

                self.assertEqual(captured["base_url"], "https://ark.example/api/v3")
                self.assertEqual(captured["api_key"], "secret")
                self.assertEqual(captured["kwargs"]["model"], "doubao-seedream-5-0-260128")
                self.assertEqual(captured["kwargs"]["size"], "4096x2304")
                self.assertEqual(captured["kwargs"]["response_format"], "url")
                self.assertEqual(captured["kwargs"]["stream"], False)
                mocked_get.assert_called_once_with("https://cdn.example/generated.png", timeout=config.timeout_seconds)
                self.assertEqual(result.path.read_bytes(), PNG_BYTES)

    def test_generate_image_uses_openai_sdk(self):
        captured = {}

        class FakeOpenAI:
            def __init__(self, *, api_key, base_url):
                captured["api_key"] = api_key
                captured["base_url"] = base_url
                self.images = types.SimpleNamespace(generate=self.generate)

            def generate(self, **kwargs):
                captured["kwargs"] = kwargs
                return types.SimpleNamespace(
                    data=[types.SimpleNamespace(b64_json=base64.b64encode(PNG_BYTES).decode("ascii"))]
                )

        fake_module = types.ModuleType("openai")
        fake_module.OpenAI = FakeOpenAI

        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(sys.modules, {"openai": fake_module}):
            config = resolve_provider_config(
                provider="openai-compatible",
                api_key="secret",
                base_url="https://openai.example/v1",
                output_dir=tmp,
            )
            result = generate_image(
                ImageGenerationRequest(
                    prompt="abstract geometry",
                    aspect_ratio="16:9",
                    image_size="1K",
                    output_dir=Path(tmp),
                    filename="sdk_openai",
                ),
                config,
                max_retries=0,
            )

            self.assertEqual(captured["api_key"], "secret")
            self.assertEqual(captured["base_url"], "https://openai.example/v1")
            self.assertEqual(captured["kwargs"]["model"], DEFAULT_MODELS["openai-compatible"])
            self.assertEqual(captured["kwargs"]["size"], "1024x576")
            self.assertEqual(result.path.read_bytes(), PNG_BYTES)


if __name__ == "__main__":
    unittest.main()
