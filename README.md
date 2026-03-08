# PPT Master - AI-Powered Multi-Format SVG Content Generation System

[![Version](https://img.shields.io/badge/version-v1.2.0-blue.svg)](https://github.com/funenc-lab/ppt-master/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/funenc-lab/ppt-master.svg)](https://github.com/funenc-lab/ppt-master/stargazers)

English | [中文](./README_CN.md)

An AI-powered intelligent visual content generation system that transforms source documents into high-quality SVG content through multi-role collaboration, **supporting presentations, social media, marketing posters, and various other formats**.

> 🎴 **Online Examples**: [GitHub Pages Online Preview](https://hugohe3.github.io/ppt-master/) - View actual generated results

> 🎬 **Quick Demo**: [YouTube](https://www.youtube.com/watch?v=jM2fHmvMwx0) | [Bilibili](https://www.bilibili.com/video/BV1iUmQBtEGH/) - Watch video demonstrations

## 🧭 Repository Lineage

- **Current maintained repository**: [`funenc-lab/ppt-master`](https://github.com/funenc-lab/ppt-master)
- **Fork source / public upstream repository**: [`hugohe3/ppt-master`](https://github.com/hugohe3/ppt-master)
- **Local Git `origin` for this workspace**: `git@github.com:funenc-lab/ppt-master.git`
- **Note**: The online preview, public demo videos, and some historical references in this README still point to public upstream resources. If you want to clone the repository, file issues, or open PRs for this workspace, use the current fork first.

---

## 🚀 Quick Start

### 1. Configure Environment

#### Python Environment (Required)

This project requires **Python 3.8+** for running PDF conversion, SVG post-processing, PPTX export, and other tools.

**Install Python:**

| Platform | Recommended Installation |
|----------|-------------------------|
| **macOS** | Use [Homebrew](https://brew.sh/): `brew install python` |
| **Windows** | Download installer from [Python Official Website](https://www.python.org/downloads/) |
| **Linux** | Use package manager: `sudo apt install python3 python3-pip` (Ubuntu/Debian) |

> 💡 **Verify Installation**: Run `python3 --version` to confirm version ≥ 3.8

#### Node.js Environment (Optional)

If you need to use the `web_to_md.cjs` tool (for converting web pages from WeChat and other high-security sites), install Node.js.

**Install Node.js:**

| Platform | Recommended Installation |
|----------|-------------------------|
| **macOS** | Use [Homebrew](https://brew.sh/): `brew install node` |
| **Windows** | Download LTS version from [Node.js Official Website](https://nodejs.org/) |
| **Linux** | Use [NodeSource](https://github.com/nodesource/distributions): `curl -fsSL https://deb.nodesource.com/setup_lts.x \| sudo -E bash - && sudo apt-get install -y nodejs` |

> 💡 **Verify Installation**: Run `node --version` to confirm version ≥ 18

### 2. Clone Repository and Install Dependencies

```bash
git clone https://github.com/funenc-lab/ppt-master.git
cd ppt-master
pip install -r requirements.txt
```

> If you encounter permission issues, use `pip install --user -r requirements.txt` or install in a virtual environment.

### 3. Open AI Editor

Recommended AI editors:

| Tool                                                | Rating | Description                                                                                                          |
| --------------------------------------------------- | :----: | -------------------------------------------------------------------------------------------------------------------- |
| **[Antigravity](https://antigravity.dev/)**         | ⭐⭐⭐ | **Highly Recommended**! Free Opus 4.6 access, integrated Banana image generation, can generate images directly in the repository |
| [Cursor](https://cursor.sh/)                        |  ⭐⭐  | Mainstream AI editor, supports multiple models                                                                        |
| [VS Code + Copilot](https://code.visualstudio.com/) |  ⭐⭐  | Microsoft official solution                                                                                           |
| [Claude Code](https://claude.ai/)                   |  ⭐⭐  | Anthropic official CLI tool                                                                                           |

### 4. Start Creating

Open the AI chat panel in your editor and describe what content you want to create:

```
User: I have a Q3 quarterly report that needs to be made into a PPT

AI (Strategist role): Sure, before we begin I need to complete eight confirmations...
   1. Canvas format: [Recommended] PPT 16:9
   2. Page count: [Recommended] 8-10 pages
   ...
```

> 💡 **Model Recommendation**: Opus 4.6 works best, Antigravity currently offers free access

> 💡 **AI Lost Context?** You can prompt the AI to refer to the `AGENTS.md` file, and it will automatically follow the role definitions in the repository

> 💡 **AI Image Generation Tip**: For AI-generated images, we recommend generating them in [Gemini](https://gemini.google.com/) and selecting **Download full size** for higher resolution than Antigravity's direct generation. Gemini images have a star watermark in the bottom right corner, which can be removed using [gemini-watermark-remover](https://github.com/journey-ad/gemini-watermark-remover) or this project's `skills/ppt_master_workflow/commands/gemini_watermark_remover.py`.

---

## 📚 Documentation Navigation

| Document | Description |
|----------|-------------|
| 🗂️ [Documentation Index](./skills/ppt_master_workflow/docs/README.md) | Canonical entry, navigation, and maintenance notes |
| 📖 [Workflow Tutorial](./skills/ppt_master_workflow/docs/workflow_tutorial.md) | Detailed workflow and case demonstrations |
| 🎨 [Design Guidelines](./skills/ppt_master_workflow/docs/design_guidelines.md) | Colors, typography, layout specifications |
| 📐 [Canvas Formats](./skills/ppt_master_workflow/docs/canvas_formats.md) | PPT, Xiaohongshu, WeChat Moments, and 10+ formats |
| 🖼️ [Image Embedding Guide](./skills/ppt_master_workflow/docs/svg_image_embedding.md) | SVG image embedding best practices |
| 📊 [Chart Template Library](./skills/ppt_master_workflow/templates/charts/) | 33 standardized chart templates · [Online Preview](./skills/ppt_master_workflow/templates/charts/preview.html) |
| ⚡ [Quick Reference](./skills/ppt_master_workflow/docs/quick_reference.md) | Common commands and parameters cheat sheet |
| 🔧 [Role Definitions](./skills/ppt_master_workflow/roles/README.md) | Index of 7 AI roles and handoff guidance |
| 🛠️ [Toolset](./skills/ppt_master_workflow/commands/README.md) | Usage instructions for all tools |
| 💼 [Examples Index](./skills/ppt_master_workflow/examples/README.md) | 15 projects, 229 SVG pages of examples |

---

## 🎴 Featured Examples

> 📁 **Example Library**: [`skills/ppt_master_workflow/examples/`](./skills/ppt_master_workflow/examples/) · **15 projects** · **229 SVG pages**

| Category                | Project                                                                                              | Pages | Features                                              |
| ----------------------- | ---------------------------------------------------------------------------------------------------- | :---: | ----------------------------------------------------- |
| 🏢 **Consulting Style** | [Attachment in Psychotherapy](./skills/ppt_master_workflow/examples/ppt169_顶级咨询风_心理治疗中的依恋/)                        |  32   | Top consulting style, largest scale example           |
|                         | [Building Effective AI Agents](./skills/ppt_master_workflow/examples/ppt169_顶级咨询风_构建有效AI代理_Anthropic/)               |  15   | Anthropic engineering blog, AI Agent architecture     |
|                         | [Chongqing Regional Report](./skills/ppt_master_workflow/examples/ppt169_顶级咨询风_重庆市区域报告_ppt169_20251213/)            |  20   | Regional fiscal analysis, Enterprise Alert data 🆕    |
|                         | [Ganzi Prefecture Economic Analysis](./skills/ppt_master_workflow/examples/ppt169_顶级咨询风_甘孜州经济财政分析/)               |  17   | Government fiscal analysis, Tibetan cultural elements |
| 🎨 **General Flexible** | [Debug Six-Step Method](./skills/ppt_master_workflow/examples/ppt169_通用灵活+代码_debug六步法/)                                |  10   | Dark tech style                                       |
|                         | [Chongqing University Thesis Format](./skills/ppt_master_workflow/examples/ppt169_通用灵活+学术_重庆大学论文格式标准/)          |  11   | Academic standards guide                              |
| ✨ **Creative Style**   | [I Ching Qian Hexagram Study](./skills/ppt_master_workflow/examples/ppt169_易理风_地山谦卦深度研究/)                            |  20   | I Ching aesthetics, Yin-Yang design                   |
|                         | [Diamond Sutra Chapter 1 Study](./skills/ppt_master_workflow/examples/ppt169_禅意风_金刚经第一品研究/)                          |  15   | Zen academic, ink wash whitespace                     |
|                         | [Git Introduction Guide](./skills/ppt_master_workflow/examples/ppt169_像素风_git_introduction/)                                 |  10   | Pixel retro game style                                |

📖 [View Complete Examples Documentation](./skills/ppt_master_workflow/examples/README.md)

---

## 🏗️ System Architecture

```
User Input (PDF/URL/Markdown)
    ↓
[Source Content Conversion] → pdf_to_md.py / web_to_md.py
    ↓
[Create Project] → project_manager.py init <project_name> --format <format>
    ↓
[Template Option] A) Use existing template B) No template
    ↓
[Need New Template?] → Use /create-template workflow separately
    ↓
[Strategist] - Eight Confirmations & Design Specifications
    ↓
[Image_Generator] (When AI generation is selected)
    ↓
[Executor] - Two-Phase Generation
    ├── Visual Construction Phase: Generate all SVG pages → svg_output/
    └── Logic Construction Phase: Generate complete script → notes/total.md
    ↓
[Post-processing] → total_md_split.py (split notes) → finalize_svg.py → svg_to_pptx.py
    ↓
Output: SVG + PPTX (auto-embeds notes)
    ↓
[Optimizer_CRAP] (Optional, only if the first full draft is unsatisfactory)
    ↓
If optimized: re-run post-processing and export
```

> 📖 For detailed workflow, see [Workflow Tutorial](./skills/ppt_master_workflow/docs/workflow_tutorial.md) and [Role Definitions](./skills/ppt_master_workflow/roles/README.md)

> 💡 **PPT Editing Tip**: The exported PPTX pages are in SVG format. To edit the content, select the page content in PowerPoint, right-click and choose **"Group" -> "Ungroup"** (or **"Convert to Shape"**). This feature requires **Office 2016** or later.

---

## 🛠️ Common Commands

```bash
# Initialize project
python3 skills/ppt_master_workflow/commands/project_manager.py init <project_name> --format ppt169

# PDF to Markdown
python3 skills/ppt_master_workflow/commands/pdf_to_md.py <PDF_file>

# Post-process SVG
python3 skills/ppt_master_workflow/commands/finalize_svg.py <project_path>

# Export PPTX
python3 skills/ppt_master_workflow/commands/svg_to_pptx.py <project_path> -s final
```

> 📖 For complete tool documentation, see [Tools Usage Guide](./skills/ppt_master_workflow/commands/README.md)

---

## 📁 Project Structure

```
ppt-master/
├── skills/
│   └── ppt_master_workflow/
│       ├── commands/    # Canonical CLI entry points
│       ├── pptmaster/   # Shared Python core
│       ├── docs/        # Workflow documentation
│       ├── roles/       # Role protocols
│       ├── templates/   # Layouts, charts, icons, style assets
│       ├── examples/    # Built-in example projects
│       └── workflows/   # Workflow entry documents
├── workspace/          # User project workspace
├── AGENTS.md           # Minimal bootstrap entry for AI agents
├── README.md           # Repository landing page (English default)
├── README_CN.md        # Chinese landing page
└── README_EN.md        # English compatibility alias
```

- The repository root stays minimal and keeps only entry files plus `workspace/`.
- All implementation, commands, docs, templates, and examples live under `skills/ppt_master_workflow/` as the single source of truth.
- In day-to-day usage, call commands directly from `skills/ppt_master_workflow/commands/`.

---

## ❓ FAQ

<details>
<summary><b>Q: How to use generated SVG files?</b></summary>

- Open directly in browser to view
- Export to PowerPoint using `svg_to_pptx.py` (Note: Requires "Convert to Shape" in PPT for editing, Office 2016+ required)
- Embed in HTML pages or edit with design tools

</details>

<details>
<summary><b>Q: What's the difference between the three Executors?</b></summary>

- **Executor_General**: General scenarios, flexible layout
- **Executor_Consultant**: General consulting, data visualization
- **Executor_Consultant_Top**: Top consulting (MBB level), 5 core techniques

</details>

<details>
<summary><b>Q: Is Optimizer_CRAP required?</b></summary>

No. Only use it when you need to optimize the visual effects of key pages.

</details>

> 📖 For more questions, see [Workflow Tutorial](./skills/ppt_master_workflow/docs/workflow_tutorial.md#faq)

---

## 🤝 Contributing

Contributions are welcome!

1. Fork this repository
2. Create your branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

**Contribution Areas**: 🎨 Design templates · 📊 Chart components · 📝 Documentation · 🐛 Bug reports · 💡 Feature suggestions

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- [SVG Repo](https://www.svgrepo.com/) - Open source icon library
- [Robin Williams](https://en.wikipedia.org/wiki/Robin_Williams_(author)) - CRAP design principles
- McKinsey, Boston Consulting, Bain - Design inspiration

## 📮 Contact

- **Current Repository**: [funenc-lab/ppt-master](https://github.com/funenc-lab/ppt-master)
- **Issue**: [GitHub Issues](https://github.com/funenc-lab/ppt-master/issues)
- **Fork Source**: [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master)
- **Upstream Author**: [@hugohe3](https://github.com/hugohe3)

---

## 🌟 Star History

If this project helps you, please give it a ⭐ Star!

<a href="https://star-history.com/#funenc-lab/ppt-master&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=funenc-lab/ppt-master&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=funenc-lab/ppt-master&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=funenc-lab/ppt-master&type=Date" />
 </picture>
</a>

---

Made with ❤️ by Hugo He

[⬆ Back to Top](#ppt-master---ai-powered-multi-format-svg-content-generation-system)
