# 仓库结构整理实施记录

> **目标**：在不破坏现有工作流与 CLI 用法的前提下，收敛共享代码边界，给后续扩展建立稳定命名空间。

> **状态说明（2026-03-07）**：本文档保留了整理过程中的阶段性记录。凡提到根目录兼容链接、`tools/` 别名或中间迁移态的条目，均应以当前的 **skill-only** 结构为准。

## 本次实施内容

1. 新增 `skills/ppt_master_workflow/` 作为 workflow-facing skill 容器
2. 将用户可执行脚本、角色协议与工作流文档收口到 skill 内
3. 将共享 Python 核心迁移到 `skills/ppt_master_workflow/pptmaster/`
4. 将文档、模板、规则文件迁移到 skill 内
5. 将内置 examples 迁移到 skill 内
6. 在根目录仅保留必要仓库说明文件与 bootstrap 入口，避免重新引入兼容链接层
7. 补充仓库结构与扩展边界文档
8. 将 `finalize_svg.py` 与 `svg_to_pptx.py` 的 CLI/service 边界拆开
9. 将 skill 内 canonical CLI 目录标准化为 `commands/`
10. 为 skill 新增 `references/` 作为规则、文档、模板的统一引用入口

## 本次没有做的事

1. 没有改动核心工作流语义
2. 没有修改用户可见命令格式
3. 没有重写 `finalize_svg.py` 与 `svg_to_pptx.py` 的内部逻辑
4. 没有引入新的打包或发布机制

## 下一阶段建议

1. 继续将 workflow 说明按 skill 维度拆分，而不是集中堆在根级说明中
2. 为 `pptmaster/` 增加自动化测试
3. 将导出器、校验器、项目模型进一步模块化

## 增量进展（继续整理）

1. 将 `svg_to_pptx.py` 的导出主循环进一步下沉到 `pptmaster.exporters.pptx_runtime`
2. 将 CLI 入口收敛为依赖检查 + 请求组装 + 共享服务调用
3. 修复 package 结构下继续演进时的扩展锚点，使导出运行时成为明确边界

## 增量进展（继续整理：finalize）

1. 新增 `pptmaster.finalize_steps`，将后处理步骤定义与 handler 从 `finalize.py` 中拆出
2. 将 `FinalizeOptions` 从固定布尔字段改为步骤列表模型，新增步骤时不再需要同步修改 dataclass 字段
3. 保持 `finalize_svg.py` CLI 用法不变，仅优化内部扩展边界

## 增量进展（继续整理：finalizers）

1. 新增 `pptmaster.finalizers` 子包，将各后处理步骤的单文件执行逻辑独立封装
2. `finalize_steps` 仅保留步骤元数据与注册关系，不再混合具体实现细节
3. 为后续逐步替换 legacy 顶层脚本建立更自然的迁移路径

## 增量进展（继续整理：svg-processing）

1. 新增 `pptmaster.svg_processing` 子包，承载纯 SVG 处理算法
2. 将 `flatten_tspan.py` 与 `svg_rect_to_path.py` 的核心能力迁移到共享模块
3. 顶层脚本改为薄 CLI 封装，`finalizers` 直接复用共享算法而非再依赖 legacy 动态导入

## 增量进展（继续整理：icons-and-images）

1. 新增 `pptmaster.svg_processing.icons` 与 `pptmaster.svg_processing.embed_images`
2. 将 `embed_icons.py` 与 `embed_images.py` 的核心逻辑迁移到共享模块，顶层脚本改为薄 CLI
3. `finalizers.embed_icons` 与 `finalizers.embed_images` 已改为直接调用共享核心，不再依赖 legacy 动态导入

## 增量进展（继续整理：crop-and-aspect）

1. 新增 `pptmaster.svg_processing.crop_images` 与 `pptmaster.svg_processing.image_aspect`
2. 将 `crop_images.py` 与 `fix_image_aspect.py` 的核心逻辑迁移到共享模块，顶层脚本改为薄 CLI
3. `finalizers.crop_images` 与 `finalizers.fix_aspect` 已改为直接调用共享核心，`finalize` 6 个步骤全部脱离 legacy 动态导入

## 增量进展（继续整理：image-utils）

1. 新增 `pptmaster.svg_processing.image_utils`，统一 Pillow 检测、图片尺寸读取、MIME 推断、SVG 资源路径解析
2. `embed_images`、`crop_images`、`fix_image_aspect` 已改为复用共享图片工具，减少重复实现
3. 共享图片能力形成独立扩展边界，后续新增图片型步骤可直接复用

## 增量进展（继续整理：core-packaging)

1. `pptmaster.config`、`pptmaster.project_utils`、`pptmaster.error_helper` 已成为真实共享实现
2. `commands/config.py`、`commands/project_utils.py`、`commands/error_helper.py` 已收敛为 thin command wrappers
3. 已移除 `pptmaster/_legacy.py` 与对应动态导入链路

## 增量进展（继续整理：pptx-animations）

1. `pptmaster.pptx_animations` 已成为动画与切换 XML 的真实共享实现
2. `commands/pptx_animations.py` 已收敛为兼容桥接层
3. `svg_to_pptx.py` 已直接依赖 package 内动画模块，导出链路进一步收口到 `pptmaster/`

## 增量进展（继续整理：svg-positioning）

1. `pptmaster.svg_positioning` 已成为图表坐标计算与 SVG 坐标校验的真实共享实现
2. `commands/svg_position_calculator.py` 已移除大块计算类定义，保留 CLI、分析与交互流程
3. 坐标系统、图表计算器、SVG 校验器与解析辅助函数已具备更清晰的复用边界

## 增量进展（继续整理：examples-indexing）

1. `pptmaster.examples_index` 已成为 examples 根目录索引生成的真实共享实现
2. `commands/generate_examples_index.py` 已收敛为薄桥接层
3. examples 扫描、资源链接生成与 README 渲染边界已从命令层下沉到共享服务层

## 增量进展（继续整理：image-analysis）

1. `pptmaster.image_analysis` 已成为图片目录扫描与分析输出的真实共享实现
2. `commands/analyze_images.py` 已收敛为薄桥接层
3. 布局建议、Markdown 清单与 CSV 输出边界已从命令层下沉到共享服务层

## 增量进展（继续整理：image-rotation）

1. `pptmaster.image_rotation` 已成为图片方向修正与预览生成的真实共享实现
2. `commands/rotate_images.py` 已收敛为薄桥接层
3. EXIF 归一化、预览页渲染、任务路径解析与批量旋转边界已从命令层下沉到共享服务层

## 增量进展（继续整理：web-markdown）

1. `pptmaster.web_markdown` 已成为网页抓取与 Markdown 转换的真实共享实现
2. `commands/web_to_md.py` 已收敛为薄桥接层
3. URL 抓取、正文识别、图片下载与 Markdown 渲染边界已从命令层下沉到共享服务层

## 增量进展（继续整理：pdf-markdown）

1. `pptmaster.pdf_markdown` 已成为 PDF 结构提取与 Markdown 渲染的真实共享实现
2. `commands/pdf_to_md.py` 已收敛为薄桥接层
3. 字体分析、标题推断、页眉页脚降噪、图片/表格抽取与目录批处理边界已从命令层下沉到共享服务层

## 增量进展（继续整理：notes-splitter）

1. `pptmaster.notes_splitter` 已成为讲稿标题匹配与拆分写入的真实共享实现
2. `commands/total_md_split.py` 已收敛为薄桥接层
3. 标题匹配、SVG 映射校验与 notes 文件输出边界已从命令层下沉到共享服务层

## 增量进展（继续整理：svg-quality）

1. `pptmaster.svg_quality` 已成为 SVG 规范校验与报告输出的真实共享实现
2. `commands/svg_quality_checker.py` 已收敛为薄桥接层
3. 规则检查、问题分类、目录扫描与报告导出边界已从命令层下沉到共享服务层

## 增量进展（继续整理：batch-validation）

1. `pptmaster.batch_validation` 已成为项目聚合校验与摘要输出的真实共享实现
2. `commands/batch_validate.py` 已收敛为薄桥接层
3. 目录扫描、项目聚合、退出码策略与报告导出边界已从命令层下沉到共享服务层

## 增量进展（继续整理：project-management）

1. `pptmaster.project_management` 已成为项目初始化、项目校验与信息摘要输出的真实共享实现
2. `commands/project_manager.py` 已收敛为薄桥接层
3. 项目创建、单项目校验与 CLI 输出编排边界已从命令层下沉到共享服务层

## 增量进展（继续整理：watermark-removal）

1. `pptmaster.watermark_removal` 已成为 Gemini 水印检测、资源定位与像素恢复的真实共享实现
2. `commands/gemini_watermark_remover.py` 已收敛为薄桥接层
3. 水印模板资源已从 `commands/assets/` 收口到 `pptmaster/assets/`

## 增量进展（继续整理：svg-position-cli）

1. `pptmaster.svg_position_cli` 已成为 SVG 坐标工具的共享 CLI 编排与分析实现
2. `commands/svg_position_calculator.py` 已收敛为薄桥接层
3. 交互模式、SVG 分析、JSON 配置编排已从命令层下沉到共享服务层

## 增量进展（继续整理：pptx-export）

1. `pptmaster.pptx_export` 已成为 PPTX 导出 CLI 编排、依赖装配与入口实现
2. `commands/svg_to_pptx.py` 已收敛为薄桥接层
3. 导出依赖检查、转场解析与 native SVG 导出装配已从命令层下沉到共享服务层

## 增量进展（继续整理：stock-sources-cli）

1. `pptmaster.stock_sources_cli` 已成为库存图下载与登记命令的共享 CLI 编排实现
2. `commands/register_stock_image.py` 与 `commands/download_stock_image.py` 已收敛为薄桥接层
3. provider 列表、参数校验、下载登记编排已从命令层下沉到共享服务层

## 增量进展（继续整理：flatten-text-cli）

1. `pptmaster.flatten_text_cli` 已成为文本扁平化命令的共享 CLI 编排实现
2. `commands/flatten_tspan.py` 已收敛为薄桥接层
3. 交互式输入、目录递归与输出路径编排已从命令层下沉到共享服务层

## 增量进展（继续整理：rounded-rects-cli）

1. `pptmaster.rounded_rect_cli` 已成为圆角矩形转 Path 命令的共享 CLI 编排实现
2. `commands/svg_rect_to_path.py` 已收敛为薄桥接层
3. 项目模式扫描、输出目录策略与批量统计已从命令层下沉到共享服务层

## 增量进展（继续整理：video-generation-cli）

1. `pptmaster.video_generation_cli` 已成为 Doubao 视频生成命令的共享 CLI 编排实现
2. `commands/doubao_i2v_task.py` 已收敛为薄桥接层
3. 子命令解析、状态输出与下载编排已从命令层下沉到共享服务层


## 增量进展（继续整理：skill-packaging）

1. 新增 `skills/ppt_master_workflow/SKILL.md` 作为仓库内 skill 入口
2. 将 `roles/`、`workflows/`、`docs/`、`templates/`、`examples/`、`AGENTS.md`、`CLAUDE.md`、`GEMINI.md` 迁移为 skill 内真实资源
3. 将 `tools/` 下用户可执行命令迁移为 skill 内真实资源，随后移除根目录兼容链接
4. 将共享核心迁移到 `skills/ppt_master_workflow/pptmaster/`，并收敛为 skill 内唯一共享核心
5. 将 skill 内 canonical CLI 目录统一为 `commands/`，并移除 skill 内 `tools/` 兼容别名
6. 将 `.agent/workflows/` 迁移为 skill 内真实资源，随后移除根目录兼容链接
7. 为规则、文档、模板新增 `references/` 统一入口


## 增量进展（继续整理：svg-processing-cli）

1. `pptmaster.rounded_rect_cli` 与 `pptmaster.flatten_text_cli` 已成为简单 SVG 后处理命令的共享 CLI 编排层
2. `commands/svg_rect_to_path.py` 与 `commands/flatten_tspan.py` 已收敛为薄桥接层
3. 项目目录遍历、交互输入与输出摘要已从命令层下沉到共享服务层


## 增量进展（继续整理：svg-asset-cli）

1. `pptmaster.svg_asset_cli` 已成为图片裁剪、图标嵌入、图片嵌入与宽高比修复命令的共享 CLI 编排层
2. `commands/crop_images.py`、`commands/embed_icons.py`、`commands/fix_image_aspect.py`、`commands/embed_images.py` 已收敛为薄桥接层
3. 参数解析、文件遍历与摘要输出已从命令层下沉到共享服务层


## 增量进展（继续整理：image-generation-compat）

1. `pptmaster.image_generation` 已吸收 Gemini 兼容入口与 provider smoke test CLI 编排
2. `commands/nano_banana_gen.py` 与 `commands/smoke_test_image_provider.py` 已进一步收敛为薄桥接层
3. 兼容包装、smoke parser 与 smoke 执行路径已从命令层下沉到共享服务层


## 增量进展（继续整理：image-analysis-cli）

1. `pptmaster.image_analysis` 已补齐标准 parser/main 入口
2. `commands/analyze_images.py` 已收敛为薄桥接层
3. 手写 `sys.argv` 分发已从命令层下沉到共享服务层


## 增量进展（继续整理：dedupe-rounded-rect-cli）

1. 移除重复共享模块 `pptmaster.rounded_rects_cli`，统一保留 `pptmaster.rounded_rect_cli` 作为 canonical 名称
2. `pptmaster.__init__` 与架构文档已同步去除旧导出与旧命名
3. 圆角矩形 CLI 的扩展边界统一收口到 `rounded_rect_cli`

## 增量进展（继续整理：dedupe-svg-postprocess-cli）

1. 移除未被命令入口使用的重复共享模块 `pptmaster.svg_postprocess_cli`
2. 统一由 `pptmaster.flatten_text_cli`、`pptmaster.rounded_rect_cli` 与 `pptmaster.svg_asset_cli` 承担对应后处理命令编排
3. 架构文档已修正为当前真实 canonical 模块
