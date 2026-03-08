# 文档中心

[English](./README.md) | 中文

本目录存放 `skills/ppt_master_workflow/` 的支持性文档，用于解释工作流、设计规范、图片规范、导出与操作手册。

## 当前规范

- **唯一 workflow source of truth**：`skills/ppt_master_workflow/`
- **完整规则手册入口**：[`../AGENTS.md`](../AGENTS.md)
- **工作流入口文档**：[`../workflows/generate-ppt.md`](../workflows/generate-ppt.md)
- **命令入口目录**：[`../commands/`](../commands/)
- **共享 Python 核心**：[`../pptmaster/`](../pptmaster/)

## 📖 文档列表

### 工作流与操作

- [workflow_tutorial.md](./workflow_tutorial.md) - 工作流教程与案例演示
- [ppt_workflow_operator_manual.md](./ppt_workflow_operator_manual.md) - 面向执行者的操作手册与检查清单
- [quick_reference.md](./quick_reference.md) - 常用命令与参数速查

### 设计与画布

- [canvas_formats.md](./canvas_formats.md) - 画布格式规范
- [design_guidelines.md](./design_guidelines.md) - 设计规范详解
- [image_layout_spec.md](./image_layout_spec.md) - 图片布局与页面图片策略
- [svg_image_embedding.md](./svg_image_embedding.md) - SVG 图片嵌入指南

### 图片与媒体能力

- [image_stock_sources.md](./image_stock_sources.md) - 商用图库来源与 manifest 规范
- [image_generation_providers.md](./image_generation_providers.md) - 图片生成 provider 注册表与环境变量
- [image_generation_setup.md](./image_generation_setup.md) - 图片生成能力配置与命令示例
- [ark_video_generation.md](./ark_video_generation.md) - ARK 图生视频任务说明与示例

### 架构与维护

- [architecture/repository_structure.md](./architecture/repository_structure.md) - 当前仓库结构与 source-of-truth 约束
- [plans/2026-03-07-repo-structure-reorg.md](./plans/2026-03-07-repo-structure-reorg.md) - 目录重构计划与背景说明

## 🔗 其他资源

- [角色定义](../roles/README_CN.md)
- [工作流索引](../workflows/README.md)
- [图表模板](../templates/charts/README.md)
- [图标库](../templates/icons/README.md)
- [工具说明](../commands/README_CN.md)
- [OCR Image to Markdown skill](../../../.agent/skills/ocr_image_to_markdown/SKILL.md) - 图片型源内容转 Markdown 的 skill 入口

## 维护规则

- 优先更新 canonical 文档，不要在平行目录复制同一套说明。
- 工作流规则变更时，先更新 `../AGENTS.md` 与 `../workflows/generate-ppt.md`。
- 命令、实现与文档说明不一致时，以 `../commands/` 与 `../pptmaster/` 的现状为准并回补文档。
- 示例统计信息优先通过 canonical 命令自动刷新，不要手改生成文件。
