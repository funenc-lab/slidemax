# SlideMax - AI 驱动的多格式 SVG 内容生成系统

[![Version](https://img.shields.io/badge/version-v1.2.0-blue.svg)](https://github.com/funenc-lab/slidemax/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/funenc-lab/slidemax.svg)](https://github.com/funenc-lab/slidemax/stargazers)

[English](./README.md) | 中文

一个基于 AI 的智能视觉内容生成系统，通过多角色协作，将源文档转化为高质量的 SVG 内容，**支持演示文稿、社交媒体、营销海报等多种格式**。

> 🎴 **在线示例**：[GitHub Pages 在线预览](https://funenc-lab.github.io/slidemax/) - 查看实际生成效果

> 🎬 **快速示例**：[YouTube](https://www.youtube.com/watch?v=jM2fHmvMwx0) | [Bilibili](https://www.bilibili.com/video/BV1iUmQBtEGH/) - 观看视频演示

## 🧭 仓库说明

- **当前维护仓库**：[`funenc-lab/slidemax`](https://github.com/funenc-lab/slidemax)
- **Fork 来源 / 上游公开仓库**：[`hugohe3/ppt-master`](https://github.com/hugohe3/ppt-master)
- **本地 Git `origin`（当前工作仓库）**：`git@github.com:funenc-lab/slidemax.git`
- **说明**：产品品牌已统一为 SlideMax，当前维护仓库 slug 也已切换为 `slidemax`；部分历史链接与公开上游 fork 仍继续使用 `ppt-master`。

---

## 🚀 快速开始

### 1. 配置环境

#### Python 环境（必需）

本项目需要 **Python 3.8+**，用于运行 PDF 转换、SVG 后处理、PPTX 导出等工具。

**安装 Python：**

| 平台 | 推荐安装方式 |
|------|------------|
| **macOS** | 使用 [Homebrew](https://brew.sh/)：`brew install python` |
| **Windows** | 从 [Python 官网](https://www.python.org/downloads/) 下载安装包 |
| **Linux** | 使用系统包管理器：`sudo apt install python3 python3-pip`（Ubuntu/Debian） |

> 💡 **验证安装**：运行 `python3 --version` 确认版本 ≥ 3.8

#### Node.js 环境（可选）

如需使用 `web_to_md.cjs` 工具（用于微信公众号等高防站点的网页转换），需安装 Node.js。

**安装 Node.js：**

| 平台 | 推荐安装方式 |
|------|------------|
| **macOS** | 使用 [Homebrew](https://brew.sh/)：`brew install node` |
| **Windows** | 从 [Node.js 官网](https://nodejs.org/) 下载 LTS 版本安装包 |
| **Linux** | 使用 [NodeSource](https://github.com/nodesource/distributions)：`curl -fsSL https://deb.nodesource.com/setup_lts.x \| sudo -E bash - && sudo apt-get install -y nodejs` |

> 💡 **验证安装**：运行 `node --version` 确认版本 ≥ 18

### 2. 克隆仓库并安装依赖

```bash
git clone https://github.com/funenc-lab/slidemax.git
cd slidemax
pip install -r requirements.txt
```

> 如遇权限问题，可使用 `pip install --user -r requirements.txt` 或在虚拟环境中安装。

### 3. 打开 AI 编辑器

推荐使用以下 AI 编辑器：

| 工具                                                | 推荐度 | 说明                                                                          |
| --------------------------------------------------- | :----: | ----------------------------------------------------------------------------- |
| **[Antigravity](https://antigravity.dev/)**         | ⭐⭐⭐ | **强烈推荐**！免费使用 Opus 4.6，集成 Banana 生图功能，可直接在仓库里生成配图 |
| [Cursor](https://cursor.sh/)                        |  ⭐⭐  | 主流 AI 编辑器，支持多种模型                                                  |
| [VS Code + Copilot](https://code.visualstudio.com/) |  ⭐⭐  | 微软官方方案                                                                  |
| [Claude Code](https://claude.ai/)                   |  ⭐⭐  | Anthropic 官方 CLI 工具                                                       |

### 4. 开始创作

在 AI 编辑器中打开聊天面板，直接描述你想创作的内容：

```
用户：我有一份关于 Q3 季度业绩的报告，需要制作成 PPT

AI（Strategist 角色）：好的，在开始之前我需要完成八项确认...
   1. 画布格式：[建议] PPT 16:9
   2. 页数范围：[建议] 8-10 页
   ...
```

> 💡 **模型推荐**：Opus 4.6 效果最佳，Antigravity 目前可免费使用

> 💡 **AI 迷失上下文？** 可提示 AI 参考 `AGENTS.md` 文件，它会自动按照仓库中的角色定义工作

> 💡 **AI 生成图片建议**：如需 AI 生成配图，建议在 [Gemini](https://gemini.google.com/) 中生成后选择 **Download full size** 下载，分辨率比 Antigravity 直接生成的更高。Gemini 生成的图片右下角会有星星水印，可使用 [gemini-watermark-remover](https://github.com/journey-ad/gemini-watermark-remover) 或本项目的 `skills/slidemax_workflow/commands/gemini_watermark_remover.py` 去除。

---

## 📚 文档导航

| 文档 | 说明 |
|------|------|
| 🗂️ [文档中心](./skills/slidemax_workflow/docs/README_CN.md) | 规范入口、索引与维护说明 |
| 📖 [工作流教程](./skills/slidemax_workflow/docs/workflow_tutorial.md) | 详细的工作流程和案例演示 |
| 🎨 [设计指南](./skills/slidemax_workflow/docs/design_guidelines.md) | 配色、排版、布局规范详解 |
| 📐 [画布格式](./skills/slidemax_workflow/docs/canvas_formats.md) | PPT、小红书、朋友圈等 10+ 种格式 |
| 🖼️ [图片嵌入指南](./skills/slidemax_workflow/docs/svg_image_embedding.md) | SVG 图片嵌入最佳实践 |
| 📊 [图表模板库](./skills/slidemax_workflow/templates/charts/) | 33 种标准化图表模板 · [在线预览](./skills/slidemax_workflow/templates/charts/preview.html) |
| ⚡ [快速参考](./skills/slidemax_workflow/docs/quick_reference.md) | 常用命令和参数速查 |
| 🔧 [角色定义](./skills/slidemax_workflow/roles/README_CN.md) | 7 个 AI 角色的完整定义 |
| 🛠️ [工具集](./skills/slidemax_workflow/commands/README_CN.md) | 所有工具的使用说明 |
| 💼 [示例索引](./skills/slidemax_workflow/examples/README.md) | 15 个项目、229 页 SVG 示例 |

---

## 🎴 精选示例

> 📁 **示例库**: [`skills/slidemax_workflow/examples/`](./skills/slidemax_workflow/examples/) · **15 个项目** · **229 页 SVG**

| 类别            | 项目                                                                           | 页数 | 特色                              |
| --------------- | ------------------------------------------------------------------------------ | :--: | --------------------------------- |
| 🏢 **咨询风格** | [心理治疗中的依恋](./skills/slidemax_workflow/examples/ppt169_顶级咨询风_心理治疗中的依恋/)             |  32  | 顶级咨询风格，最大规模示例        |
|                 | [构建有效AI代理](./skills/slidemax_workflow/examples/ppt169_顶级咨询风_构建有效AI代理_Anthropic/)       |  15  | Anthropic 工程博客，AI Agent 架构 |
|                 | [重庆市区域报告](./skills/slidemax_workflow/examples/ppt169_顶级咨询风_重庆市区域报告_ppt169_20251213/) |  20  | 区域财政分析，企业预警通数据 🆕   |
|                 | [甘孜州经济财政分析](./skills/slidemax_workflow/examples/ppt169_顶级咨询风_甘孜州经济财政分析/)         |  17  | 政务财政分析，藏区文化元素        |
| 🎨 **通用灵活** | [Debug 六步法](./skills/slidemax_workflow/examples/ppt169_通用灵活+代码_debug六步法/)                   |  10  | 深色科技风格                      |
|                 | [重庆大学论文格式](./skills/slidemax_workflow/examples/ppt169_通用灵活+学术_重庆大学论文格式标准/)      |  11  | 学术规范指南                      |
| ✨ **创意风格** | [地山谦卦深度研究](./skills/slidemax_workflow/examples/ppt169_易理风_地山谦卦深度研究/)                 |  20  | 易经本体美学，阴阳爻变设计        |
|                 | [金刚经第一品研究](./skills/slidemax_workflow/examples/ppt169_禅意风_金刚经第一品研究/)                 |  15  | 禅意学术，水墨留白                |
|                 | [Git 入门指南](./skills/slidemax_workflow/examples/ppt169_像素风_git_introduction/)                     |  10  | 像素复古游戏风                    |

📖 [查看完整示例文档](./skills/slidemax_workflow/examples/README.md)

---

## 🏗️ 系统架构

```
用户输入 (PDF/URL/Markdown)
    ↓
[源内容转换] → pdf_to_md.py / web_to_md.py
    ↓
[创建项目] → project_manager.py init <项目名> --format <格式>
    ↓
[模板选项] A) 使用已有模板 B) 不使用模板
    ↓
[需要新模板？] → 使用 /create-template 工作流单独创建
    ↓
[Strategist] 策略师 - 八项确认与设计规范
    ↓
[Image_Generator] 图片生成师（当选择 AI 生成时）
    ↓
[Executor] 执行师 - 分阶段生成
    ├── 视觉构建阶段：连续生成所有 SVG 页面 → svg_output/
    └── 逻辑构建阶段：生成完整讲稿 → notes/total.md
    ↓
[后处理] → total_md_split.py（拆分讲稿）→ finalize_svg.py → svg_to_pptx.py
    ↓
输出: SVG + PPTX（自动嵌入讲稿）
    ↓
[Optimizer_CRAP] 优化师（可选，初版后不满意再用）
    ↓
如有优化：重新运行后处理与导出
```

> 📖 详细工作流程请参阅 [工作流教程](./skills/slidemax_workflow/docs/workflow_tutorial.md) 和 [角色定义](./skills/slidemax_workflow/roles/README_CN.md)

> 💡 **PPT 编辑提示**：导出的 PPTX 页面为 SVG 格式。若需编辑内容，请在 PowerPoint 中选中页面，右键选择 **"转换为形状"** (Convert to Shape)。此功能需要 **Office 2016** 或更高版本。

---

## 🛠️ 常用命令

```bash
# 初始化项目
python3 skills/slidemax_workflow/commands/project_manager.py init <项目名> --format ppt169

# PDF 转 Markdown
python3 skills/slidemax_workflow/commands/pdf_to_md.py <PDF文件>

# 后处理 SVG
python3 skills/slidemax_workflow/commands/finalize_svg.py <项目路径>

# 导出 PPTX
python3 skills/slidemax_workflow/commands/svg_to_pptx.py <项目路径> -s final
```

> 📖 完整工具说明请参阅 [工具使用指南](./skills/slidemax_workflow/commands/README_CN.md)

---

## 📁 项目结构

```
slidemax/
├── skills/
│   └── slidemax_workflow/
│       ├── commands/    # Canonical CLI entry points
│       ├── slidemax/   # Shared Python core
│       ├── docs/        # Workflow documentation
│       ├── roles/       # Role protocols
│       ├── templates/   # Layouts, charts, icons, style assets
│       ├── examples/    # Built-in example projects
│       └── workflows/   # Workflow entry documents
├── workspace/          # User project workspace
├── AGENTS.md           # Minimal bootstrap entry for AI agents
├── README.md           # 英文默认首页
├── README_CN.md        # 中文首页
└── README_EN.md        # 英文兼容入口
```

- 根目录保持最小化，只保留仓库入口文件与 `workspace/`。
- 所有真实实现、命令、文档、模板、示例都以 `skills/slidemax_workflow/` 为唯一 source of truth。
- 日常使用时请直接调用 `skills/slidemax_workflow/commands/` 下的命令。

---

## ❓ 常见问题

<details>
<summary><b>Q: 生成的 SVG 文件如何使用？</b></summary>

- 直接在浏览器中打开查看
- 使用 `svg_to_pptx.py` 导出为 PowerPoint（需在 PPT 中"转换为形状"以编辑，要求 Office 2016+）
- 嵌入到 HTML 页面或使用设计工具编辑

</details>

<details>
<summary><b>Q: 三种执行师有什么区别？</b></summary>

- **Executor_General**: 通用场景，灵活布局
- **Executor_Consultant**: 一般咨询，数据可视化
- **Executor_Consultant_Top**: 顶级咨询（MBB 级），5 大核心技巧

</details>

<details>
<summary><b>Q: 必须使用 Optimizer_CRAP 吗？</b></summary>

不是必须的。仅在需要优化关键页面视觉效果时使用。

</details>

> 📖 更多问题请查看 [工作流教程](./skills/slidemax_workflow/docs/workflow_tutorial.md#常见问题)

---

## 🤝 贡献指南

欢迎贡献！

1. Fork 本仓库
2. 创建分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

**贡献方向**：🎨 设计模板 · 📊 图表组件 · 📝 文档完善 · 🐛 Bug 报告 · 💡 功能建议

---

## 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。

## 🙏 致谢

- [SVG Repo](https://www.svgrepo.com/) - 开源图标库
- [Robin Williams](https://en.wikipedia.org/wiki/Robin_Williams_(author)) - CRAP 设计原则
- 麦肯锡、波士顿咨询、贝恩 - 设计灵感来源

## 📮 联系方式

- **当前仓库**: [funenc-lab/slidemax](https://github.com/funenc-lab/slidemax)
- **Issue**: [GitHub Issues](https://github.com/funenc-lab/slidemax/issues)
- **Fork 来源**: [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master)
- **上游作者**: [@hugohe3](https://github.com/hugohe3)

---

## 🌟 Star History

如果这个项目对你有帮助，请给一个 ⭐ Star 支持一下！

<a href="https://star-history.com/#funenc-lab/slidemax&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=funenc-lab/slidemax&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=funenc-lab/slidemax&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=funenc-lab/slidemax&type=Date" />
 </picture>
</a>

---

Made with ❤️ by Hugo He

[⬆ 回到顶部](#slidemax---ai-驱动的多格式-svg-内容生成系统)
