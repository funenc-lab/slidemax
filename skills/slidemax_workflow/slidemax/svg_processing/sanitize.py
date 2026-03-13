"""Sanitize SVG files for SlideMax delivery compatibility."""

from __future__ import annotations

from typing import Tuple
from xml.etree import ElementTree as ET

SVG_NAMESPACE = "http://www.w3.org/2000/svg"
EDITOR_NAMESPACES = {
    "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd",
    "http://www.inkscape.org/namespaces/inkscape",
}
REMOVABLE_TAGS = {"metadata", "namedview"}

ET.register_namespace("", SVG_NAMESPACE)


def local_name(value: str) -> str:
    """Return the local XML name without its namespace wrapper."""

    if value.startswith("{") and "}" in value:
        return value.split("}", 1)[1]
    return value


def namespace_uri(value: str) -> str:
    """Return the namespace URI from a tag or attribute name."""

    if value.startswith("{") and "}" in value:
        return value[1:].split("}", 1)[0]
    return ""


def _parse_opacity(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_opacity(value: float) -> str:
    formatted = f"{value:.4f}".rstrip("0").rstrip(".")
    return formatted or "0"


def combine_opacity(existing: str | None, applied: str) -> str:
    """Combine an existing element opacity with a propagated group opacity."""

    existing_value = _parse_opacity(existing) if existing is not None else None
    applied_value = _parse_opacity(applied)

    if existing_value is None or applied_value is None:
        return applied if existing is None else existing

    return _format_opacity(existing_value * applied_value)


def apply_group_opacity(element: ET.Element, opacity: str) -> int:
    """Push a group's opacity down to its non-group descendants."""

    changes = 0
    for child in list(element):
        if local_name(child.tag) == "defs":
            continue
        if namespace_uri(child.tag) in EDITOR_NAMESPACES:
            continue
        if local_name(child.tag) == "g":
            changes += apply_group_opacity(child, opacity)
            continue

        combined = combine_opacity(child.attrib.get("opacity"), opacity)
        if child.attrib.get("opacity") != combined:
            child.set("opacity", combined)
            changes += 1
    return changes


def sanitize_tree(tree: ET.ElementTree) -> int:
    """Sanitize an SVG tree in place and return the number of changes."""

    root = tree.getroot()
    return _sanitize_element(root, in_defs=False)


def _sanitize_element(element: ET.Element, *, in_defs: bool) -> int:
    current_in_defs = in_defs or local_name(element.tag) == "defs"
    changes = 0

    removable_attrs = [
        attr_name
        for attr_name in list(element.attrib)
        if namespace_uri(attr_name) in EDITOR_NAMESPACES
    ]
    for attr_name in removable_attrs:
        del element.attrib[attr_name]
        changes += 1

    if not current_in_defs and "id" in element.attrib:
        del element.attrib["id"]
        changes += 1

    if local_name(element.tag) == "g" and "opacity" in element.attrib:
        group_opacity = element.attrib.pop("opacity")
        changes += 1
        changes += apply_group_opacity(element, group_opacity)

    for child in list(element):
        child_local_name = local_name(child.tag)
        child_namespace = namespace_uri(child.tag)
        if child_local_name in REMOVABLE_TAGS or child_namespace in EDITOR_NAMESPACES:
            element.remove(child)
            changes += 1
            continue

        changes += _sanitize_element(child, in_defs=current_in_defs)

    return changes


def sanitize_svg_text(content: str) -> Tuple[str, int]:
    """Sanitize an SVG string and return the sanitized text and change count."""

    tree = ET.ElementTree(ET.fromstring(content))
    changes = sanitize_tree(tree)
    if hasattr(ET, "indent"):
        ET.indent(tree, space="  ")
    return ET.tostring(tree.getroot(), encoding="unicode"), changes

