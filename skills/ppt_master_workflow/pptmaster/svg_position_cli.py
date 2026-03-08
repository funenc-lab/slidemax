from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .project_utils import CANVAS_FORMATS
from .svg_positioning import (
    BarChartCalculator,
    ChartArea,
    CoordinateSystem,
    GridLayoutCalculator,
    LineChartCalculator,
    PieChartCalculator,
    RadarChartCalculator,
    SVGPositionValidator,
    extract_attr,
    parse_data_string,
    parse_tuple,
    parse_xy_data_string,
)

InputFn = Callable[[str], str]
OutputFn = Callable[[str], None]


def configure_console_encoding() -> None:
    if sys.platform != 'win32':
        return

    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        import io

        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def build_chart_area(area_value: Optional[str]) -> Optional[ChartArea]:
    if not area_value:
        return None

    parts = parse_tuple(area_value)
    if len(parts) != 4:
        raise ValueError('Chart area must contain four comma-separated numbers: x_min,y_min,x_max,y_max')
    return ChartArea(parts[0], parts[1], parts[2], parts[3])


def format_canvas_label(canvas: str) -> str:
    return str(CANVAS_FORMATS.get(canvas, {}).get('dimensions', canvas))


def read_text_file(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def analyze_svg_file(svg_file: str | Path) -> str:
    svg_path = Path(svg_file)
    if not svg_path.exists():
        raise FileNotFoundError(f'SVG file does not exist: {svg_path}')

    content = read_text_file(svg_path)
    lines: List[str] = []
    lines.append('')
    lines.append('=' * 70)
    lines.append(f'SVG analysis: {svg_path.name}')
    lines.append('=' * 70)

    viewbox_match = re.search(r'viewBox="([^"]+)"', content)
    if viewbox_match:
        lines.append(f'Canvas viewBox: {viewbox_match.group(1)}')

    rect_elements = re.findall(r'<rect[^>]*/?>', content)
    rects: List[Tuple[str, str, Optional[str], Optional[str]]] = []
    for element in rect_elements:
        x = extract_attr(element, 'x')
        y = extract_attr(element, 'y')
        width = extract_attr(element, 'width')
        height = extract_attr(element, 'height')
        if x is not None and y is not None:
            rects.append((x, y, width, height))

    circle_elements = re.findall(r'<circle[^>]*/?>', content)
    circles: List[Tuple[str, str, Optional[str]]] = []
    for element in circle_elements:
        cx = extract_attr(element, 'cx')
        cy = extract_attr(element, 'cy')
        radius = extract_attr(element, 'r')
        if cx is not None and cy is not None:
            circles.append((cx, cy, radius))

    polylines = re.findall(r'<(?:polyline|polygon)[^>]*points="([^"]*)"', content)
    paths = re.findall(r'<path[^>]*d="([^"]*)"', content)

    lines.append('')
    lines.append('Element summary:')
    lines.append(f'  - rect: {len(rects)}')
    lines.append(f'  - circle: {len(circles)}')
    lines.append(f'  - polyline/polygon: {len(polylines)}')
    lines.append(f'  - path: {len(paths)}')

    if rects:
        lines.append('')
        lines.append('=== Rect elements ===')
        lines.append(f"{'No.':<4}  {'X':<8}  {'Y':<8}  {'Width':<8}  {'Height':<8}")
        lines.append('-' * 45)
        for index, (x, y, width, height) in enumerate(rects[:20], start=1):
            lines.append(f"{index:<4}  {x:<8}  {y:<8}  {(width or '-'): <8}  {(height or '-'): <8}")
        if len(rects) > 20:
            lines.append(f'... {len(rects) - 20} additional rect elements omitted')

    if circles:
        lines.append('')
        lines.append('=== Circle elements ===')
        lines.append(f"{'No.':<4}  {'CX':<10}  {'CY':<10}  {'Radius':<8}")
        lines.append('-' * 40)
        for index, (cx, cy, radius) in enumerate(circles[:20], start=1):
            lines.append(f"{index:<4}  {cx:<10}  {cy:<10}  {(radius or '-'): <8}")
        if len(circles) > 20:
            lines.append(f'... {len(circles) - 20} additional circle elements omitted')

    if polylines:
        lines.append('')
        lines.append('=== Polyline or polygon elements ===')
        for index, points in enumerate(polylines, start=1):
            point_list = points.strip().split()
            preview: List[str] = []
            for point in point_list[:5]:
                if ',' in point:
                    x, y = point.split(',', 1)
                    preview.append(f'({x},{y})')
            lines.append(f'Polyline {index} ({len(point_list)} points):')
            lines.append(f"  Preview: {' -> '.join(preview)}")
            if len(point_list) > 5:
                lines.append(f'  ... {len(point_list)} points total')

    lines.append('')
    lines.append('=' * 70)
    return '\n'.join(lines)


def render_custom_line_report(
    base_x: float,
    step_x: float,
    base_y: float,
    scale_y: float,
    reference_value: float,
    values: Sequence[float],
) -> str:
    lines: List[str] = []
    lines.append('')
    lines.append(f'Formula: X = {base_x} + index * {step_x}')
    lines.append(f'         Y = {base_y} - (value - {reference_value}) * {scale_y}')
    lines.append('')
    lines.append(f"{'No.':<4}  {'Value':<10}  {'X':<8}  {'Y':<8}")
    lines.append('-' * 35)

    points: List[str] = []
    for index, value in enumerate(values, start=1):
        x = base_x + index * step_x
        y = base_y - (value - reference_value) * scale_y
        lines.append(f'{index:<4}  {value:<10.1f}  {x:<8.0f}  {y:<8.0f}')
        points.append(f'{int(x)},{int(y)}')

    lines.append('')
    lines.append('polyline points:')
    lines.append(' '.join(points))
    return '\n'.join(lines)


def interactive_mode(input_fn: InputFn = input, output_fn: OutputFn = print) -> int:
    output_fn('\n' + '=' * 60)
    output_fn('SVG position calculator - interactive mode')
    output_fn('=' * 60)
    output_fn('\nChoose a chart type:')
    output_fn('  1. Bar chart')
    output_fn('  2. Pie chart')
    output_fn('  3. Radar chart')
    output_fn('  4. Line chart')
    output_fn('  5. Grid layout')
    output_fn('  6. Custom line formula')
    output_fn('  0. Exit')

    while True:
        try:
            choice = input_fn('\nSelect [1-6, 0 to exit]: ').strip()
            if choice == '0':
                output_fn('Exit interactive mode')
                return 0

            if choice == '1':
                output_fn('\n=== Bar chart calculation ===')
                data_str = input_fn('Enter data (label1:value1,label2:value2): ').strip()
                if not data_str:
                    output_fn('Example: east:185,south:142,north:128')
                    continue
                canvas = input_fn('Canvas format [ppt169]: ').strip() or 'ppt169'
                calc = BarChartCalculator(CoordinateSystem(canvas))
                output_fn('')
                output_fn(calc.format_table(calc.calculate(parse_data_string(data_str))))
                continue

            if choice == '2':
                output_fn('\n=== Pie chart calculation ===')
                data_str = input_fn('Enter data (label1:value1,label2:value2): ').strip()
                if not data_str:
                    output_fn('Example: A:35,B:25,C:20,D:12,Other:8')
                    continue
                center = parse_tuple(input_fn('Center [420,400]: ').strip() or '420,400')
                radius = float(input_fn('Radius [200]: ').strip() or '200')
                calc = PieChartCalculator(center, radius)
                output_fn('')
                output_fn(calc.format_table(calc.calculate(parse_data_string(data_str))))
                continue

            if choice == '3':
                output_fn('\n=== Radar chart calculation ===')
                data_str = input_fn('Enter data (label1:value1,label2:value2): ').strip()
                if not data_str:
                    output_fn('Example: performance:90,security:85,ux:75,price:70')
                    continue
                center = parse_tuple(input_fn('Center [640,400]: ').strip() or '640,400')
                radius = float(input_fn('Radius [200]: ').strip() or '200')
                calc = RadarChartCalculator(center, radius)
                output_fn('')
                output_fn(calc.format_table(calc.calculate(parse_data_string(data_str))))
                continue

            if choice == '4':
                output_fn('\n=== Line chart calculation ===')
                data_str = input_fn('Enter data (x1:y1,x2:y2): ').strip()
                if not data_str:
                    output_fn('Example: 0:50,10:80,20:120,30:95')
                    continue
                canvas = input_fn('Canvas format [ppt169]: ').strip() or 'ppt169'
                calc = LineChartCalculator(CoordinateSystem(canvas))
                output_fn('')
                output_fn(calc.format_table(calc.calculate(parse_xy_data_string(data_str))))
                continue

            if choice == '5':
                output_fn('\n=== Grid layout calculation ===')
                rows = int(input_fn('Rows [2]: ').strip() or '2')
                cols = int(input_fn('Columns [3]: ').strip() or '3')
                canvas = input_fn('Canvas format [ppt169]: ').strip() or 'ppt169'
                calc = GridLayoutCalculator(CoordinateSystem(canvas))
                output_fn('')
                output_fn(calc.format_table(calc.calculate(rows, cols)))
                continue

            if choice == '6':
                output_fn('\n=== Custom line formula ===')
                base_x = float(input_fn('Base X [170]: ').strip() or '170')
                step_x = float(input_fn('Step X [40]: ').strip() or '40')
                base_y = float(input_fn('Base Y [595]: ').strip() or '595')
                scale_y = float(input_fn('Scale Y [20]: ').strip() or '20')
                reference_value = float(input_fn('Reference value [100]: ').strip() or '100')
                data_str = input_fn('Enter values (comma-separated): ').strip()
                if not data_str:
                    output_fn('Please provide at least one numeric value.')
                    continue
                values = [float(value.strip()) for value in data_str.split(',') if value.strip()]
                output_fn(render_custom_line_report(base_x, step_x, base_y, scale_y, reference_value, values))
                continue

            output_fn('Invalid selection. Enter 1-6 or 0.')
        except KeyboardInterrupt:
            output_fn('\nExit interactive mode')
            return 0
        except Exception as exc:
            output_fn(f'[ERROR] {exc}')


def from_json_config(config_file: str | Path) -> str:
    config_path = Path(config_file)
    if not config_path.exists():
        raise FileNotFoundError(f'Config file does not exist: {config_path}')

    config = json.loads(read_text_file(config_path))
    chart_type = str(config.get('type', 'bar'))
    data = config.get('data', {})

    lines = [f'Loaded config: {config_path.name}', f'Chart type: {chart_type}']

    if chart_type == 'bar':
        canvas = str(config.get('canvas', 'ppt169'))
        calc = BarChartCalculator(CoordinateSystem(canvas))
        lines.append(calc.format_table(calc.calculate(data)))
        return '\n'.join(lines)

    if chart_type == 'pie':
        center = tuple(config.get('center', [420, 400]))
        radius = float(config.get('radius', 200))
        calc = PieChartCalculator(center, radius)
        lines.append(calc.format_table(calc.calculate(data)))
        return '\n'.join(lines)

    if chart_type == 'line':
        canvas = str(config.get('canvas', 'ppt169'))
        calc = LineChartCalculator(CoordinateSystem(canvas))
        points_data = [(point[0], point[1]) for point in data]
        lines.append(calc.format_table(calc.calculate(points_data)))
        return '\n'.join(lines)

    if chart_type == 'custom_line':
        lines.append(
            render_custom_line_report(
                float(config.get('base_x', 170)),
                float(config.get('step_x', 40)),
                float(config.get('base_y', 595)),
                float(config.get('scale_y', 20)),
                float(config.get('ref_value', 100)),
                [float(value) for value in config.get('values', [])],
            )
        )
        return '\n'.join(lines)

    raise ValueError(f'Unsupported chart type in config: {chart_type}')


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Calculate SVG chart coordinates and inspect positioned elements.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python svg_position_calculator.py analyze example.svg
  python svg_position_calculator.py interactive
  python svg_position_calculator.py from-json config.json
  python svg_position_calculator.py calc bar --data "east:185,south:142"
  python svg_position_calculator.py calc pie --data "A:35,B:25,C:20"
  python svg_position_calculator.py calc line --data "0:50,10:80,20:120"
''',
    )

    subparsers = parser.add_subparsers(dest='command', help='Subcommands')

    calc_parser = subparsers.add_parser('calc', help='Calculate positions')
    calc_subparsers = calc_parser.add_subparsers(dest='chart_type', help='Chart type')

    bar_parser = calc_subparsers.add_parser('bar', help='Bar chart')
    bar_parser.add_argument('--data', required=True, help='label1:value1,label2:value2')
    bar_parser.add_argument('--canvas', default='ppt169', help='Canvas format')
    bar_parser.add_argument('--area', help='x_min,y_min,x_max,y_max')
    bar_parser.add_argument('--bar-width', type=float, default=50, help='Bar width')
    bar_parser.add_argument('--horizontal', action='store_true', help='Use horizontal bars')

    pie_parser = calc_subparsers.add_parser('pie', help='Pie or donut chart')
    pie_parser.add_argument('--data', required=True, help='label1:value1,label2:value2')
    pie_parser.add_argument('--center', default='420,400', help='x,y')
    pie_parser.add_argument('--radius', type=float, default=200, help='Radius')
    pie_parser.add_argument('--inner-radius', type=float, default=0, help='Inner radius for donut charts')
    pie_parser.add_argument('--start-angle', type=float, default=-90, help='Start angle in degrees')

    radar_parser = calc_subparsers.add_parser('radar', help='Radar chart')
    radar_parser.add_argument('--data', required=True, help='label1:value1,label2:value2')
    radar_parser.add_argument('--center', default='640,400', help='x,y')
    radar_parser.add_argument('--radius', type=float, default=200, help='Radius')
    radar_parser.add_argument('--max-value', type=float, help='Optional max value')

    line_parser = calc_subparsers.add_parser('line', help='Line or scatter chart')
    line_parser.add_argument('--data', required=True, help='x1:y1,x2:y2')
    line_parser.add_argument('--canvas', default='ppt169', help='Canvas format')
    line_parser.add_argument('--area', help='x_min,y_min,x_max,y_max')
    line_parser.add_argument('--x-range', help='min,max')
    line_parser.add_argument('--y-range', help='min,max')

    grid_parser = calc_subparsers.add_parser('grid', help='Grid layout')
    grid_parser.add_argument('--rows', type=int, required=True, help='Rows')
    grid_parser.add_argument('--cols', type=int, required=True, help='Columns')
    grid_parser.add_argument('--canvas', default='ppt169', help='Canvas format')
    grid_parser.add_argument('--area', help='x_min,y_min,x_max,y_max')
    grid_parser.add_argument('--padding', type=float, default=20, help='Inner padding')
    grid_parser.add_argument('--gap', type=float, default=20, help='Gap between cells')

    validate_parser = subparsers.add_parser('validate', help='Validate or inspect SVG positions')
    validate_parser.add_argument('svg_file', help='SVG file path')
    validate_parser.add_argument('--extract', action='store_true', help='Extract all detectable positions')
    validate_parser.add_argument('--tolerance', type=float, default=1.0, help='Validation tolerance in pixels')

    analyze_parser = subparsers.add_parser('analyze', help='Analyze SVG primitives')
    analyze_parser.add_argument('svg_file', help='SVG file path')

    subparsers.add_parser('interactive', help='Interactive mode')

    json_parser = subparsers.add_parser('from-json', help='Load configuration from JSON')
    json_parser.add_argument('config_file', help='JSON config file path')

    return parser


def handle_calc_command(args: argparse.Namespace) -> str:
    chart_area = build_chart_area(getattr(args, 'area', None))

    if args.chart_type == 'bar':
        canvas = getattr(args, 'canvas', 'ppt169')
        coord = CoordinateSystem(canvas, chart_area)
        calc = BarChartCalculator(coord)
        positions = calc.calculate(parse_data_string(args.data), bar_width=args.bar_width, horizontal=args.horizontal)
        return '\n'.join(
            [
                '',
                '=== Bar chart coordinates ===',
                f'Canvas: {format_canvas_label(canvas)}',
                f'Chart area: ({coord.chart_area.x_min}, {coord.chart_area.y_min}) - ({coord.chart_area.x_max}, {coord.chart_area.y_max})',
                '',
                calc.format_table(positions),
            ]
        )

    if args.chart_type == 'pie':
        calc = PieChartCalculator(parse_tuple(args.center), args.radius)
        slices = calc.calculate(parse_data_string(args.data), start_angle=args.start_angle, inner_radius=args.inner_radius)
        return '\n'.join(['', '=== Pie chart slices ===', calc.format_table(slices)])

    if args.chart_type == 'radar':
        calc = RadarChartCalculator(parse_tuple(args.center), args.radius)
        points = calc.calculate(parse_data_string(args.data), max_value=args.max_value)
        return '\n'.join(['', '=== Radar chart points ===', calc.format_table(points)])

    if args.chart_type == 'line':
        canvas = getattr(args, 'canvas', 'ppt169')
        coord = CoordinateSystem(canvas, chart_area)
        calc = LineChartCalculator(coord)
        x_range = parse_tuple(args.x_range) if args.x_range else None
        y_range = parse_tuple(args.y_range) if args.y_range else None
        points = calc.calculate(parse_xy_data_string(args.data), x_range, y_range)
        return '\n'.join(['', '=== Line or scatter coordinates ===', f'Canvas: {format_canvas_label(canvas)}', calc.format_table(points)])

    if args.chart_type == 'grid':
        canvas = getattr(args, 'canvas', 'ppt169')
        coord = CoordinateSystem(canvas, chart_area)
        calc = GridLayoutCalculator(coord)
        cells = calc.calculate(args.rows, args.cols, args.padding, args.gap)
        return '\n'.join(['', f'=== Grid layout ({args.rows}x{args.cols}) ===', f'Canvas: {format_canvas_label(canvas)}', calc.format_table(cells)])

    raise ValueError(f'Unsupported chart type: {args.chart_type}')


def handle_validate_command(args: argparse.Namespace) -> str:
    validator = SVGPositionValidator(tolerance=args.tolerance)
    if not args.extract:
        return 'Validation mode currently supports --extract only. Use --extract to inspect all detected positions.'

    svg_path = Path(args.svg_file)
    positions = validator.extract_all_positions(read_text_file(svg_path))
    lines = ['', '=== Extracted element positions ===', f'File: {svg_path}', '']
    for element_id, attrs in positions.items():
        lines.append(f'{element_id}:')
        for attr_name, value in attrs.items():
            lines.append(f'  {attr_name}: {value}')
    return '\n'.join(lines)


def execute_parsed_command(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
    *,
    output_fn: OutputFn = print,
    calc_handler: Callable[[argparse.Namespace], str] = handle_calc_command,
    validate_handler: Callable[[argparse.Namespace], str] = handle_validate_command,
    analyze_handler: Callable[[str | Path], str] = analyze_svg_file,
    interactive_runner: Callable[[], int] = interactive_mode,
    json_loader: Callable[[str | Path], str] = from_json_config,
) -> int:
    """Execute a parsed CLI command with injectable handlers for testing."""

    if args.command == 'calc':
        if not getattr(args, 'chart_type', None):
            parser.print_help()
            return 1
        output_fn(calc_handler(args))
        return 0

    if args.command == 'validate':
        output_fn(validate_handler(args))
        return 0

    if args.command == 'analyze':
        output_fn(analyze_handler(args.svg_file))
        return 0

    if args.command == 'interactive':
        return interactive_runner()

    if args.command == 'from-json':
        output_fn(json_loader(args.config_file))
        return 0

    parser.print_help()
    return 1


def run_cli(argv: Optional[Sequence[str]] = None) -> int:
    configure_console_encoding()
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return execute_parsed_command(args, parser)


def main() -> None:
    raise SystemExit(run_cli())


__all__ = [
    'analyze_svg_file',
    'build_chart_area',
    'build_parser',
    'configure_console_encoding',
    'execute_parsed_command',
    'format_canvas_label',
    'from_json_config',
    'handle_calc_command',
    'handle_validate_command',
    'interactive_mode',
    'main',
    'read_text_file',
    'render_custom_line_report',
    'run_cli',
]
