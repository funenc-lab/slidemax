# AI Setup Prompts

Use this document when you want an AI assistant to help configure SlideMax environment variables without guessing the workflow structure.

## Image Generation Prompt

Paste the following into your AI assistant after you copy `skills/slidemax_workflow/examples/config/slidemax_image.env.example` to a local untracked file:

```text
I am setting up SlideMax image generation.
Please help me choose the correct provider block, tell me which required environment variables I must fill in, which optional variables I can leave empty, and how to verify the setup.
Use these files as the canonical references:
- skills/slidemax_workflow/examples/config/slidemax_image.env.example
- skills/slidemax_workflow/docs/image_generation_setup.md
- skills/slidemax_workflow/docs/image_generation_providers.md
After the file is filled, tell me which doctor command to run next.
```

## Stock Image Registration Prompt

Paste the following into your AI assistant after you copy `skills/slidemax_workflow/examples/config/slidemax_stock.env.example` to a local untracked file:

```text
I am setting up SlideMax stock image registration.
Please explain each variable in my stock env file, tell me which values are safe defaults, and tell me whether I need to change the provider allowlist for my team.
Use these files as the canonical references:
- skills/slidemax_workflow/examples/config/slidemax_stock.env.example
- skills/slidemax_workflow/docs/image_stock_sources.md
Then tell me which registration command or download command I should run first.
```

## ARK Video Prompt

Paste the following into your AI assistant after you copy `skills/slidemax_workflow/examples/config/slidemax_ark.env.example` to a local untracked file:

```text
I am setting up SlideMax ARK video generation.
Please tell me which variables are required, which defaults are safe to keep, and how to verify the setup before I create a live task.
Use these files as the canonical references:
- skills/slidemax_workflow/examples/config/slidemax_ark.env.example
- skills/slidemax_workflow/docs/ark_video_generation.md
Then give me the safest first command to run.
```

## Safety Rules

- Keep real secrets in local untracked files only.
- Do not paste real API keys into versioned files.
- Prefer `project_manager.py doctor` before the first live provider request.
- Ask the AI assistant to explain why each variable is needed instead of blindly filling every optional field.
