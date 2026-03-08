from __future__ import annotations
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from slidemax.project_utils import CANVAS_FORMATS

@dataclass
class ChartArea:
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    @property
    def width(self) -> float:
        return self.x_max - self.x_min

    @property
    def height(self) -> float:
        return self.y_max - self.y_min

    @property
    def center(self) -> Tuple[float, float]:
        return ((self.x_min + self.x_max) / 2, (self.y_min + self.y_max) / 2)

class CoordinateSystem:

    def __init__(self, canvas_format: str='ppt169', chart_area: Optional[ChartArea]=None):
        self.canvas_format = canvas_format
        if canvas_format in CANVAS_FORMATS:
            viewbox = CANVAS_FORMATS[canvas_format]['viewbox']
            parts = viewbox.split()
            self.canvas_width = int(parts[2])
            self.canvas_height = int(parts[3])
        else:
            self.canvas_width = 1280
            self.canvas_height = 720
        if chart_area:
            self.chart_area = chart_area
        else:
            self.chart_area = ChartArea(x_min=140, y_min=150, x_max=self.canvas_width - 120, y_max=self.canvas_height - 120)

    def data_to_svg_x(self, data_x: float, x_range: Tuple[float, float]) -> float:
        (x_min, x_max) = x_range
        if x_max == x_min:
            return self.chart_area.x_min
        ratio = (data_x - x_min) / (x_max - x_min)
        return self.chart_area.x_min + ratio * self.chart_area.width

    def data_to_svg_y(self, data_y: float, y_range: Tuple[float, float]) -> float:
        (y_min, y_max) = y_range
        if y_max == y_min:
            return self.chart_area.y_max
        ratio = (data_y - y_min) / (y_max - y_min)
        return self.chart_area.y_max - ratio * self.chart_area.height

    def data_to_svg(self, data_x: float, data_y: float, x_range: Tuple[float, float], y_range: Tuple[float, float]) -> Tuple[float, float]:
        return (self.data_to_svg_x(data_x, x_range), self.data_to_svg_y(data_y, y_range))

@dataclass
class BarPosition:
    index: int
    label: str
    value: float
    x: float
    y: float
    width: float
    height: float
    label_x: float
    label_y: float
    value_x: float
    value_y: float

class BarChartCalculator:

    def __init__(self, coord_system: CoordinateSystem):
        self.coord = coord_system

    def calculate(self, data: Dict[str, float], bar_width: float=50, gap_ratio: float=0.3, y_min: float=0, y_max: Optional[float]=None, horizontal: bool=False) -> List[BarPosition]:
        labels = list(data.keys())
        values = list(data.values())
        n = len(labels)
        if n == 0:
            return []
        if y_max is None:
            y_max = max(values) * 1.1
        area = self.coord.chart_area
        if horizontal:
            return self._calculate_horizontal(labels, values, bar_width, gap_ratio, y_min, y_max)
        total_width = area.width
        if bar_width is None:
            bar_width = total_width / (n * (1 + gap_ratio))
        gap = bar_width * gap_ratio
        total_bars_width = n * bar_width + (n - 1) * gap
        start_x = area.x_min + (area.width - total_bars_width) / 2
        results = []
        for (i, (label, value)) in enumerate(zip(labels, values)):
            x = start_x + i * (bar_width + gap)
            ratio = (value - y_min) / (y_max - y_min) if y_max > y_min else 0
            height = ratio * area.height
            y = area.y_max - height
            center_x = x + bar_width / 2
            results.append(BarPosition(index=i + 1, label=label, value=value, x=round(x, 1), y=round(y, 1), width=round(bar_width, 1), height=round(height, 1), label_x=round(center_x, 1), label_y=round(area.y_max + 30, 1), value_x=round(center_x, 1), value_y=round(y - 15, 1)))
        return results

    def _calculate_horizontal(self, labels: List[str], values: List[float], bar_height: float, gap_ratio: float, x_min: float, x_max: float) -> List[BarPosition]:
        n = len(labels)
        area = self.coord.chart_area
        if bar_height is None:
            bar_height = area.height / (n * (1 + gap_ratio))
        gap = bar_height * gap_ratio
        total_bars_height = n * bar_height + (n - 1) * gap
        start_y = area.y_min + (area.height - total_bars_height) / 2
        results = []
        for (i, (label, value)) in enumerate(zip(labels, values)):
            y = start_y + i * (bar_height + gap)
            ratio = (value - x_min) / (x_max - x_min) if x_max > x_min else 0
            width = ratio * area.width
            x = area.x_min
            center_y = y + bar_height / 2
            results.append(BarPosition(index=i + 1, label=label, value=value, x=round(x, 1), y=round(y, 1), width=round(width, 1), height=round(bar_height, 1), label_x=round(area.x_min - 10, 1), label_y=round(center_y, 1), value_x=round(x + width + 10, 1), value_y=round(center_y, 1)))
        return results

    def format_table(self, positions: List[BarPosition]) -> str:
        lines = []
        lines.append('No.   Label       Value      X        Y        Width    Height')
        lines.append('----  ----------  --------  -------  -------  -------  -------')
        for p in positions:
            lines.append(f'{p.index:4d}  {p.label:<10s}  {p.value:>8.1f}  {p.x:>7.1f}  {p.y:>7.1f}  {p.width:>7.1f}  {p.height:>7.1f}')
        return '\n'.join(lines)

@dataclass
class PieSlice:
    index: int
    label: str
    value: float
    percentage: float
    start_angle: float
    end_angle: float
    path_d: str
    label_x: float
    label_y: float
    start_x: float
    start_y: float
    end_x: float
    end_y: float

class PieChartCalculator:

    def __init__(self, center: Tuple[float, float]=(420, 400), radius: float=200):
        (self.cx, self.cy) = center
        self.radius = radius

    def calculate(self, data: Dict[str, float], start_angle: float=-90, inner_radius: float=0) -> List[PieSlice]:
        labels = list(data.keys())
        values = list(data.values())
        total = sum(values)
        if total == 0:
            return []
        results = []
        current_angle = start_angle
        for (i, (label, value)) in enumerate(zip(labels, values)):
            percentage = value / total * 100
            angle_span = value / total * 360
            end_angle = current_angle + angle_span
            start_rad = math.radians(current_angle)
            end_rad = math.radians(end_angle)
            start_x = self.radius * math.cos(start_rad)
            start_y = self.radius * math.sin(start_rad)
            end_x = self.radius * math.cos(end_rad)
            end_y = self.radius * math.sin(end_rad)
            large_arc = 1 if angle_span > 180 else 0
            if inner_radius > 0:
                inner_start_x = inner_radius * math.cos(start_rad)
                inner_start_y = inner_radius * math.sin(start_rad)
                inner_end_x = inner_radius * math.cos(end_rad)
                inner_end_y = inner_radius * math.sin(end_rad)
                path_d = f'M {inner_start_x:.2f},{inner_start_y:.2f} L {start_x:.2f},{start_y:.2f} A {self.radius},{self.radius} 0 {large_arc},1 {end_x:.2f},{end_y:.2f} L {inner_end_x:.2f},{inner_end_y:.2f} A {inner_radius},{inner_radius} 0 {large_arc},0 {inner_start_x:.2f},{inner_start_y:.2f} Z'
            else:
                path_d = f'M 0,0 L {start_x:.2f},{start_y:.2f} A {self.radius},{self.radius} 0 {large_arc},1 {end_x:.2f},{end_y:.2f} Z'
            mid_angle = (current_angle + end_angle) / 2
            mid_rad = math.radians(mid_angle)
            label_distance = self.radius * 0.7
            label_x = self.cx + label_distance * math.cos(mid_rad)
            label_y = self.cy + label_distance * math.sin(mid_rad)
            results.append(PieSlice(index=i + 1, label=label, value=value, percentage=round(percentage, 1), start_angle=round(current_angle, 1), end_angle=round(end_angle, 1), path_d=path_d, label_x=round(label_x, 1), label_y=round(label_y, 1), start_x=round(start_x, 2), start_y=round(start_y, 2), end_x=round(end_x, 2), end_y=round(end_y, 2)))
            current_angle = end_angle
        return results

    def format_table(self, slices: List[PieSlice]) -> str:
        lines = []
        lines.append(f'Center: ({self.cx}, {self.cy}) | Radius: {self.radius}')
        lines.append('')
        lines.append('No.   Label       Percent    Start°    End°      LabelX   LabelY')
        lines.append('----  ----------  --------  --------  --------  -------  -------')
        for s in slices:
            lines.append(f'{s.index:4d}  {s.label:<10s}  {s.percentage:>6.1f}%  {s.start_angle:>8.1f}  {s.end_angle:>8.1f}  {s.label_x:>7.1f}  {s.label_y:>7.1f}')
        lines.append('')
        lines.append('=== Arc Endpoints (relative to center) ===')
        lines.append('No.   StartX     StartY     EndX       EndY')
        lines.append('----  ---------  ---------  ---------  ---------')
        for s in slices:
            lines.append(f'{s.index:4d}  {s.start_x:>9.2f}  {s.start_y:>9.2f}  {s.end_x:>9.2f}  {s.end_y:>9.2f}')
        lines.append('')
        lines.append('=== Path d Attribute ===')
        for s in slices:
            lines.append(f'{s.index}. {s.label}: {s.path_d}')
        return '\n'.join(lines)

@dataclass
class RadarPoint:
    index: int
    label: str
    value: float
    percentage: float
    angle: float
    x: float
    y: float
    abs_x: float
    abs_y: float
    label_x: float
    label_y: float

class RadarChartCalculator:

    def __init__(self, center: Tuple[float, float]=(640, 400), radius: float=200):
        (self.cx, self.cy) = center
        self.radius = radius

    def calculate(self, data: Dict[str, float], max_value: Optional[float]=None, start_angle: float=-90) -> List[RadarPoint]:
        labels = list(data.keys())
        values = list(data.values())
        n = len(labels)
        if n == 0:
            return []
        if max_value is None:
            max_value = max(values)
        angle_step = 360 / n
        results = []
        for (i, (label, value)) in enumerate(zip(labels, values)):
            angle = start_angle + i * angle_step
            rad = math.radians(angle)
            percentage = value / max_value * 100 if max_value > 0 else 0
            point_radius = self.radius * (value / max_value) if max_value > 0 else 0
            x = point_radius * math.cos(rad)
            y = point_radius * math.sin(rad)
            label_distance = self.radius + 30
            label_x = self.cx + label_distance * math.cos(rad)
            label_y = self.cy + label_distance * math.sin(rad)
            results.append(RadarPoint(index=i + 1, label=label, value=value, percentage=round(percentage, 1), angle=round(angle, 1), x=round(x, 2), y=round(y, 2), abs_x=round(self.cx + x, 2), abs_y=round(self.cy + y, 2), label_x=round(label_x, 1), label_y=round(label_y, 1)))
        return results

    def calculate_grid(self, levels: int=5) -> List[List[Tuple[float, float]]]:
        n = 6
        grids = []
        for level in range(1, levels + 1):
            level_radius = self.radius * level / levels
            points = []
            angle_step = 360 / n
            for i in range(n):
                angle = -90 + i * angle_step
                rad = math.radians(angle)
                x = level_radius * math.cos(rad)
                y = level_radius * math.sin(rad)
                points.append((round(x, 2), round(y, 2)))
            grids.append(points)
        return grids

    def format_table(self, points: List[RadarPoint]) -> str:
        lines = []
        lines.append(f'Center: ({self.cx}, {self.cy}) | Radius: {self.radius}')
        lines.append('')
        lines.append('No.   Dimension   Value    Percent    Angle      X        Y        AbsX     AbsY')
        lines.append('----  ----------  ------  --------  ------  -------  -------  -------  -------')
        for p in points:
            lines.append(f'{p.index:4d}  {p.label:<10s}  {p.value:>6.1f}  {p.percentage:>6.1f}%  {p.angle:>6.1f}  {p.x:>7.2f}  {p.y:>7.2f}  {p.abs_x:>7.1f}  {p.abs_y:>7.1f}')
        lines.append('')
        lines.append('=== SVG Polygon Points ===')
        points_str = ' '.join([f'{p.x},{p.y}' for p in points])
        lines.append(f'points="{points_str}"')
        return '\n'.join(lines)

@dataclass
class DataPoint:
    index: int
    x_value: float
    y_value: float
    svg_x: float
    svg_y: float
    label: Optional[str] = None

class LineChartCalculator:

    def __init__(self, coord_system: CoordinateSystem):
        self.coord = coord_system

    def calculate(self, data: List[Tuple[float, float]], x_range: Optional[Tuple[float, float]]=None, y_range: Optional[Tuple[float, float]]=None, labels: Optional[List[str]]=None) -> List[DataPoint]:
        if not data:
            return []
        x_values = [p[0] for p in data]
        y_values = [p[1] for p in data]
        if x_range is None:
            x_range = (min(x_values), max(x_values))
        if y_range is None:
            y_min = 0
            y_max = max(y_values) * 1.1
            y_range = (y_min, y_max)
        results = []
        for (i, (x, y)) in enumerate(data):
            (svg_x, svg_y) = self.coord.data_to_svg(x, y, x_range, y_range)
            results.append(DataPoint(index=i + 1, x_value=x, y_value=y, svg_x=round(svg_x, 1), svg_y=round(svg_y, 1), label=labels[i] if labels and i < len(labels) else None))
        return results

    def generate_path(self, points: List[DataPoint], closed: bool=False) -> str:
        if not points:
            return ''
        parts = [f'M {points[0].svg_x},{points[0].svg_y}']
        for p in points[1:]:
            parts.append(f'L {p.svg_x},{p.svg_y}')
        if closed:
            parts.append('Z')
        return ' '.join(parts)

    def format_table(self, points: List[DataPoint]) -> str:
        lines = []
        area = self.coord.chart_area
        lines.append(f'Chart area: ({area.x_min}, {area.y_min}) - ({area.x_max}, {area.y_max})')
        lines.append('')
        lines.append('No.   X value    Y value    SVG_X     SVG_Y')
        lines.append('----  ---------  ---------  --------  --------')
        for p in points:
            label_part = f'  ({p.label})' if p.label else ''
            lines.append(f'{p.index:4d}  {p.x_value:>9.2f}  {p.y_value:>9.2f}  {p.svg_x:>8.1f}  {p.svg_y:>8.1f}{label_part}')
        lines.append('')
        lines.append('=== SVG Path ===')
        lines.append(self.generate_path(points))
        return '\n'.join(lines)

@dataclass
class GridCell:
    row: int
    col: int
    index: int
    x: float
    y: float
    width: float
    height: float
    center_x: float
    center_y: float

class GridLayoutCalculator:

    def __init__(self, coord_system: CoordinateSystem):
        self.coord = coord_system

    def calculate(self, rows: int, cols: int, padding: float=20, gap: float=20) -> List[GridCell]:
        area = self.coord.chart_area
        available_width = area.width - 2 * padding - (cols - 1) * gap
        available_height = area.height - 2 * padding - (rows - 1) * gap
        cell_width = available_width / cols
        cell_height = available_height / rows
        results = []
        index = 1
        for row in range(rows):
            for col in range(cols):
                x = area.x_min + padding + col * (cell_width + gap)
                y = area.y_min + padding + row * (cell_height + gap)
                results.append(GridCell(row=row + 1, col=col + 1, index=index, x=round(x, 1), y=round(y, 1), width=round(cell_width, 1), height=round(cell_height, 1), center_x=round(x + cell_width / 2, 1), center_y=round(y + cell_height / 2, 1)))
                index += 1
        return results

    def format_table(self, cells: List[GridCell]) -> str:
        lines = []
        area = self.coord.chart_area
        lines.append(f'Chart area: ({area.x_min}, {area.y_min}) - ({area.x_max}, {area.y_max})')
        lines.append('')
        lines.append('No.   Row   Col   X        Y        Width    Height   CenterX  CenterY')
        lines.append('----  ----  ----  -------  -------  -------  -------  -------  -------')
        for c in cells:
            lines.append(f'{c.index:4d}  {c.row:4d}  {c.col:4d}  {c.x:>7.1f}  {c.y:>7.1f}  {c.width:>7.1f}  {c.height:>7.1f}  {c.center_x:>7.1f}  {c.center_y:>7.1f}')
        return '\n'.join(lines)

@dataclass
class ValidationResult:
    element_type: str
    element_id: str
    attribute: str
    expected: float
    actual: float
    deviation: float
    passed: bool

class SVGPositionValidator:

    def __init__(self, tolerance: float=1.0):
        self.tolerance = tolerance

    def validate_from_file(self, svg_file: str, expected_coords: Dict[str, Dict[str, float]]) -> List[ValidationResult]:
        svg_path = Path(svg_file)
        if not svg_path.exists():
            raise FileNotFoundError(f'SVG file does not exist: {svg_file}')
        with open(svg_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.validate_content(content, expected_coords)

    def validate_content(self, svg_content: str, expected_coords: Dict[str, Dict[str, float]]) -> List[ValidationResult]:
        results = []
        for (element_id, attrs) in expected_coords.items():
            for (attr, expected) in attrs.items():
                actual = self._extract_attribute(svg_content, element_id, attr)
                if actual is not None:
                    deviation = abs(actual - expected)
                    passed = deviation <= self.tolerance
                    results.append(ValidationResult(element_type=self._guess_element_type(element_id), element_id=element_id, attribute=attr, expected=expected, actual=actual, deviation=round(deviation, 2), passed=passed))
                else:
                    results.append(ValidationResult(element_type=self._guess_element_type(element_id), element_id=element_id, attribute=attr, expected=expected, actual=float('nan'), deviation=float('inf'), passed=False))
        return results

    def _extract_attribute(self, content: str, element_id: str, attr: str) -> Optional[float]:
        pattern = f'id="{element_id}"[^>]*{attr}="([^"]+)"'
        match = re.search(pattern, content)
        if not match:
            pattern = f'{attr}="([^"]+)"[^>]*id="{element_id}"'
            match = re.search(pattern, content)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None

    def _guess_element_type(self, element_id: str) -> str:
        id_lower = element_id.lower()
        if 'bar' in id_lower or 'rect' in id_lower:
            return 'rect'
        elif 'circle' in id_lower or 'dot' in id_lower:
            return 'circle'
        elif 'path' in id_lower or 'slice' in id_lower:
            return 'path'
        elif 'line' in id_lower:
            return 'line'
        elif 'text' in id_lower or 'label' in id_lower:
            return 'text'
        return 'unknown'

    def extract_all_positions(self, svg_content: str) -> Dict[str, Dict[str, float]]:
        positions = {}
        rect_pattern = '<rect[^>]*(?:id="([^"]*)")?[^>]*x="([^"]*)"[^>]*y="([^"]*)"[^>]*(?:width="([^"]*)")?[^>]*(?:height="([^"]*)")?'
        for match in re.finditer(rect_pattern, svg_content):
            id_val = match.group(1) or f'rect_{len(positions)}'
            positions[id_val] = {'x': float(match.group(2)) if match.group(2) else 0, 'y': float(match.group(3)) if match.group(3) else 0}
            if match.group(4):
                positions[id_val]['width'] = float(match.group(4))
            if match.group(5):
                positions[id_val]['height'] = float(match.group(5))
        circle_pattern = '<circle[^>]*(?:id="([^"]*)")?[^>]*cx="([^"]*)"[^>]*cy="([^"]*)"'
        for match in re.finditer(circle_pattern, svg_content):
            id_val = match.group(1) or f'circle_{len(positions)}'
            positions[id_val] = {'cx': float(match.group(2)), 'cy': float(match.group(3))}
        return positions

    def format_results(self, results: List[ValidationResult]) -> str:
        lines = []
        lines.append('=== SVG Position Validation Results ===')
        lines.append(f'Tolerance: {self.tolerance}px')
        lines.append('')
        lines.append('State   Element ID       Attr    Expected  Actual    Delta')
        lines.append('----  --------------  ------  --------  --------  ------')
        passed_count = 0
        for r in results:
            status = '[OK]' if r.passed else '[X]'
            if r.passed:
                passed_count += 1
            actual_str = f'{r.actual:.1f}' if not math.isnan(r.actual) else 'N/A'
            deviation_str = f'{r.deviation:.2f}' if not math.isinf(r.deviation) else 'N/A'
            lines.append(f'{status}    {r.element_id:<14s}  {r.attribute:<6s}  {r.expected:>8.1f}  {actual_str:>8s}  {deviation_str:>6s}')
        lines.append('')
        lines.append(f'Passed: {passed_count}/{len(results)} ({passed_count / len(results) * 100:.1f}%)')
        return '\n'.join(lines)

def parse_data_string(data_str: str) -> Dict[str, float]:
    result = {}
    for item in data_str.split(','):
        item = item.strip()
        if not item:
            continue
        if ':' in item:
            (label, value) = item.split(':', 1)
            try:
                result[label.strip()] = float(value.strip())
            except ValueError:
                print(f"[WARN] Could not parse numeric value: '{value.strip()}', skipped")
        else:
            print(f"[WARN] Invalid format (expected 'label:value'): '{item}'")
    return result

def parse_xy_data_string(data_str: str) -> List[Tuple[float, float]]:
    result = []
    for item in data_str.split(','):
        item = item.strip()
        if not item:
            continue
        if ':' in item:
            (x, y) = item.split(':', 1)
            try:
                result.append((float(x.strip()), float(y.strip())))
            except ValueError:
                print(f"[WARN] Could not parse coordinate pair: '{item}', skipped")
        else:
            print(f"[WARN] Invalid format (expected 'x:y'): '{item}'")
    return result

def parse_tuple(s: str) -> Tuple[float, ...]:
    return tuple((float(x.strip()) for x in s.split(',')))

def extract_attr(element: str, attr_name: str) -> Optional[str]:
    pattern = f'{attr_name}="([^"]*)"'
    match = re.search(pattern, element)
    return match.group(1) if match else None
__all__ = ['BarChartCalculator', 'BarPosition', 'ChartArea', 'CoordinateSystem', 'DataPoint', 'GridCell', 'GridLayoutCalculator', 'LineChartCalculator', 'PieChartCalculator', 'PieSlice', 'RadarChartCalculator', 'RadarPoint', 'SVGPositionValidator', 'ValidationResult', 'extract_attr', 'parse_data_string', 'parse_tuple', 'parse_xy_data_string']
