# 用户工作区

此目录用于存放进行中的用户项目与运行产物。

## 创建新项目

```bash
python3 skills/slidemax_workflow/commands/project_manager.py init my_project --format ppt169
```

## 目录结构

完成后的项目应包含：

```
project_name_format_YYYYMMDD/
├── README.md
├── 设计规范与内容大纲.md
├── svg_output/
│   ├── 01_cover.svg
│   └── ...
└── images/ (可选)
```

## 注意事项

- 此目录下的内容已被 `.gitignore` 排除
- 完成的项目可以移动到 `skills/slidemax_workflow/examples/` 目录分享
