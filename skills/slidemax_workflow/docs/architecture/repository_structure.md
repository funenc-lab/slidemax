# 仓库结构与扩展边界

## 目标

本次整理的目标是在 **skill-only canonical structure** 下收敛共享代码边界，降低后续扩展时的脚本级耦合。

## 当前推荐结构

```text
skills/
└── slidemax_workflow/  # Workflow-facing skill package
    ├── SKILL.md          # Skill entry description
    ├── AGENTS.md         # Canonical workflow rules
    ├── commands/         # Canonical CLI scripts
    ├── slidemax/        # Canonical shared Python core
    ├── roles/            # Role protocols
    ├── workflows/        # Workflow entry documents
    ├── docs/             # Canonical documentation set
    ├── templates/        # Canonical layout/chart/icon assets
    ├── examples/         # Canonical built-in sample projects
    └── references/       # Local reference hub
AGENTS.md                 # Minimal bootstrap that points to skills/slidemax_workflow/AGENTS.md
README.md                 # Repository landing page (English default)
README_CN.md              # Repository landing page (Chinese)
README_EN.md              # English compatibility alias
workspace/                # User project workspace (gitignored)
```

## 设计原则

### 1. Skill owns workflow-facing assets

- `skills/slidemax_workflow/commands/` 是用户可执行命令的真实位置。
- `skills/slidemax_workflow/slidemax/` 是共享 Python 核心的真实位置。
- `skills/slidemax_workflow/roles/`、`workflows/`、`docs/`、`templates/`、`examples/` 是相应资源的真实位置。
- 样式资产（layouts、charts、icons、design spec references）统一收口在 `skills/slidemax_workflow/templates/`。
- 根目录只保留最小入口文件与 `workspace/`，真实实现与资源全部收口在 skill 内。

### 2. Package-first imports

- 新代码优先从 `slidemax.*` 导入共享能力。
- 新增 CLI 时，优先落在 `skills/slidemax_workflow/commands/`。
- 共享逻辑优先沉到 `skills/slidemax_workflow/slidemax/`，CLI 只负责参数解析和编排。

### 3. Skill-only source of truth

- 所有工作流命令、共享核心、角色、文档、模板、示例都只在 `skills/slidemax_workflow/` 内演进。
- 根目录不再保留脚本、目录别名或包装层。
- 用户工作区与实现资源严格分离。

## 现阶段扩展点

### Skill 扩展

- `skills/slidemax_workflow/SKILL.md`
- `skills/slidemax_workflow/workflows/`
- `skills/slidemax_workflow/references/`
- 适合新增：skill 元数据、执行约束、资源导航、工作流分层说明

### 配置扩展

- `slidemax.config`
- 适合新增：画布格式、配色方案、版式约束、共享路径策略
- 内置示例根目录通过 `get_example_dirs()` 统一发现，默认包含 skill 内置 `skills/slidemax_workflow/examples/`，并可通过环境变量 `SLIDEMAX_EXTRA_EXAMPLE_PATHS` 追加外部样例根目录
- `SLIDEMAX_EXTRA_EXAMPLE_PATHS` 使用系统路径分隔符（macOS/Linux 为 `:`，Windows 为 `;`）

### 项目领域扩展

- `slidemax.project_utils`
- 适合新增：项目命名解析、结构校验、元数据索引、批量扫描能力

### 错误与诊断扩展

- `slidemax.error_helper`
- 适合新增：统一错误码、分级诊断、机器可读错误输出

### 后处理编排扩展

- `slidemax.finalize`
- `slidemax.finalize_steps`
- `slidemax.finalizers.*`
- `slidemax.svg_processing.*`
- `slidemax.svg_processing.image_utils`
- `slidemax.svg_positioning`
- 当前推荐做法：CLI 只解析参数，步骤定义注册在 `finalize_steps`，单步实现放在 `finalizers`，可复用 SVG/图片算法放在 `svg_processing`，共享图片基础设施放在 `image_utils`
- 已迁移到共享算法的步骤：`embed-icons`、`crop-images`、`fix-aspect`、`embed-images`、`flatten-text`、`fix-rounded`
- 适合新增：步骤注册、分阶段执行、批量统计、可选 pipeline profile

### 坐标计算 CLI 扩展

- `slidemax.svg_position_cli`
- 适合新增：命令解析、交互式向导、SVG 分析报告、JSON 配置编排

### SVG 后处理 CLI 扩展

- `slidemax.flatten_text_cli`
- `slidemax.rounded_rect_cli`
- `slidemax.svg_asset_cli`
- `slidemax.svg_processing.flatten_text`
- `slidemax.svg_processing.rounded_rects`
- 适合新增：交互式路径输入、目录遍历策略、更多单步 SVG 后处理命令

### 图片分析扩展

- `slidemax.image_analysis`
- 适合新增：图片目录扫描、布局建议策略、Markdown 清单渲染、CSV 导出策略

### 图片清理扩展

- `slidemax.watermark_removal`
- 适合新增：水印资源定位、检测规则、像素恢复算法、批量图片清理编排

### 商用图库扩展

- `slidemax.stock_sources`
- 当前同时承载：provider 注册表、manifest 结构、下载策略，以及库存图命令编排辅助函数
- 适合新增：provider 注册表、manifest 结构、下载策略、素材登记/下载 CLI 编排

### 视频生成扩展

- `slidemax.video_generation`
- 适合新增：provider 配置解析、request 模型、轮询策略、下载策略、视频任务 CLI 编排

### 输入转换扩展

- `slidemax.web_markdown`
- 适合新增：URL 抓取策略、正文识别规则、图片本地化、Markdown 文档渲染、批量 URL 执行
- `slidemax.pdf_markdown`
- 适合新增：PDF 字体分析、标题推断、页眉页脚降噪、图片与表格抽取、批量目录执行

### 图片方向修正扩展

- `slidemax.image_rotation`
- 适合新增：EXIF 归一化、预览页渲染、任务文件解析、路径解析策略、批量旋转执行

### 示例索引扩展

- `slidemax.examples_index`
- 适合新增：examples 根目录扫描、索引渲染、资源链接策略、外部 examples 根兼容策略

### 讲稿拆分扩展

- `slidemax.notes_splitter`
- 适合新增：标题匹配策略、SVG 映射校验、notes 文件拆分与输出命名策略

### 文本扁平化 CLI 扩展

- `slidemax.flatten_text_cli`
- 适合新增：交互式路径输入、目录递归处理、输出路径策略

### 圆角矩形转换 CLI 扩展

- `slidemax.rounded_rect_cli`
- 适合新增：项目模式扫描、输出目录策略、批量转换统计

### SVG 质量检查扩展

- `slidemax.svg_quality`
- 适合新增：规则集合、问题分类、目录扫描、报告格式与批量项目校验

### 批量项目校验扩展

- `slidemax.batch_validation`
- 适合新增：目录选择策略、项目聚合校验、摘要统计、退出码策略与文本报告导出

### 项目管理扩展

- `slidemax.project_management`
- 适合新增：项目初始化策略、README 模板、单项目校验编排、信息摘要输出

### 商用图库 CLI 扩展

- 当前命令桥接直接复用 `slidemax.stock_sources` 中的 CLI helper
- 适合新增：provider 列表输出、参数解析、下载与登记编排、CLI 入口复用

### 视频生成 CLI 扩展

- `slidemax.video_generation_cli`
- 适合新增：子命令解析、任务状态输出、下载命令编排

### 导出服务扩展

- `slidemax.pptx_export`
- `slidemax.pptx_animations`
- 适合新增：导出请求模型、输出命名策略、notes 策略、切换/动画 XML 生成、不同导出后端

### 导出子模块扩展

- `slidemax.exporters.*`
- 当前推荐入口：`slidemax.exporters.pptx_runtime.export_presentation`
- 适合新增：OpenXML 构造、媒体处理、格式适配、不同 Office 兼容策略

## 后续建议

1. 为 `skills/slidemax_workflow/workflows/` 增加更细粒度的专题 workflow
2. 为 `slidemax.*` 补充自动化测试，并持续保持 `commands/` 作为 thin CLI wrappers
3. 保持根目录最小化，只在 skill 内持续演进 workflow 能力


### 4. GitHub-facing README convention

- GitHub 默认展示的 `README.md` 统一使用英文入口页。
- 中文文档放在同目录的 `README_CN.md`，并在页首提供双向切换。
- `README_EN.md` 仅保留为英文兼容别名页，避免旧链接失效。
