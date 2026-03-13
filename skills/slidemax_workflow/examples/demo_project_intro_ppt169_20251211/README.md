# Demo Project Intro

This example is a curated SlideMax reference project. It demonstrates a complete ten-slide product introduction deck and keeps the full delivery structure required by the workflow.

## Why This Example Is Trusted

- The project contains raw SVG output, finalized SVG output, notes, templates, images, and an exported PPTX file.
- `notes/total.md` is kept alongside split per-slide note files so both validation and authoring flows are covered.
- The finalized assets are intended to pass the workflow validation and SVG compatibility checks.

## Workflow Coverage

1. Introduce the workflow value proposition and target user pain points.
2. Explain the solution structure, roles, features, supported formats, and tool ecosystem.
3. End with a clear quick-start sequence and a call to action.

## Directory Highlights

- `svg_output/`: Raw slide SVG files before final cleanup.
- `svg_final/`: Finalized SVG files prepared for PPT export.
- `images/`: Example raster assets used by the deck.
- `notes/`: Total notes plus one markdown file per slide.
- `templates/`: Project-local placeholder directory for reusable assets.

## Validation Commands

```bash
python3 ../../../scripts/slidemax.py project_manager validate .
python3 ../../../scripts/slidemax.py svg_quality_checker svg_final
```
