"""Convert SVG rounded rectangles into path elements."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Tuple
from xml.etree import ElementTree as ET


def rect_to_rounded_path(x: float, y: float, width: float, height: float, rx: float, ry: float) -> str:
    """Convert a rounded rectangle into an equivalent SVG path."""

    rx = min(rx, width / 2)
    ry = min(ry, height / 2)

    x1 = x + rx
    x2 = x + width - rx
    y1 = y + ry
    y2 = y + height - ry

    path = (
        f"M{x1:.2f},{y:.2f} "
        f"H{x2:.2f} "
        f"A{rx:.2f},{ry:.2f} 0 0 1 {x + width:.2f},{y1:.2f} "
        f"V{y2:.2f} "
        f"A{rx:.2f},{ry:.2f} 0 0 1 {x2:.2f},{y + height:.2f} "
        f"H{x1:.2f} "
        f"A{rx:.2f},{ry:.2f} 0 0 1 {x:.2f},{y2:.2f} "
        f"V{y1:.2f} "
        f"A{rx:.2f},{ry:.2f} 0 0 1 {x1:.2f},{y:.2f} "
        f"Z"
    )
    return re.sub(r"\.00(?=\s|,|[A-Za-z]|$)", "", path)


def parse_float(value: str, default: float = 0.0) -> float:
    """Safely parse an SVG float value with optional units."""

    if not value:
        return default
    try:
        value = re.sub(r"(px|pt|em|%|rem)$", "", value.strip())
        return float(value)
    except ValueError:
        return default


def process_svg(content: str, verbose: bool = False) -> Tuple[str, int]:
    """Convert rounded rectangles in raw SVG content to paths."""

    converted_count = 0
    xml_declaration = ""
    if content.strip().startswith("<?xml"):
        match = re.match(r"(<\?xml[^?]*\?>)", content)
        if match:
            xml_declaration = match.group(1) + "\n"

    ET.register_namespace("", "http://www.w3.org/2000/svg")
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return content, 0

    namespace_prefix = ""
    if root.tag.startswith("{"):
        namespace_prefix = root.tag.split("}")[0] + "}"

    def get_tag_name(tag):
        if tag.startswith("{"):
            return tag.split("}")[1]
        return tag

    def process_element(element):
        nonlocal converted_count
        tag_name = get_tag_name(element.tag)

        if tag_name == "rect":
            rx = parse_float(element.get("rx", "0"))
            ry = parse_float(element.get("ry", "0"))
            if rx == 0 and ry > 0:
                rx = ry
            elif ry == 0 and rx > 0:
                ry = rx

            if rx > 0 or ry > 0:
                x = parse_float(element.get("x", "0"))
                y = parse_float(element.get("y", "0"))
                width = parse_float(element.get("width", "0"))
                height = parse_float(element.get("height", "0"))
                if width > 0 and height > 0:
                    path_d = rect_to_rounded_path(x, y, width, height, rx, ry)
                    rect_attrs = {"x", "y", "width", "height", "rx", "ry"}
                    element.tag = namespace_prefix + "path" if namespace_prefix else "path"
                    element.set("d", path_d)
                    for attr in rect_attrs:
                        if attr in element.attrib:
                            del element.attrib[attr]
                    converted_count += 1
                    if verbose:
                        print(f"    Converted rounded rectangle: rx={rx}, ry={ry}")

        for child in element:
            process_element(child)

    process_element(root)
    result = ET.tostring(root, encoding="unicode")
    if xml_declaration:
        result = xml_declaration + result
    return result, converted_count


def process_svg_file(input_path: Path, output_path: Path, verbose: bool = False) -> Tuple[bool, int]:
    """Process one SVG file and write the converted output."""

    try:
        content = input_path.read_text(encoding="utf-8")
        processed, count = process_svg(content, verbose)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(processed, encoding="utf-8")
        return True, count
    except Exception as exc:
        if verbose:
            print(f"  Error: {exc}")
        return False, 0


def find_svg_files(project_path: Path, source: str = "output") -> Tuple[List[Path], str]:
    """Find SVG files for a project directory or one of its source folders."""

    dir_map = {
        "output": "svg_output",
        "final": "svg_final",
        "flat": "svg_output_flattext",
        "final_flat": "svg_final_flattext",
    }
    dir_name = dir_map.get(source, source)
    svg_dir = project_path / dir_name

    if not svg_dir.exists():
        if (project_path / "svg_output").exists():
            dir_name = "svg_output"
            svg_dir = project_path / dir_name
        elif project_path.is_dir():
            svg_dir = project_path
            dir_name = project_path.name

    if not svg_dir.exists():
        return [], ""

    return sorted(svg_dir.glob("*.svg")), dir_name
