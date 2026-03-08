# Image Generation Credentials and Tooling Setup

This guide explains how to configure credentials, environment variables, and command examples for the PPT Master image workflow.

## Files Delivered

- Environment template: `../examples/config/pptmaster_image.env.example`
- Command template: `../examples/config/image_generate_commands.sh.example`
- Provider reference: `./image_generation_providers.md`
- Stock image setup: `./image_stock_sources.md`
- Stock env template: `../examples/config/pptmaster_stock.env.example`
- Stock command template: `../examples/config/register_stock_image.sh.example`
- ARK video setup: `./ark_video_generation.md`

## Recommended Setup Flow

1. Copy the environment template to an untracked local file.
2. Fill in only the provider block you intend to use.
3. Load the file with `source` in the current shell.
4. Install the SDK package for the provider you plan to use.
5. Run `image_generate.py` using the matching provider.

## Example: Create a local config file

```bash
cp skills/ppt_master_workflow/examples/config/pptmaster_image.env.example .env.pptmaster-image
```

Then edit `.env.pptmaster-image` and load it:

```bash
source .env.pptmaster-image
```

## Image Acquisition Modes

PPT Master currently supports three stable image acquisition paths inside the workflow:

1. **Project-local images**
   - User-provided assets or template assets copied into `<project>/images/`
   - Executor references local files directly

2. **Commercial stock images**
   - Use `download_stock_image.py` to download from a supported commercial source
   - Or use `register_stock_image.py` to register an already-downloaded file
   - Assets are normalized into `<project>/images/stock/` and tracked in `manifest.json`

3. **AI-generated images**
   - Use `image_generate.py`
   - Static image generation is wired through official SDKs for Gemini, OpenAI-compatible providers, and Doubao Seedream models

> Note: In the current PPT Master workflow, Doubao static image generation is handled by Seedream models in `image_generate.py`. ARK Seedance workflows remain under `doubao_i2v_task.py`.

## SDK dependencies

Install the official SDK for the provider you want to use:

```bash
pip install google-genai Pillow
pip install openai Pillow
pip install "volcengine-python-sdk[ark]" Pillow
```

## Shared Variables

These variables apply across providers and are the preferred place for workflow defaults:

- `PPTMASTER_IMAGE_PROVIDER`
- `PPTMASTER_IMAGE_OUTPUT_DIR`
- `PPTMASTER_IMAGE_TIMEOUT`
- `PPTMASTER_IMAGE_API_KEY`
- `PPTMASTER_IMAGE_BASE_URL`
- `PPTMASTER_IMAGE_ENDPOINT`
- `PPTMASTER_IMAGE_MODEL`

Use shared variables when your environment switches providers frequently and you want one common override surface.

## Provider-Specific Variables

### Gemini

- `GEMINI_API_KEY`
- `GEMINI_BASE_URL`
- `GEMINI_IMAGE_MODEL`

### OpenAI-compatible

- `OPENAI_IMAGE_API_KEY`
- `OPENAI_IMAGE_BASE_URL`
- `OPENAI_IMAGE_ENDPOINT`
- `OPENAI_IMAGE_MODEL`

### Doubao

- `DOUBAO_API_KEY`
- `DOUBAO_BASE_URL`
- `DOUBAO_IMAGE_ENDPOINT`
- `DOUBAO_IMAGE_MODEL`

## Provider Examples

### Gemini

```bash
export PPTMASTER_IMAGE_PROVIDER=gemini
export GEMINI_API_KEY="your-key"
export PPTMASTER_IMAGE_OUTPUT_DIR="workspace/demo/images"
```

### Doubao Seedream

Use Seedream as the default model for static image generation.
Use `doubao_i2v_task.py` when you need Seedance-based image-to-video generation.

```bash
export PPTMASTER_IMAGE_PROVIDER=doubao
export DOUBAO_API_KEY="your-key"
export DOUBAO_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"
export DOUBAO_IMAGE_MODEL="doubao-seedream-4.5"
export PPTMASTER_IMAGE_OUTPUT_DIR="workspace/demo/images"
```

For `doubao-seedream-5-0-260128`, the workflow now enforces a local minimum canvas size of `3686400` pixels before the SDK request is sent.
For example, `16:9` with `1K` is rejected locally, while `16:9` with `4K` is valid.

Recommended smoke test for Seedream 5 widescreen output:

```bash
python3 skills/ppt_master_workflow/commands/smoke_test_image_provider.py \
  --provider doubao \
  --model doubao-seedream-5-0-260128 \
  --prompt "Minimal business presentation background" \
  --aspect-ratio 16:9 \
  --image-size 4K \
  --output workspace/demo/images \
  --filename seedream5_smoke
```

## Tool Invocation Examples

Use the bundled shell example directly or copy the commands into your own scripts:

```bash
bash skills/ppt_master_workflow/examples/config/image_generate_commands.sh.example
```

For commercial stock images, use the dedicated examples and commands:

```bash
bash skills/ppt_master_workflow/examples/config/register_stock_image.sh.example
python3 skills/ppt_master_workflow/commands/download_stock_image.py workspace/demo \
  --provider pexels \
  --source-url "https://www.pexels.com/photo/example-id/" \
  --download-url "https://images.pexels.com/photos/example.jpeg" \
  --filename stock_cover.jpg
```

You can also inspect supported providers without credentials:

```bash
python3 skills/ppt_master_workflow/commands/image_generate.py --list-providers
python3 skills/ppt_master_workflow/commands/smoke_test_image_provider.py --provider doubao --output workspace/demo/images
```

## Safety Notes

- Do not commit filled credential files.
- Keep real keys in a local file outside git or in your shell profile.
- Prefer `PPTMASTER_IMAGE_OUTPUT_DIR` for stable project-local output routing.
- If a provider requires a non-standard gateway, set `*_IMAGE_ENDPOINT` explicitly.
