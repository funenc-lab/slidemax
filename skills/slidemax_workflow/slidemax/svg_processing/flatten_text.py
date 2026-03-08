"""Flatten SVG text tspans into simpler text nodes."""

from __future__ import annotations

import os
import re
from xml.etree import ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"
NSMAP = {"svg": SVG_NS}

ET.register_namespace("", SVG_NS)

TEXT_STYLE_ATTRS = {
    "font-family",
    "font-size",
    "font-weight",
    "font-style",
    "font-variant",
    "font-stretch",
    "letter-spacing",
    "word-spacing",
    "kerning",
    "text-anchor",
    "text-decoration",
    "dominant-baseline",
    "writing-mode",
    "direction",
    "fill",
    "fill-opacity",
    "stroke",
    "stroke-width",
    "stroke-opacity",
    "opacity",
    "paint-order",
    "transform",
    "clip-path",
    "filter",
}

NUM_RE = re.compile(r"^[\s,]*([+-]?(?:\d+\.?\d*|\d*\.\d+))")


def parse_first_number(value: str):
    """Parse the first numeric token from an SVG numeric attribute."""

    if value is None:
        return None
    match = NUM_RE.match(value)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def format_number(value: float) -> str:
    """Format SVG numeric output with trimmed trailing zeros."""

    if value is None:
        return None
    if abs(value - round(value)) < 1e-6:
        return str(int(round(value)))
    return f"{value:.6f}".rstrip("0").rstrip(".")


def parse_style(style_str: str) -> dict:
    """Parse inline SVG style content into a dictionary."""

    output = {}
    if not style_str:
        return output
    for chunk in style_str.split(";"):
        if not chunk.strip():
            continue
        if ":" in chunk:
            key, value = chunk.split(":", 1)
            output[key.strip()] = value.strip()
    return output


def style_to_string(style_map: dict) -> str:
    """Serialize an inline style dictionary back into SVG syntax."""

    if not style_map:
        return ""
    return ";".join(f"{key}:{value}" for key, value in style_map.items())


def merge_styles(parent_style: str, child_style: str) -> str:
    """Merge parent and child SVG style strings with child precedence."""

    parent = parse_style(parent_style)
    child = parse_style(child_style)
    parent.update(child)
    return style_to_string(parent)


def get_attr(element, name, default=None):
    """Read an attribute from an XML element with a default."""

    return element.get(name) if element is not None and name in element.attrib else default


def compute_line_positions(text_el, tspan_el, cur_x, cur_y):
    """Compute absolute line positions for a nested tspan node."""

    t_x_attr = get_attr(tspan_el, "x")
    t_y_attr = get_attr(tspan_el, "y")
    t_dx_attr = get_attr(tspan_el, "dx")
    t_dy_attr = get_attr(tspan_el, "dy")

    if t_x_attr is not None:
        next_x = parse_first_number(t_x_attr)
    elif t_dx_attr is not None:
        dx = parse_first_number(t_dx_attr) or 0.0
        next_x = (cur_x or 0.0) + dx
    else:
        next_x = cur_x

    if t_y_attr is not None:
        next_y = parse_first_number(t_y_attr)
    elif t_dy_attr is not None:
        dy = parse_first_number(t_dy_attr) or 0.0
        next_y = (cur_y or 0.0) + dy
    else:
        next_y = cur_y

    return next_x, next_y


def collect_text_content(element) -> str:
    """Collect flattened text content from an element subtree."""

    parts = []
    for text in element.itertext():
        if text:
            parts.append(text)
    return "".join(parts)


def copy_text_attrs(src_el, dst_el, exclude=None):
    """Copy supported text style attributes from source to destination."""

    exclude = exclude or set()
    if "style" in src_el.attrib and "style" not in exclude:
        dst_el.set("style", src_el.attrib["style"])
    for key in TEXT_STYLE_ATTRS:
        if key in exclude:
            continue
        value = src_el.get(key)
        if value is not None:
            dst_el.set(key, value)
    xml_space = src_el.get("{http://www.w3.org/XML/1998/namespace}space")
    if xml_space is not None and "{http://www.w3.org/XML/1998/namespace}space" not in exclude:
        dst_el.set("{http://www.w3.org/XML/1998/namespace}space", xml_space)


def _create_text_element_from_line(text_el, lead_text, tspans, x, y):
    """Create a replacement text element for one visual line."""

    new_element = ET.Element(f"{{{SVG_NS}}}text")
    copy_text_attrs(text_el, new_element, exclude={"x", "y"})
    new_element.set("x", format_number(x))
    new_element.set("y", format_number(y))

    parent_transform = text_el.get("transform")
    if parent_transform:
        new_element.set("transform", parent_transform)

    if not lead_text and len(tspans) == 1:
        tspan = tspans[0]
        content = collect_text_content(tspan)
        merged_style = merge_styles(text_el.get("style"), tspan.get("style"))
        if merged_style:
            new_element.set("style", merged_style)
        for attr in TEXT_STYLE_ATTRS:
            child_value = tspan.get(attr)
            if child_value is not None:
                new_element.set(attr, child_value)
        child_transform = tspan.get("transform")
        if parent_transform and child_transform:
            new_element.set("transform", f"{parent_transform} {child_transform}")
        elif child_transform:
            new_element.set("transform", child_transform)
        new_element.text = content
    else:
        if lead_text:
            new_element.text = lead_text
        for tspan in tspans:
            new_tspan = ET.SubElement(new_element, f"{{{SVG_NS}}}tspan")
            for attr in TEXT_STYLE_ATTRS:
                child_value = tspan.get(attr)
                if child_value is not None:
                    new_tspan.set(attr, child_value)
            if tspan.get("style"):
                new_tspan.set("style", tspan.get("style"))
            new_tspan.text = collect_text_content(tspan)
            if tspan.tail:
                new_tspan.tail = tspan.tail

    return new_element


def flatten_text_with_tspans(tree: ET.ElementTree) -> bool:
    """Flatten multi-line tspan-based text nodes into simpler text nodes."""

    root = tree.getroot()
    parent_map = {child: parent for parent in root.iter() for child in parent}
    changed = False

    def is_svg_tag(element, name):
        return element.tag == f"{{{SVG_NS}}}{name}"

    def is_new_line_tspan(tspan):
        t_dy_attr = get_attr(tspan, "dy")
        t_y_attr = get_attr(tspan, "y")
        t_x_attr = get_attr(tspan, "x")
        dy_value = parse_first_number(t_dy_attr) if t_dy_attr is not None else None
        if t_y_attr is not None:
            return True
        if dy_value is not None and dy_value != 0:
            return True
        if t_x_attr is not None:
            return True
        return False

    candidates = []
    for element in root.iter():
        if is_svg_tag(element, "text"):
            has_tspan_child = any(is_svg_tag(child, "tspan") for child in list(element))
            if has_tspan_child:
                candidates.append(element)

    for text_el in candidates:
        parent = parent_map.get(text_el)
        if parent is None:
            continue

        needs_flatten = False
        for child in list(text_el):
            if not is_svg_tag(child, "tspan"):
                continue
            if is_new_line_tspan(child):
                needs_flatten = True
                break
        if not needs_flatten:
            continue

        base_x = parse_first_number(get_attr(text_el, "x")) or 0.0
        base_y = parse_first_number(get_attr(text_el, "y")) or 0.0
        cur_x, cur_y = base_x, base_y
        new_texts = []
        current_tspans = []
        current_lead_text = text_el.text or ""

        for child in list(text_el):
            if not is_svg_tag(child, "tspan"):
                continue
            if is_new_line_tspan(child) and (current_tspans or current_lead_text):
                new_texts.append(
                    _create_text_element_from_line(
                        text_el,
                        current_lead_text,
                        current_tspans,
                        cur_x,
                        cur_y,
                    )
                )
                current_lead_text = ""
                current_tspans = []
            cur_x, cur_y = compute_line_positions(text_el, child, cur_x, cur_y)
            current_tspans.append(child)

        if current_tspans or current_lead_text:
            new_texts.append(
                _create_text_element_from_line(
                    text_el,
                    current_lead_text,
                    current_tspans,
                    cur_x,
                    cur_y,
                )
            )

        children = list(parent)
        insert_index = children.index(text_el) if text_el in children else None
        for offset, new_element in enumerate(new_texts):
            if insert_index is not None:
                parent.insert(insert_index + offset, new_element)
            else:
                parent.append(new_element)
        parent.remove(text_el)
        changed = True

    return changed


def process_svg_file(src_path: str, dst_path: str) -> bool:
    """Process one SVG file and write the flattened result to a destination."""

    try:
        tree = ET.parse(src_path)
    except ET.ParseError as exc:
        print(f"[WARN] Failed to parse {src_path}: {exc}")
        return False

    changed = flatten_text_with_tspans(tree)
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    tree.write(dst_path, encoding="utf-8", xml_declaration=False, method="xml")
    return changed


def compute_default_output_base(input_path: str) -> str:
    """Compute the default output location for file or directory input."""

    if os.path.isdir(input_path):
        head, tail = os.path.split(os.path.normpath(input_path))
        if tail == "svg_output":
            return os.path.join(head, "svg_output_flattext")
        return input_path.rstrip("/\\") + "_flattext"

    base, extension = os.path.splitext(input_path)
    return base + "_flattext" + extension
