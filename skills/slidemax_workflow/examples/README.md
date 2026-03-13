# SlideMax Example Index

> This file is generated automatically by `../scripts/slidemax.py`

> Last updated: 2026-03-13 15:59:31

## Overview

- **Projects**: 15
- **Curated reference projects**: 2
- **Preview-only projects**: 13
- **Canvas formats**: 1
- **SVG files**: 229

## Trust Policy

- Curated reference projects pass delivery validation and svg_final compatibility checks.
- Preview-only projects are kept for browsing, inspiration, or historical comparison and must not be used as a canonical workflow reference.

### Format distribution

- **PPT 16:9**: 15 projects

## Recently Updated

- **顶级咨询风_重庆市区域报告** (PPT 16:9) - 2025-12-13
- **demo_project_intro** (PPT 16:9) - 2025-12-11
- **像素风_git_introduction** (PPT 16:9) - Unknown date
- **易理风_地山谦卦深度研究** (PPT 16:9) - Unknown date
- **禅意风_金刚经第一品研究** (PPT 16:9) - Unknown date

## Curated Reference Projects


### PPT 16:9 (1280×720)

- **[demo_project_intro](./demo_project_intro_ppt169_20251211)** - 2025-12-11 - 10 slides - passes delivery validation; svg_final clean.
- **[谷歌风_google_annual_report](./ppt169_谷歌风_google_annual_report)** - Unknown date - 10 slides - passes delivery validation; svg_final clean.

## Preview-only Projects


### PPT 16:9 (1280×720)

- **[顶级咨询风_重庆市区域报告](./ppt169_顶级咨询风_重庆市区域报告_ppt169_20251213)** - 2025-12-13 - 20 slides - missing README.md. missing speaker notes for 20 slide(s).
- **[像素风_git_introduction](./ppt169_像素风_git_introduction)** - Unknown date - 10 slides - missing README.md. missing speaker notes for 10 slide(s). svg_final compatibility errors: 4.
- **[易理风_地山谦卦深度研究](./ppt169_易理风_地山谦卦深度研究)** - Unknown date - 20 slides - missing README.md. missing speaker notes for 20 slide(s).
- **[禅意风_金刚经第一品研究](./ppt169_禅意风_金刚经第一品研究)** - Unknown date - 15 slides - missing README.md. missing speaker notes for 15 slide(s). svg_final compatibility errors: 3.
- **[通用灵活+代码_debug六步法](./ppt169_通用灵活+代码_debug六步法)** - Unknown date - 10 slides - missing README.md. missing speaker notes for 10 slide(s). svg_final compatibility errors: 5.
- **[通用灵活+学术_重庆大学论文格式标准](./ppt169_通用灵活+学术_重庆大学论文格式标准)** - Unknown date - 11 slides - missing README.md. missing speaker notes for 11 slide(s). svg_final compatibility errors: 9.
- **[通过灵活+代码_三大AI编程神器横向对比](./ppt169_通过灵活+代码_三大AI编程神器横向对比)** - Unknown date - 11 slides - missing README.md. missing speaker notes for 11 slide(s). svg_final compatibility errors: 2.
- **[顶级咨询风_心理治疗中的依恋](./ppt169_顶级咨询风_心理治疗中的依恋)** - Unknown date - 32 slides - missing README.md. missing speaker notes for 32 slide(s). svg_final compatibility errors: 6.
- **[顶级咨询风_构建有效AI代理_Anthropic](./ppt169_顶级咨询风_构建有效AI代理_Anthropic)** - Unknown date - 15 slides - missing README.md. missing speaker notes for 15 slide(s). svg_final compatibility errors: 4.
- **[顶级咨询风_甘孜州经济财政分析](./ppt169_顶级咨询风_甘孜州经济财政分析)** - Unknown date - 17 slides - missing README.md. missing speaker notes for 17 slide(s). svg_final compatibility errors: 5.
- **[高端咨询风_南欧江水电站战略评估](./ppt169_高端咨询风_南欧江水电站战略评估)** - Unknown date - 20 slides - missing speaker notes for 20 slide(s). svg_final compatibility errors: 3.
- **[高端咨询风_汽车认证五年战略规划](./ppt169_高端咨询风_汽车认证五年战略规划)** - Unknown date - 20 slides - missing README.md. missing speaker notes for 20 slide(s). svg_final compatibility errors: 2.
- **[麦肯锡风_kimsoong_customer_loyalty](./ppt169_麦肯锡风_kimsoong_customer_loyalty)** - Unknown date - 8 slides - missing speaker notes for 8 slide(s). svg_final compatibility errors: 4.

## Usage

### Preview a project

Each example project contains:

- `Design specification` markdown
- `svg_output/` - raw SVG output
- `svg_final/` - finalized SVG output
- `README.md` - required for curated reference projects

**Method 1: HTTP server (recommended)**

```bash
python3 -m http.server --directory ./<project_name>/svg_output 8000
# Open http://localhost:8000
```

**Method 2: Open an SVG directly**

```bash
open ./<project_name>/svg_output/slide_01_cover.svg
```

### Create a new project

Follow the structure of an existing project, or use the project manager command:

```bash
python3 ../scripts/slidemax.py project_manager init my_project --format ppt169
```

## Contribution

Contributions are welcome in this examples root.

### Project requirements

1. Follow the standard project structure
2. Include a complete `README.md` for new curated reference examples
3. Pass `project_manager validate` and keep `svg_final/` compatible with the SVG quality rules
4. Use the directory format `{project_name}_{format}_{YYYYMMDD}` for new examples
5. Legacy examples may use older naming conventions, but new additions should not

### Workflow

1. Create the project inside the current examples root
2. Validate the project: `python3 ../scripts/slidemax.py project_manager validate './<project>'`
3. Refresh the index: `python3 ../scripts/slidemax.py generate_examples_index`
4. Submit the change for review

## Related Resources

- [Workflow rules](../AGENTS.md)
- [Design guidelines](../references/docs/design_guidelines.md)
- [Canvas formats](../references/docs/canvas_formats.md)
- [Image prompt guidance](../references/docs/image_prompt_guidance.md)
- [Roles](../roles/AGENTS.md)
- [Chart templates](../templates/charts/README.md)

---

*Generated on 2026-03-13 15:59:31 by SlideMax*