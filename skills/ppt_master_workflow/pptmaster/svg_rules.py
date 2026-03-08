"""Canonical SVG compatibility rules for PPT Master.

This module is the single source of truth for SVG compatibility constraints,
quality-check detection messages, and ErrorHelper remediation guidance.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple


RECOMMENDED_SYSTEM_FONTS = ['system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI']

FORBIDDEN_ELEMENTS: Tuple[str, ...] = (
    'clipPath',
    'mask',
    'style',
    'foreignObject',
    'marker',
    'textPath',
    'animate',
    'animateMotion',
    'animateTransform',
    'animateColor',
    'set',
    'script',
    'iframe',
)

FORBIDDEN_ATTRIBUTES: Tuple[str, ...] = (
    'class',
    'id',
    'onclick',
    'onload',
    'onmouseover',
    'onmouseout',
    'onfocus',
    'onblur',
    'onchange',
    'marker-end',
)

FORBIDDEN_PATTERNS: Tuple[str, ...] = (
    r'@font-face',
    r'rgba\s*\(',
    r'<\?xml-stylesheet\b',
    r'<link[^>]*rel\s*=\s*["\']stylesheet["\']',
    r'@import\s+',
    r'<g[^>]*\sopacity\s*=',
    r'<image[^>]*\sopacity\s*=',
    r'\bon\w+\s*=',
    r'(?s)(?=.*<symbol)(?=.*<use\b)',
)


@dataclass(frozen=True)
class SubstringDetectionSpec:
    error_code: str
    marker: str
    error_message: str
    helper_message: str
    solutions: Tuple[str, ...]
    severity: str = 'error'


@dataclass(frozen=True)
class RegexDetectionSpec:
    error_code: str
    pattern: str
    error_message: str
    helper_message: str
    solutions: Tuple[str, ...]
    severity: str = 'error'
    search_in_lowercase: bool = False


@dataclass(frozen=True)
class CompoundDetectionSpec:
    error_code: str
    markers: Tuple[str, ...]
    regex_patterns: Tuple[str, ...]
    error_message: str
    helper_message: str
    solutions: Tuple[str, ...]
    severity: str = 'error'


_SUBSTRING_DETECTION_SPECS: Tuple[SubstringDetectionSpec, ...] = (
    SubstringDetectionSpec(
        error_code='clippath_detected',
        marker='<clippath',
        error_message='Detected forbidden <clipPath> element (PPT does not support SVG clipping paths).',
        helper_message='检测到禁用的 <clipPath> 元素',
        solutions=(
            '移除 <clipPath> 元素',
            'PPT 不支持 SVG 裁剪路径',
            '使用基础形状组合替代裁剪效果',
        ),
    ),
    SubstringDetectionSpec(
        error_code='mask_detected',
        marker='<mask',
        error_message='Detected forbidden <mask> element (PPT does not support SVG masks).',
        helper_message='检测到禁用的 <mask> 元素',
        solutions=(
            '移除 <mask> 元素',
            'PPT 不支持 SVG 遮罩',
            '使用不透明度（opacity/fill-opacity）替代',
        ),
    ),
    SubstringDetectionSpec(
        error_code='style_element_detected',
        marker='<style',
        error_message='Detected forbidden <style> element (use inline attributes instead).',
        helper_message='检测到禁用的 <style> 元素',
        solutions=(
            '移除 <style> 元素',
            '将 CSS 样式转换为内联属性',
            '例如: fill="#000" 而非 class="text-black"',
        ),
    ),
    SubstringDetectionSpec(
        error_code='foreignobject_detected',
        marker='<foreignobject',
        error_message='Detected forbidden <foreignObject> element (use <text> + <tspan> for manual wrapping).',
        helper_message='检测到禁用的 <foreignObject> 元素',
        solutions=(
            '移除 <foreignObject> 元素',
            '使用 <text> + <tspan> 进行手动换行',
            '这是项目的技术规范要求',
            '参考: docs/design_guidelines.md',
        ),
    ),
    SubstringDetectionSpec(
        error_code='textpath_detected',
        marker='<textpath',
        error_message='Detected forbidden <textPath> element (path text is not compatible with PPT).',
        helper_message='检测到禁用的 <textPath> 元素',
        solutions=(
            '移除 <textPath> 元素',
            '路径文本不兼容 PPT',
            '使用普通 <text> 元素并手动调整位置',
        ),
    ),
    SubstringDetectionSpec(
        error_code='marker_detected',
        marker='<marker',
        error_message='Detected forbidden <marker> element (PPT does not support SVG markers).',
        helper_message='检测到禁用的 <marker> 元素',
        solutions=(
            '移除 <marker> 定义',
            '使用 line + polygon 绘制箭头',
            '参考 AGENTS.md 的箭头绘制方案',
        ),
    ),
    SubstringDetectionSpec(
        error_code='iframe_detected',
        marker='<iframe',
        error_message='Detected <iframe> element (unexpected inside SVG).',
        helper_message='检测到禁用的 <iframe> 元素',
        solutions=(
            '移除 <iframe> 元素',
            'SVG 中不应嵌入外部页面',
        ),
    ),
)

_REGEX_DETECTION_SPECS: Tuple[RegexDetectionSpec, ...] = (
    RegexDetectionSpec(
        error_code='class_attribute_detected',
        pattern=r'\bclass\s*=',
        error_message='Detected forbidden class attribute (use inline styles instead).',
        helper_message='检测到禁用的 class 属性',
        solutions=(
            '移除所有 class 属性',
            '使用内联样式替代',
            '例如: fill="#000" stroke="#333" 直接写在元素上',
        ),
    ),
    RegexDetectionSpec(
        error_code='id_attribute_detected',
        pattern=r'\bid\s*=',
        error_message='Detected forbidden id attribute (use inline styles instead).',
        helper_message='检测到禁用的 id 属性',
        solutions=(
            '移除所有 id 属性',
            '使用内联样式替代',
            '避免依赖选择器定位或样式复用',
        ),
    ),
    RegexDetectionSpec(
        error_code='external_css_detected',
        pattern=r'<\?xml-stylesheet\b',
        error_message='Detected forbidden xml-stylesheet declaration (external CSS is not allowed).',
        helper_message='检测到禁用的外部 CSS 引用',
        solutions=(
            '移除 <?xml-stylesheet?> 声明',
            '移除 <link rel="stylesheet"> 引用',
            '移除 @import 外部样式',
            '将样式改为内联属性',
        ),
        search_in_lowercase=True,
    ),
    RegexDetectionSpec(
        error_code='external_css_detected',
        pattern=r'<link[^>]*rel\s*=\s*["\']stylesheet["\']',
        error_message='Detected forbidden <link rel="stylesheet"> element (external CSS is not allowed).',
        helper_message='检测到禁用的外部 CSS 引用',
        solutions=(
            '移除 <?xml-stylesheet?> 声明',
            '移除 <link rel="stylesheet"> 引用',
            '移除 @import 外部样式',
            '将样式改为内联属性',
        ),
        search_in_lowercase=True,
    ),
    RegexDetectionSpec(
        error_code='external_css_detected',
        pattern=r'@import\s+',
        error_message='Detected forbidden @import statement (external CSS is not allowed).',
        helper_message='检测到禁用的外部 CSS 引用',
        solutions=(
            '移除 <?xml-stylesheet?> 声明',
            '移除 <link rel="stylesheet"> 引用',
            '移除 @import 外部样式',
            '将样式改为内联属性',
        ),
    ),
    RegexDetectionSpec(
        error_code='marker_end_detected',
        pattern=r'\bmarker-end\s*=',
        error_message='Detected forbidden marker-end attribute (use line + polygon instead).',
        helper_message='检测到禁用的 marker-end 属性',
        solutions=(
            '移除 marker-end 属性',
            '使用 line + polygon 绘制箭头',
            '确保箭头方向与线条一致',
        ),
    ),
    RegexDetectionSpec(
        error_code='animation_detected',
        pattern=r'<animate',
        error_message='Detected forbidden SMIL animation element <animate*> (SVG animations are not exported).',
        helper_message='检测到禁用的 SMIL 动画元素',
        solutions=(
            '移除所有 <animate>, <animateMotion>, <animateTransform> 等元素',
            'SVG 动画不会导出到 PPT',
            '如需动画效果，在 PPT 中使用 PPT 原生动画',
        ),
        search_in_lowercase=True,
    ),
    RegexDetectionSpec(
        error_code='set_detected',
        pattern=r'<set\b',
        error_message='Detected forbidden SMIL animation element <set> (SVG animations are not exported).',
        helper_message='检测到禁用的 <set> 元素',
        solutions=(
            '移除 <set> 元素',
            'SVG 动画不会导出到 PPT',
            '如需动画效果请在 PPT 中设置',
        ),
        search_in_lowercase=True,
    ),
    RegexDetectionSpec(
        error_code='script_detected',
        pattern=r'<script',
        error_message='Detected forbidden <script> element (scripts and event handlers are not allowed).',
        helper_message='检测到禁用的 <script> 元素',
        solutions=(
            '移除 <script> 元素',
            '禁止脚本和事件处理',
            'SVG 中的 JavaScript 不会在 PPT 中执行',
        ),
        search_in_lowercase=True,
    ),
    RegexDetectionSpec(
        error_code='event_attribute_detected',
        pattern=r'\bon\w+\s*=',
        error_message='Detected forbidden event handler attribute (such as onclick or onload).',
        helper_message='检测到禁用的事件属性',
        solutions=(
            '移除 onclick/onload 等事件属性',
            'SVG 禁止脚本和事件处理',
            '交互请在 PPT 中实现',
        ),
    ),
    RegexDetectionSpec(
        error_code='rgba_detected',
        pattern=r'rgba\s*\(',
        error_message='Detected forbidden rgba() color usage (use fill-opacity or stroke-opacity instead).',
        helper_message='检测到禁用的 rgba() 颜色',
        solutions=(
            '将 rgba() 改为 hex + opacity 写法',
            '示例: fill="#FFFFFF" fill-opacity="0.1"',
            '描边使用 stroke-opacity',
        ),
        search_in_lowercase=True,
    ),
    RegexDetectionSpec(
        error_code='group_opacity_detected',
        pattern=r'<g[^>]*\sopacity\s*=',
        error_message='Detected forbidden <g opacity> usage (set opacity on child elements individually).',
        helper_message='检测到禁用的 <g opacity>',
        solutions=(
            '移除组级 opacity',
            '为每个子元素单独设置透明度',
            '使用 fill-opacity / stroke-opacity 控制',
        ),
        search_in_lowercase=True,
    ),
    RegexDetectionSpec(
        error_code='image_opacity_detected',
        pattern=r'<image[^>]*\sopacity\s*=',
        error_message='Detected forbidden <image opacity> usage (use an overlay-based workaround).',
        helper_message='检测到禁用的 <image opacity>',
        solutions=(
            '移除图片 opacity 属性',
            '添加遮罩层 <rect> 控制透明度',
            '确保遮罩颜色与背景一致',
        ),
        search_in_lowercase=True,
    ),
    RegexDetectionSpec(
        error_code='webfont_detected',
        pattern=r'@font-face',
        error_message='Detected forbidden @font-face declaration (use system font stacks).',
        helper_message='检测到禁用的 Web 字体 (@font-face)',
        solutions=(
            '移除 @font-face 声明',
            '使用系统字体栈',
            'font-family: system-ui, -apple-system, sans-serif',
        ),
    ),
)

_COMPOUND_DETECTION_SPECS: Tuple[CompoundDetectionSpec, ...] = (
    CompoundDetectionSpec(
        error_code='symbol_use_detected',
        markers=('<symbol',),
        regex_patterns=(r'<use\b',),
        error_message='Detected forbidden <symbol> + <use> combination (prefer basic shapes or simpler reuse patterns).',
        helper_message='检测到禁用的 <symbol> + <use> 复杂用法',
        solutions=(
            '将 <symbol> 展开为实际 SVG 代码',
            '避免 <symbol> + <use> 的复用结构',
            '需要图标时可直接嵌入 SVG 路径',
        ),
    ),
)


def get_substring_detection_specs() -> List[SubstringDetectionSpec]:
    return list(_SUBSTRING_DETECTION_SPECS)


def get_regex_detection_specs() -> List[RegexDetectionSpec]:
    return list(_REGEX_DETECTION_SPECS)


def get_compound_detection_specs() -> List[CompoundDetectionSpec]:
    return list(_COMPOUND_DETECTION_SPECS)


def build_svg_constraints() -> Dict[str, List[str]]:
    return {
        'forbidden_elements': list(FORBIDDEN_ELEMENTS),
        'forbidden_attributes': list(FORBIDDEN_ATTRIBUTES),
        'forbidden_patterns': list(FORBIDDEN_PATTERNS),
        'recommended_fonts': list(RECOMMENDED_SYSTEM_FONTS),
    }


def build_error_solutions() -> Dict[str, Dict[str, object]]:
    solutions: Dict[str, Dict[str, object]] = {}
    for spec in [*get_substring_detection_specs(), *get_regex_detection_specs(), *get_compound_detection_specs()]:
        solutions[spec.error_code] = {
            'message': spec.helper_message,
            'solutions': list(spec.solutions),
            'severity': spec.severity,
        }
    return solutions


__all__ = [
    'CompoundDetectionSpec',
    'FORBIDDEN_ATTRIBUTES',
    'FORBIDDEN_ELEMENTS',
    'FORBIDDEN_PATTERNS',
    'RECOMMENDED_SYSTEM_FONTS',
    'RegexDetectionSpec',
    'SubstringDetectionSpec',
    'build_error_solutions',
    'build_svg_constraints',
    'get_compound_detection_specs',
    'get_regex_detection_specs',
    'get_substring_detection_specs',
]
