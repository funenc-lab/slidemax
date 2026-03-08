# SlideMax Example Index

> This file is generated automatically by `../commands/generate_examples_index.py`

> Last updated: 2026-03-08 19:17:28

## Overview

- **Projects**: 15
- **Canvas formats**: 2
- **SVG files**: 229

### Format distribution

- **unknown**: 13 projects
- **PPT 16:9**: 2 projects

## Recently Updated

- **ppt169_像素风_git_introduction** (未知格式) - 未知日期
- **ppt169_易理风_地山谦卦深度研究** (未知格式) - 未知日期
- **ppt169_禅意风_金刚经第一品研究** (未知格式) - 未知日期
- **ppt169_谷歌风_google_annual_report** (未知格式) - 未知日期
- **ppt169_通用灵活+代码_debug六步法** (未知格式) - 未知日期

## Project List


### PPT 16:9 (1280×720)

- **[ppt169_顶级咨询风_重庆市区域报告](./ppt169_顶级咨询风_重庆市区域报告_ppt169_20251213)** - 2025-12-13 - 20 slides
- **[demo_project_intro](./demo_project_intro_ppt169_20251211)** - 2025-12-11 - 10 slides

### Other formats

- **[ppt169_像素风_git_introduction](./ppt169_像素风_git_introduction)** (未知格式) - 未知日期 - 10 slides
- **[ppt169_易理风_地山谦卦深度研究](./ppt169_易理风_地山谦卦深度研究)** (未知格式) - 未知日期 - 20 slides
- **[ppt169_禅意风_金刚经第一品研究](./ppt169_禅意风_金刚经第一品研究)** (未知格式) - 未知日期 - 15 slides
- **[ppt169_谷歌风_google_annual_report](./ppt169_谷歌风_google_annual_report)** (未知格式) - 未知日期 - 10 slides
- **[ppt169_通用灵活+代码_debug六步法](./ppt169_通用灵活+代码_debug六步法)** (未知格式) - 未知日期 - 10 slides
- **[ppt169_通用灵活+学术_重庆大学论文格式标准](./ppt169_通用灵活+学术_重庆大学论文格式标准)** (未知格式) - 未知日期 - 11 slides
- **[ppt169_通过灵活+代码_三大AI编程神器横向对比](./ppt169_通过灵活+代码_三大AI编程神器横向对比)** (未知格式) - 未知日期 - 11 slides
- **[ppt169_顶级咨询风_心理治疗中的依恋](./ppt169_顶级咨询风_心理治疗中的依恋)** (未知格式) - 未知日期 - 32 slides
- **[ppt169_顶级咨询风_构建有效AI代理_Anthropic](./ppt169_顶级咨询风_构建有效AI代理_Anthropic)** (未知格式) - 未知日期 - 15 slides
- **[ppt169_顶级咨询风_甘孜州经济财政分析](./ppt169_顶级咨询风_甘孜州经济财政分析)** (未知格式) - 未知日期 - 17 slides
- **[ppt169_高端咨询风_南欧江水电站战略评估](./ppt169_高端咨询风_南欧江水电站战略评估)** (未知格式) - 未知日期 - 20 slides
- **[ppt169_高端咨询风_汽车认证五年战略规划](./ppt169_高端咨询风_汽车认证五年战略规划)** (未知格式) - 未知日期 - 20 slides
- **[ppt169_麦肯锡风_kimsoong_customer_loyalty](./ppt169_麦肯锡风_kimsoong_customer_loyalty)** (未知格式) - 未知日期 - 8 slides

## Usage

### Preview a project

Each example project usually contains:

- `README.md` - project overview
- `Design specification` markdown
- `svg_output/` - raw SVG output

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
python3 ../commands/project_manager.py init my_project --format ppt169
```

## Contribution

Contributions are welcome in this examples root.

### Project requirements

1. Follow the standard project structure
2. Include a complete `README.md` and design specification
3. Keep SVG files aligned with the technical constraints
4. Use the directory format `{project_name}_{format}_{YYYYMMDD}`

### Workflow

1. Create the project inside the current examples root
2. Validate the project: `python3 ../commands/project_manager.py validate './<project>'`
3. Refresh the index: `python3 ../commands/generate_examples_index.py`
4. Submit the change for review

## Related Resources

- [Workflow rules](../AGENTS.md)
- [Docs index](../docs/README.md)
- [Workflow tutorial](../docs/workflow_tutorial.md)
- [Design guidelines](../docs/design_guidelines.md)
- [Canvas formats](../docs/canvas_formats.md)
- [Roles](../roles/README.md)
- [Chart templates](../templates/charts/README.md)

---

*Generated on 2026-03-08 19:17:28 by SlideMax*