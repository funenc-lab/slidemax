# Image Generation Providers

This document defines the provider-neutral image generation surface for PPT Master.

## Goals

- Keep the workflow independent from a single image vendor.
- Allow image output paths to be configured through environment variables.
- Allow new models and gateways to be added without rewriting the role workflow.
- Use the official SDK for each supported provider.

## Canonical Command

Use `commands/image_generate.py` as the primary CLI.

```bash
python3 skills/ppt_master_workflow/commands/image_generate.py "Abstract tech background" \
  --provider gemini \
  --aspect-ratio 16:9 \
  --image-size 4K \
  --output workspace/demo/images \
  --filename cover_bg
```

The legacy `commands/nano_banana_gen.py` command remains available as a Gemini-only compatibility wrapper.

## Image Acquisition Modes

PPT Master accepts image assets through the following normalized paths:

- Local or template assets copied into `<project>/images/`
- Commercial stock assets downloaded or registered into `<project>/images/stock/`
- AI-generated assets written into `<project>/images/` by `image_generate.py`

The workflow keeps Executor on project-local paths and avoids third-party hotlinks inside slide SVG files.

## Example Files

- Environment template: `../examples/config/pptmaster_image.env.example`
- Command template: `../examples/config/image_generate_commands.sh.example`
- Setup guide: `./image_generation_setup.md`

## Supported Providers

### 1. `gemini`

- Default model: `gemini-3.1-flash-image-preview`
- Environment variables:
  - `GEMINI_API_KEY` or `PPTMASTER_IMAGE_API_KEY`
  - `GEMINI_BASE_URL` or `PPTMASTER_IMAGE_BASE_URL`
  - `GEMINI_IMAGE_MODEL` or `PPTMASTER_IMAGE_MODEL`
  - Official SDK: `google-genai`

### 2. `openai-compatible`

- Default model: `gpt-image-1`
- Intended for providers exposing an OpenAI-compatible API through the official `openai` SDK.
- Environment variables:
  - `OPENAI_IMAGE_API_KEY` / `OPENAI_API_KEY` / `PPTMASTER_IMAGE_API_KEY`
  - `OPENAI_IMAGE_BASE_URL` / `OPENAI_BASE_URL` / `PPTMASTER_IMAGE_BASE_URL`
  - `OPENAI_IMAGE_ENDPOINT` / `PPTMASTER_IMAGE_ENDPOINT`
  - `OPENAI_IMAGE_MODEL` / `PPTMASTER_IMAGE_MODEL`
  - Official SDK: `openai`

### 3. `doubao`

- Default model: `doubao-seedream-4.5`
- Static image generation defaults to the Seedream series.
- `image_generate.py` is wired to the official ARK SDK for static image generation.
- ARK image-to-video tasks should use `commands/doubao_i2v_task.py` with Seedance models instead of `image_generate.py`.
- Seedream 5 models can be selected through `--model` or `DOUBAO_IMAGE_MODEL`.
- The workflow validates known model constraints locally before the request is sent.
  - Current built-in rule: `doubao-seedream-5*` requires at least `3686400` pixels.
- Environment variables:
  - `DOUBAO_API_KEY` or `PPTMASTER_IMAGE_API_KEY`
  - `DOUBAO_BASE_URL` or `PPTMASTER_IMAGE_BASE_URL`
  - `DOUBAO_IMAGE_ENDPOINT` or `PPTMASTER_IMAGE_ENDPOINT`
  - `DOUBAO_IMAGE_MODEL` or `PPTMASTER_IMAGE_MODEL`
  - Official SDK: `volcengine-python-sdk[ark]`

## Shared Environment Variables

- `PPTMASTER_IMAGE_PROVIDER`: default provider when `--provider` is omitted.
- `PPTMASTER_IMAGE_MODEL`: default model override for the active provider.
- `PPTMASTER_IMAGE_OUTPUT_DIR`: default output directory for generated assets.
- `PPTMASTER_IMAGE_BASE_URL`: shared provider base URL override.
- `PPTMASTER_IMAGE_ENDPOINT`: shared provider endpoint override.
- `PPTMASTER_IMAGE_API_KEY`: shared provider API key override.
- `PPTMASTER_IMAGE_TIMEOUT`: HTTP timeout in seconds.

## Recommended Configuration Examples

### Gemini

```bash
export PPTMASTER_IMAGE_PROVIDER=gemini
export GEMINI_API_KEY="your-key"
export PPTMASTER_IMAGE_OUTPUT_DIR="workspace/demo/images"
```

### Doubao Seedream

```bash
export PPTMASTER_IMAGE_PROVIDER=doubao
export DOUBAO_API_KEY="your-key"
export DOUBAO_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"
export DOUBAO_IMAGE_MODEL="doubao-seedream-4.5"
export PPTMASTER_IMAGE_OUTPUT_DIR="workspace/demo/images"
```

## Doubao ARK Note

The `doubao` entry in `image_generate.py` now prefers the official ARK SDK for image generation.
If you need the official ARK image-to-video task flow, use `commands/doubao_i2v_task.py` and `docs/ark_video_generation.md`.

## Workflow Guidance

- `Strategist` decides whether the image source is template, user-provided, AI-generated, or placeholder.
- `Image_Generator` always writes prompts to `images/image_prompts.md` first.
- When AI generation is required, the role should prefer `image_generate.py` over provider-specific commands.
- Store all final assets in the project `images/` directory before entering `Executor`.
