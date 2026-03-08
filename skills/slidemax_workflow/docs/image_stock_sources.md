# 商用图库来源指南

本文档定义 SlideMax 中第三方商用图库图片的来源登记规则。

## 目标

- 将第三方图库图片纳入标准工作流，而不是散落在聊天记录中
- 对每张图库图片保存来源、许可证、作者和本地路径
- 确保 Executor 始终引用项目本地图片，而不是外部热链

## 当前支持的图库来源

### 1. Unsplash

- 官网：<https://unsplash.com>
- 许可证页面：<https://unsplash.com/license>
- 适合：封面背景、办公场景、生活方式照片
- 当前工作流建议：下载到本地后登记到 `images/stock/manifest.json`

### 2. Pexels

- 官网：<https://www.pexels.com>
- 许可证页面：<https://www.pexels.com/license/>
- 适合：人物、商业场景、营销配图
- 当前工作流建议：下载到本地后登记到 `images/stock/manifest.json`

### 3. Pixabay

- 官网：<https://pixabay.com>
- 许可证摘要页：<https://pixabay.com/service/license-summary/>
- 适合：照片、插画、矢量素材
- 当前工作流建议：下载到本地后登记到 `images/stock/manifest.json`

> ⚠️ 以上链接和条款应在实际交付前再次到官方页面复核。本文档只提供 workflow 级登记规则，不构成法律意见。

---

## 目录约定

```text
<项目路径>/
├── images/
│   └── stock/
│       ├── manifest.json
│       ├── cover_bg.jpg
│       └── section_hero.jpg
```

- `images/stock/`：保存所有本地化后的图库图片
- `images/stock/manifest.json`：保存来源登记表

---

## manifest 字段

`manifest.json` 中每条记录至少包含：

| 字段 | 说明 |
|------|------|
| `filename` | 本地文件名 |
| `local_path` | 相对项目根目录的路径 |
| `source_type` | 固定为 `stock` |
| `source_provider` | 图库提供方 |
| `source_url` | 原始素材页面 |
| `creator_name` | 作者/摄影师 |
| `creator_url` | 作者主页 |
| `license_name` | 许可证名称 |
| `license_url` | 许可证页面 |
| `commercial_use_allowed` | 是否允许商用 |
| `attribution_required` | 是否要求署名 |
| `restriction_notes` | 使用限制说明 |
| `verification_note` | 复核提示 |
| `downloaded_at` | 登记时间 |
| `keywords` | 关键词列表 |

---

## 推荐命令

### 列出支持的图库来源

```bash
python3 skills/slidemax_workflow/commands/register_stock_image.py --list-providers
```

### 直接下载并登记一张图库图片

```bash
python3 skills/slidemax_workflow/commands/download_stock_image.py <项目路径> \
  --provider pexels \
  --source-url "https://www.pexels.com/photo/example-id/" \
  --download-url "https://images.pexels.com/photos/example.jpeg" \
  --filename hero_cover.jpeg
```

### 登记一张已下载的图库图片

```bash
python3 skills/slidemax_workflow/commands/register_stock_image.py <项目路径> \
  --provider unsplash \
  --source-url "https://unsplash.com/photos/example-id" \
  --local-file "/absolute/path/to/downloaded/hero.jpg" \
  --filename hero_cover.jpg \
  --creator-name "Photographer Name"
```

### 登记项目内已存在的图片

```bash
python3 skills/slidemax_workflow/commands/register_stock_image.py <项目路径> \
  --provider pexels \
  --source-url "https://www.pexels.com/photo/example-id/" \
  --local-path images/stock/section_hero.jpg
```

---

## Strategist / Executor 规则

### Strategist

- 若图片来源选择“商用图库”，必须在《设计规范与内容大纲》中写明：
  - 来源类型：商用图库
  - 来源提供方：Unsplash / Pexels / Pixabay
  - 图片用途与页面位置
  - 本地文件名

### Executor

- Executor 只引用本地路径，例如：

```xml
<image href="../images/stock/hero_cover.jpg" x="0" y="0" width="1280" height="720" preserveAspectRatio="xMidYMid slice"/>
```

- 不直接引用第三方网页 URL

---

## 示例文件

- 配置示例：`../examples/config/slidemax_stock.env.example`
- 命令示例：`../examples/config/register_stock_image.sh.example`
- 下载并登记示例：`../examples/config/download_stock_image.sh.example`
