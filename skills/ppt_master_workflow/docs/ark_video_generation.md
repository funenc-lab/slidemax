# ARK Video Generation

This document describes the dedicated ARK image-to-video task flow.

## Why a Separate Flow

`commands/image_generate.py` is the canonical image-generation entry point.
The ARK `contents/generations/tasks` API is a task-based image-to-video workflow,
so it is intentionally implemented as a separate module and command.

## Files Delivered

- Module: `../pptmaster/video_generation.py`
- Command: `../commands/doubao_i2v_task.py`
- Env template: `../examples/config/pptmaster_ark.env.example`
- Command template: `../examples/config/doubao_i2v_commands.sh.example`

## Credentials

Use environment variables for credentials and transport settings:

- `ARK_API_KEY`
- `ARK_BASE_URL`
- `ARK_TIMEOUT`
- `ARK_VIDEO_MODEL`

Example:

```bash
cp skills/ppt_master_workflow/examples/config/pptmaster_ark.env.example .env.pptmaster-ark
source .env.pptmaster-ark
```

## Command Examples

Create a task and print the task id:

```bash
python3 skills/ppt_master_workflow/commands/doubao_i2v_task.py create \
  "Fast drone flight through a canyon" \
  --image-url "https://example.com/reference.png"
```

Create, wait, and download:

```bash
python3 skills/ppt_master_workflow/commands/doubao_i2v_task.py run \
  "Fast drone flight through a canyon" \
  --image-url "https://example.com/reference.png" \
  --model "doubao-seedance-1-5-pro-251215" \
  --duration 5 \
  --camera-fixed false \
  --watermark true \
  --output workspace/demo/videos/canyon.mp4
```

Query task status:

```bash
python3 skills/ppt_master_workflow/commands/doubao_i2v_task.py status <task_id>
```

Download from a signed video URL:

```bash
python3 skills/ppt_master_workflow/commands/doubao_i2v_task.py download \
  --video-url "https://...signed-url..." \
  --output workspace/demo/videos/result.mp4
```

## Notes on Models

- The command accepts any model name through `--model`.
- The default command example uses `doubao-seedance-1-5-pro-251215` because it is the model that has been verified in this workflow.
- As of 2026-03-05, the official Volcano Engine documentation lists `Doubao-Seedance-2.0` as experience-center only and not yet open through the public API. Keep the model override flexible in code, but do not treat it as a verified API default until your ARK account and the official docs confirm availability.

## Output Behavior

- `create`: prints the task id only, unless `--wait` is added.
- `run`: creates, waits, and optionally downloads when `--output` is provided.
- `download`: downloads a generated video from a signed URL.
