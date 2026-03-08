"""Shared PDF-to-Markdown extraction service for PPT Master."""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set

try:
    import fitz  # type: ignore[import-not-found]
except ImportError as exc:  # pragma: no cover - dependency availability check
    fitz = None
    FITZ_IMPORT_ERROR = exc
else:
    FITZ_IMPORT_ERROR = None


MONTHS_EN_PATTERN = (
    r'(?:January|February|March|April|May|June|July|August|September|October|November|December)'
)


def require_pymupdf() -> None:
    """Ensure PyMuPDF is available before attempting PDF extraction."""

    if fitz is None:
        raise RuntimeError('PyMuPDF is required. Install it with: pip install PyMuPDF')


def analyze_font_sizes(doc: Any) -> Dict[str, float]:
    """Analyze document font sizes to infer heading levels."""

    size_counter: Counter[float] = Counter()

    for page in doc:
        blocks = page.get_text('dict')['blocks']
        for block in blocks:
            if block['type'] != 0:
                continue
            for line in block['lines']:
                for span in line['spans']:
                    size = round(span['size'], 1)
                    text = span['text'].strip()
                    if text:
                        size_counter[size] += len(text)

    if not size_counter:
        return {'body': 12, 'h1': 24, 'h2': 18, 'h3': 14}

    sorted_sizes = sorted(size_counter.items(), key=lambda item: item[1], reverse=True)
    body_size = sorted_sizes[0][0]
    all_sizes = sorted(size_counter.keys(), reverse=True)
    larger_sizes = [size for size in all_sizes if size > body_size + 1]

    size_map: Dict[str, float] = {'body': body_size}
    if len(larger_sizes) >= 1:
        size_map['h1'] = larger_sizes[0]
    if len(larger_sizes) >= 2:
        size_map['h2'] = larger_sizes[1]
    if len(larger_sizes) >= 3:
        size_map['h3'] = larger_sizes[2]
    return size_map


def get_heading_level(
    size: float,
    size_map: Dict[str, float],
    text: str = '',
    flags: int = 0,
    strict: bool = True,
) -> int:
    """Infer a heading level from font size, style, and textual hints."""

    level = 0
    if 'h1' in size_map and size >= size_map['h1'] - 0.5:
        level = 1
    elif 'h2' in size_map and size >= size_map['h2'] - 0.5:
        level = 2
    elif 'h3' in size_map and size >= size_map['h3'] - 0.5:
        level = 3

    if level == 0:
        return 0
    if not strict or not text:
        return level

    stripped_text = text.strip()
    if len(stripped_text) > 80:
        return 0

    sentence_endings = '.。!！?？'
    if stripped_text and stripped_text[-1] in sentence_endings:
        if not re.match('^[\\d\\u7b2c]+[.\\u3001\\u7ae0\\u8282]', stripped_text):
            return 0

    is_bold = bool(flags & 16)
    if not is_bold and level >= 2:
        body_size = size_map.get('body', 12)
        if size < body_size + 2:
            return 0

    return level


def is_monospace_font(font_name: str) -> bool:
    """Return whether a font name likely represents a monospace font."""

    if not font_name:
        return False
    font_lower = font_name.lower()
    mono_fonts = [
        'courier',
        'consolas',
        'monaco',
        'menlo',
        'monospace',
        'source code',
        'fira code',
        'jetbrains',
        'inconsolata',
        'dejavu sans mono',
        'liberation mono',
        'ubuntu mono',
        'roboto mono',
        'robotomono',
        'sf mono',
        'cascadia',
        'hack',
    ]
    return any(font in font_lower for font in mono_fonts)


def format_span_text(text: str, flags: int) -> str:
    """Apply inline markdown emphasis based on PDF font flags."""

    stripped = text.strip()
    if not stripped:
        return ''

    is_bold = bool(flags & 16)
    is_italic = bool(flags & 2)

    if is_bold and is_italic:
        return f'***{stripped}***'
    if is_bold:
        return f'**{stripped}**'
    if is_italic:
        return f'*{stripped}*'
    return stripped


def detect_list_item(text: str) -> tuple[bool, Optional[str], str]:
    """Detect unordered or ordered list markers in extracted lines."""

    stripped = text.strip()
    unordered_patterns = [
        (r'^[•●○◦▪▸►]\s*', '-'),
        (r'^[-–—]\s+', '-'),
        (r'^\*\s+', '-'),
    ]
    for pattern, marker in unordered_patterns:
        match = re.match(pattern, stripped)
        if match:
            return (True, 'ul', marker + ' ' + stripped[match.end():])

    ordered_match = re.match(r'^(\d+)[.、)]\s*', stripped)
    if ordered_match:
        number = ordered_match.group(1)
        return (True, 'ol', f"{number}. {stripped[ordered_match.end():]}")

    return (False, None, stripped)


def remove_page_footer(text: str) -> str:
    """Remove common footer patterns such as month-year-page-number strings."""

    pattern_en = rf'\s*{MONTHS_EN_PATTERN}\s+\d{{4}}\s+\d{{1,3}}\s*$'
    cleaned = re.sub(pattern_en, '', text, flags=re.IGNORECASE)
    pattern_cn = r'\s*\d{4}年\d{1,2}月\s+\d{1,3}\s*$'
    cleaned = re.sub(pattern_cn, '', cleaned)
    return cleaned.rstrip()


def detect_headers_footers(doc: Any, threshold_ratio: float = 0.6) -> Set[str]:
    """Detect repeated header and footer text blocks across pages."""

    if len(doc) < 3:
        return set()

    headers: List[str] = []
    footers: List[str] = []

    pages_to_scan = list(range(len(doc)))
    if len(doc) > 40:
        pages_to_scan = pages_to_scan[:20] + pages_to_scan[-20:]

    for page_index in pages_to_scan:
        page = doc[page_index]
        rect = page.rect
        height = rect.height
        top_rect = fitz.Rect(0, 0, rect.width, height * 0.15)
        bottom_rect = fitz.Rect(0, height * 0.85, rect.width, height)

        for block in page.get_text('blocks'):
            block_rect = fitz.Rect(block[:4])
            text = block[4].strip()
            if not text:
                continue
            if block_rect.intersects(top_rect):
                headers.append(text)
            elif block_rect.intersects(bottom_rect):
                footers.append(text)

    noise_texts: Set[str] = set()
    total_scanned = len(pages_to_scan)
    for collection in (headers, footers):
        counter = Counter(collection)
        for text, count in counter.items():
            if count / total_scanned > threshold_ratio:
                noise_texts.add(text)
    return noise_texts


def merge_adjacent_headings(elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge consecutive short headings of the same level."""

    if not elements:
        return elements

    merged: List[Dict[str, Any]] = []
    index = 0
    while index < len(elements):
        element = elements[index]
        if element.get('type') != 0 or not element.get('is_heading'):
            merged.append(element)
            index += 1
            continue

        match = re.match(r'^(#{1,6})\s+(.+)$', element['content'])
        if not match:
            merged.append(element)
            index += 1
            continue

        level = match.group(1)
        title_text = match.group(2)

        next_index = index + 1
        while next_index < len(elements) and len(title_text) < 60:
            next_element = elements[next_index]
            if next_element.get('type') != 0 or not next_element.get('is_heading'):
                break

            next_match = re.match(r'^(#{1,6})\s+(.+)$', next_element['content'])
            if not next_match or next_match.group(1) != level:
                break

            next_text = next_match.group(2)
            if len(next_text) > 40:
                break

            title_text += ' ' + next_text
            next_index += 1

        merged_element = element.copy()
        merged_element['content'] = f'{level} {title_text}'
        merged.append(merged_element)
        index = next_index

    return merged


def clean_text(text: str) -> str:
    """Remove duplicate empty lines while preserving paragraph structure."""

    lines = text.split('\n')
    cleaned_lines: List[str] = []
    previous_empty = False

    for line in lines:
        trimmed = line.rstrip()
        is_empty = len(trimmed.strip()) == 0
        if is_empty:
            if not previous_empty:
                cleaned_lines.append('')
            previous_empty = True
            continue
        cleaned_lines.append(trimmed)
        previous_empty = False

    return '\n'.join(cleaned_lines)


def merge_adjacent_formatting(text: str) -> str:
    """Normalize adjacent markdown emphasis markers."""

    normalized = re.sub(r'\*\*\s*\*\*', ' ', text)
    normalized = re.sub(r'\*\s*\*', ' ', normalized)
    normalized = re.sub(r'\*\*\*\s*\*\*\*', ' ', normalized)
    return normalized


def is_sentence_end(text: str) -> bool:
    """Return whether the text ends with sentence punctuation."""

    stripped = text.rstrip()
    if not stripped:
        return True
    end_punctuation = '.。!！?？:：;；'
    return stripped[-1] in end_punctuation


def should_merge_lines(current: Dict[str, Any], next_line: Dict[str, Any]) -> bool:
    """Return whether two consecutive lines should be merged into one paragraph."""

    if current.get('is_heading') or next_line.get('is_heading'):
        return False
    if current.get('is_list') or next_line.get('is_list'):
        return False
    if is_sentence_end(current.get('content', '')):
        return False
    return True


def extract_pdf_to_markdown(pdf_path: str, output_path: Optional[str] = None) -> str:
    """Extract text, tables, and images from a PDF and render markdown."""

    require_pymupdf()
    try:
        doc = fitz.open(pdf_path)
    except Exception as exc:
        print(f'[ERROR] Unable to open PDF file: {exc}')
        return ''

    filename = Path(pdf_path).stem
    title = re.sub(r'^\d+-', '', filename).strip()

    print('[INFO] Analyzing document structure...')
    size_map = analyze_font_sizes(doc)
    print(
        '   Font size map: '
        f"body={size_map.get('body', 'N/A')}, "
        f"H1={size_map.get('h1', 'N/A')}, "
        f"H2={size_map.get('h2', 'N/A')}, "
        f"H3={size_map.get('h3', 'N/A')}"
    )

    print('[INFO] Detecting repeated headers and footers...')
    noise_texts = detect_headers_footers(doc)
    if noise_texts:
        print(f'   Found {len(noise_texts)} repeated noise block(s) to remove:')
        for text in list(noise_texts)[:3]:
            print(f'     - {text[:30]}...')

    markdown_content = f'# {title}\n\n'

    image_dir: Optional[Path] = None
    relative_image_dir = 'images'
    if output_path:
        resolved_output_path = Path(output_path)
        image_dir = resolved_output_path.parent / relative_image_dir
        image_dir.mkdir(parents=True, exist_ok=True)

    image_count = 0

    for page_num, page in enumerate(doc, 1):
        if page_num > 1:
            markdown_content += f'\n\n<!-- Page {page_num} -->\n\n'

        try:
            tables = page.find_tables()
        except Exception:
            tables = []

        table_rects = [fitz.Rect(table.bbox) for table in tables]
        page_elements: List[Dict[str, Any]] = []

        for table in tables:
            page_elements.append({'y0': table.bbox[1], 'type': 2, 'content': table.to_markdown()})
            print(f'  [OK] Table detected: P{page_num}')

        blocks = page.get_text('dict')['blocks']
        for block in blocks:
            block_rect = fitz.Rect(block['bbox'])
            is_in_table = False
            for table_rect in table_rects:
                intersection = block_rect & table_rect
                if intersection.get_area() > 0.6 * block_rect.get_area():
                    is_in_table = True
                    break
            if is_in_table:
                continue

            if block['type'] == 0:
                block_text_full = ''.join(
                    span['text'] for line in block['lines'] for span in line['spans']
                ).strip()
                if block_text_full in noise_texts:
                    continue

                for line in block['lines']:
                    line_size = 0.0
                    line_flags = 0
                    is_code_line = False
                    formatted_spans: List[str] = []

                    for span in line['spans']:
                        span_text = span['text']
                        if not span_text.strip():
                            if span_text:
                                formatted_spans.append(span_text)
                            continue

                        span_size = span['size']
                        span_flags = span['flags']
                        line_size = max(line_size, span_size)
                        line_flags |= span_flags

                        heading_level = get_heading_level(span_size, size_map, span_text, span_flags)
                        font_name = span.get('font', '')
                        if is_monospace_font(font_name):
                            is_code_line = True
                            formatted_spans.append(span_text)
                        elif heading_level > 0:
                            formatted_spans.append(span_text.strip())
                        else:
                            formatted_spans.append(format_span_text(span_text, span_flags))

                    line_text = ''.join(formatted_spans).strip()
                    if not line_text or line_text in noise_texts:
                        continue

                    line_text = merge_adjacent_formatting(line_text)
                    heading_level = get_heading_level(line_size, size_map, line_text, line_flags)
                    is_list, _list_type, list_content = detect_list_item(line_text)

                    if heading_level > 0:
                        prefix = '#' * heading_level + ' '
                        clean_line = re.sub(r'\*+([^*]+)\*+', r'\1', line_text)
                        final_text = prefix + clean_line
                    elif is_list:
                        final_text = list_content
                    else:
                        final_text = line_text

                    page_elements.append(
                        {
                            'y0': line['bbox'][1],
                            'type': 0,
                            'content': final_text,
                            'is_heading': heading_level > 0,
                            'is_list': is_list,
                            'is_code': is_code_line,
                        }
                    )
            elif block['type'] == 1:
                page_elements.append({'y0': block['bbox'][1], 'type': 1, 'content': block})

        page_elements.sort(key=lambda element: element['y0'])
        page_elements = merge_adjacent_headings(page_elements)

        merged_elements: List[Dict[str, Any]] = []
        index = 0
        while index < len(page_elements):
            element = page_elements[index]
            if element['type'] == 0 and not element.get('is_heading') and not element.get('is_list'):
                merged_content = element['content']
                next_index = index + 1
                while next_index < len(page_elements):
                    next_element = page_elements[next_index]
                    if next_element['type'] != 0:
                        break
                    if not should_merge_lines(
                        {'content': merged_content, 'is_heading': False, 'is_list': False},
                        next_element,
                    ):
                        break
                    merged_content += ' ' + next_element['content']
                    next_index += 1
                merged_elements.append(
                    {
                        'type': 0,
                        'content': remove_page_footer(merged_content),
                        'is_heading': False,
                        'is_list': False,
                    }
                )
                index = next_index
            else:
                merged_elements.append(element)
                index += 1

        previous_was_list = False
        previous_was_code = False
        code_block_lines: List[str] = []

        def flush_code_block() -> None:
            nonlocal code_block_lines, markdown_content
            if code_block_lines:
                markdown_content += '```\n'
                markdown_content += '\n'.join(code_block_lines) + '\n'
                markdown_content += '```\n\n'
                code_block_lines = []

        for element in merged_elements:
            if element['type'] == 0:
                is_list = element.get('is_list', False)
                is_heading = element.get('is_heading', False)
                is_code = element.get('is_code', False)

                if is_code:
                    if previous_was_list:
                        markdown_content += '\n'
                        previous_was_list = False
                    code_block_lines.append(element['content'])
                    previous_was_code = True
                    continue

                if previous_was_code:
                    flush_code_block()
                    previous_was_code = False

                if is_heading:
                    if previous_was_list:
                        markdown_content += '\n'
                    markdown_content += element['content'] + '\n\n'
                    previous_was_list = False
                elif is_list:
                    markdown_content += element['content'] + '\n'
                    previous_was_list = True
                else:
                    if previous_was_list:
                        markdown_content += '\n'
                    markdown_content += element['content'] + '\n\n'
                    previous_was_list = False

            elif element['type'] == 2:
                if previous_was_code:
                    flush_code_block()
                    previous_was_code = False
                if previous_was_list:
                    markdown_content += '\n'
                markdown_content += element['content'] + '\n\n'
                previous_was_list = False

            elif element['type'] == 1:
                if previous_was_code:
                    flush_code_block()
                    previous_was_code = False
                if image_dir is None:
                    continue

                block = element['content']
                extension = block['ext']
                image_data = block['image']
                safe_filename = filename.replace(' ', '_')
                image_name = f'{safe_filename}_p{page_num}_{image_count}.{extension}'
                image_path = image_dir / image_name

                try:
                    with image_path.open('wb') as handle:
                        handle.write(image_data)
                    if previous_was_list:
                        markdown_content += '\n'
                    markdown_content += f'![{image_name}]({relative_image_dir}/{image_name})\n\n'
                    image_count += 1
                    previous_was_list = False
                    print(f'  [OK] Extracted image: {image_name}')
                except Exception as exc:
                    print(f'  [WARN] Failed to save image: {exc}')

        if previous_was_code:
            flush_code_block()

    doc.close()

    markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)
    markdown_content = markdown_content.strip() + '\n'

    if output_path:
        resolved_output = Path(output_path)
        resolved_output.parent.mkdir(parents=True, exist_ok=True)
        resolved_output.write_text(markdown_content, encoding='utf-8')
        print(f'[OK] Saved Markdown to: {resolved_output}')

    return markdown_content


def process_directory(input_dir: str, output_dir: Optional[str] = None) -> None:
    """Convert every PDF file in a directory into markdown files."""

    input_path = Path(input_dir)
    output_path = Path(output_dir) if output_dir else input_path
    pdf_files = sorted(input_path.glob('*.pdf'))

    print(f'Found {len(pdf_files)} PDF file(s)')
    for pdf_file in pdf_files:
        output_file = output_path / f'{pdf_file.stem}.md'
        print(f'Processing: {pdf_file.name}')
        extract_pdf_to_markdown(str(pdf_file), str(output_file))


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for PDF-to-Markdown conversion."""

    parser = argparse.ArgumentParser(
        description='PDF to Markdown converter with structure-aware extraction.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python3 skills/ppt_master_workflow/commands/pdf_to_md.py book.pdf
  python3 skills/ppt_master_workflow/commands/pdf_to_md.py book.pdf -o output.md
  python3 skills/ppt_master_workflow/commands/pdf_to_md.py ./pdfs
  python3 skills/ppt_master_workflow/commands/pdf_to_md.py ./pdfs -o ./markdown

Extraction features:
  - Detect heading levels from font sizes
  - Preserve bold and italic emphasis
  - Detect ordered and unordered lists
  - Extract tables as Markdown when available
  - Remove repeated headers and footers
  - Insert <!-- Page N --> delimiters for downstream LLM processing
''',
    )
    parser.add_argument('input', help='PDF file or directory containing PDF files')
    parser.add_argument('-o', '--output', help='Output file or directory')
    return parser


def run_cli(argv: Optional[Sequence[str]] = None) -> int:
    """Execute the CLI entrypoint for PDF conversion."""

    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    input_path = Path(args.input)

    if input_path.is_file():
        output = args.output or str(input_path.with_suffix('.md'))
        extract_pdf_to_markdown(str(input_path), output)
        return 0

    if input_path.is_dir():
        process_directory(str(input_path), args.output)
        return 0

    print(f'[ERROR] File or directory not found: {args.input}')
    return 1


def main() -> None:
    raise SystemExit(run_cli())


__all__ = [
    'MONTHS_EN_PATTERN',
    'analyze_font_sizes',
    'build_parser',
    'clean_text',
    'detect_headers_footers',
    'detect_list_item',
    'extract_pdf_to_markdown',
    'format_span_text',
    'get_heading_level',
    'is_monospace_font',
    'is_sentence_end',
    'main',
    'merge_adjacent_formatting',
    'merge_adjacent_headings',
    'process_directory',
    'remove_page_footer',
    'require_pymupdf',
    'run_cli',
    'should_merge_lines',
]
