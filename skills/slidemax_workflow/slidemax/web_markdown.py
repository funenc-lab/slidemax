"""Shared web-to-Markdown conversion service for SlideMax."""

from __future__ import annotations

import argparse
import datetime as dt
import io
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import urljoin, urlparse

try:
    import requests
except ImportError as exc:  # pragma: no cover - dependency availability check
    requests = None
    REQUESTS_IMPORT_ERROR = exc
else:
    REQUESTS_IMPORT_ERROR = None

try:
    from bs4 import BeautifulSoup, NavigableString
except ImportError as exc:  # pragma: no cover - dependency availability check
    BeautifulSoup = None
    NavigableString = None
    BS4_IMPORT_ERROR = exc
else:
    BS4_IMPORT_ERROR = None

try:
    from PIL import Image
except ImportError:  # pragma: no cover - optional dependency
    Image = None
    PILLOW_AVAILABLE = False
else:
    PILLOW_AVAILABLE = True


DEFAULT_OUTPUT_DIR = Path('./workspace')
DEFAULT_TIMEOUT = 30
DEFAULT_USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/120.0.0.0 Safari/537.36'
)
DEFAULT_ACCEPT_LANGUAGE = 'zh-CN,zh;q=0.9,en;q=0.8'

GOVERNMENT_SUFFIX_PATTERN = re.compile(
    r'[-_|].*?(?:\u653f\u5e9c|\u95e8\u6237|\u7f51\u7ad9|\u59d4\u5458\u4f1a).*$'
)
CHINESE_CHAR_PATTERN = re.compile(r'[\u4e00-\u9fa5]')
DATE_PATTERNS = [
    re.compile(r'(?:\u53d1\u5e03[\u65f6\u65e5]\u95f4[：:]\s*(\d{4}[-/\u5e74]\d{1,2}[-/\u6708]\d{1,2}[\u65e5]?))'),
    re.compile(r'(?:\u65e5\u671f[：:]\s*(\d{4}[-/\u5e74]\d{1,2}[-/\u6708]\d{1,2}[\u65e5]?))'),
    re.compile(r'(\d{4}[-/\u5e74]\d{1,2}[-/\u6708]\d{1,2}[\u65e5]?)\s*(?:\u53d1\u5e03|\u6765\u6e90)'),
    re.compile(r'(?:\u65f6\u95f4[：:]\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2}))'),
]
SOURCE_PATTERNS = [
    re.compile(r'\u6765\u6e90[：:]\s*([^\s<]+)'),
    re.compile(r'\u53d1\u5e03(?:\u5355\u4f4d|\u673a\u6784)[：:]\s*([^\s<]+)'),
]
URL_DATE_PATTERNS = [
    re.compile(r'(\d{4})(\d{2})[/_](?:t\d+_)?'),
    re.compile(r'(\d{4})[-/](\d{2})[-/](\d{2})'),
]


@dataclass(frozen=True)
class WebToMarkdownConfig:
    """Runtime configuration for web page conversion."""

    output_dir: Path = DEFAULT_OUTPUT_DIR
    timeout: int = DEFAULT_TIMEOUT
    user_agent: str = DEFAULT_USER_AGENT
    accept_language: str = DEFAULT_ACCEPT_LANGUAGE
    content_selectors: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PageMetadata:
    """Extracted metadata for a web page."""

    title: str
    date: str = ''
    description: str = ''
    author: str = ''
    source_url: str = ''

    def as_dict(self) -> Dict[str, str]:
        return {
            'title': self.title,
            'date': self.date,
            'description': self.description,
            'author': self.author,
            'source_url': self.source_url,
        }


@dataclass(frozen=True)
class ProcessResult:
    """Outcome for a single URL conversion."""

    success: bool
    url: str
    error: Optional[str] = None
    output_path: Optional[Path] = None
    image_count: int = 0
    content_length: int = 0

    def as_tuple(self) -> tuple[bool, str, Optional[str]]:
        return (self.success, self.url, self.error)


DEFAULT_CONFIG = WebToMarkdownConfig(
    content_selectors=(
        {'class_': re.compile(r'tys-main-zt-show', re.I)},
        {'class_': re.compile(r'tys-main', re.I)},
        {'class_': 'TRS_Editor'},
        {'class_': 'TRS_UEDITOR'},
        {'class_': 'ucontent'},
        {'class_': 'article-content'},
        {'class_': 'news-content'},
        {'class_': 'detail-content'},
        {'class_': 'content-text'},
        {'class_': 'pages_content'},
        {'class_': 'zwgk_content'},
        {'class_': 'content_detail'},
        {'class_': 'text_content'},
        {'class_': 'main-content'},
        {'class_': 'main_content'},
        {'class_': 'view-content'},
        {'class_': 'info-content'},
        {'id': 'Zoom'},
        {'id': 'content'},
        {'id': 'article'},
        {'class_': 'content'},
        {'name': 'article'},
        {'name': 'main'},
    )
)

CONFIG = {
    'output_dir': str(DEFAULT_OUTPUT_DIR),
    'timeout': DEFAULT_TIMEOUT,
    'user_agent': DEFAULT_USER_AGENT,
    'content_selectors': list(DEFAULT_CONFIG.content_selectors),
}


def require_runtime_dependencies() -> None:
    """Validate optional runtime dependencies required for this command."""

    missing: List[str] = []
    if requests is None:
        missing.append('requests')
    if BeautifulSoup is None or NavigableString is None:
        missing.append('beautifulsoup4')
    if missing:
        package_list = ' '.join(missing)
        raise RuntimeError(f'Missing required dependencies: {package_list}. Install with: pip install {package_list}')


def disable_insecure_request_warnings() -> None:
    """Silence urllib3 warnings because this converter uses verify=False for compatibility."""

    try:
        import urllib3
    except ImportError:  # pragma: no cover - optional transitively provided dependency
        return
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def build_config(output_dir: Optional[str | Path] = None) -> WebToMarkdownConfig:
    """Create an immutable configuration from defaults or CLI overrides."""

    resolved_output_dir = Path(output_dir).expanduser() if output_dir else Path(CONFIG['output_dir']).expanduser()
    return WebToMarkdownConfig(
        output_dir=resolved_output_dir,
        timeout=int(CONFIG['timeout']),
        user_agent=str(CONFIG['user_agent']),
        accept_language=DEFAULT_ACCEPT_LANGUAGE,
        content_selectors=tuple(CONFIG['content_selectors']),
    )


def fetch_url(url: str, config: Optional[WebToMarkdownConfig] = None) -> str:
    """Fetch a URL with headers, timeout handling, and encoding detection."""

    require_runtime_dependencies()
    runtime_config = config or build_config()
    headers = {
        'User-Agent': runtime_config.user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': runtime_config.accept_language,
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=runtime_config.timeout,
            verify=False,
        )
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        return response.text
    except Exception as exc:
        raise RuntimeError(f'Failed to fetch {url}: {exc}') from exc


def clean_title(title: str) -> str:
    """Remove common site suffixes from page titles."""

    if not title:
        return ''
    return GOVERNMENT_SUFFIX_PATTERN.sub('', title).strip()


def sanitize_filename(name: str) -> str:
    """Convert arbitrary text into a safe filename."""

    normalized = re.sub(r'\s+', '_', name)
    normalized = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9_]', '', normalized)
    normalized = re.sub(r'_+', '_', normalized)
    return normalized[:80]


def derive_base_name(title: str, url: str) -> str:
    """Derive a stable markdown filename stem from title or URL."""

    base_name = sanitize_filename(title or '')
    if base_name:
        return base_name

    parsed = urlparse(url)
    path = parsed.path.strip('/')
    candidate = f'{parsed.netloc}_{path}' if path else (parsed.netloc or 'untitled')
    base_name = sanitize_filename(candidate)
    if base_name:
        return base_name

    timestamp = dt.datetime.now().strftime('%Y%m%d_%H%M%S')
    return f'untitled_{timestamp}'


def build_image_filename(abs_url: str, seq: int, content_type: Optional[str] = None) -> str:
    """Build a stable local filename for a downloaded image."""

    parsed = urlparse(abs_url)
    basename = os.path.basename(parsed.path).split('?')[0]
    stem, extension = os.path.splitext(basename)

    if not extension or len(extension) > 5 or '/' in extension:
        extension = ''

    if not extension and content_type:
        content_type_value = content_type.split(';')[0].lower()
        extension_map = {
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
        }
        extension = extension_map.get(content_type_value, '')

    if not extension:
        extension = '.jpg'

    stem_value = sanitize_filename(stem) if stem else f'image_{seq}'
    return f'{stem_value}{extension}'


def _resolve_unique_path(directory: Path, filename: str) -> Path:
    candidate = directory / filename
    stem = candidate.stem
    extension = candidate.suffix
    counter = 1
    while candidate.exists():
        candidate = directory / f'{stem}_{counter}{extension}'
        counter += 1
    return candidate


def _download_binary(url: str, config: WebToMarkdownConfig) -> Any:
    headers = {'User-Agent': config.user_agent}
    response = requests.get(
        url,
        headers=headers,
        timeout=config.timeout,
        verify=False,
    )
    response.raise_for_status()
    return response


def download_and_rewrite_images(
    content_element: Any,
    page_url: str,
    image_dir: str | Path,
    rel_prefix: str,
    config: Optional[WebToMarkdownConfig] = None,
) -> int:
    """Download images within the selected content block and rewrite image sources."""

    require_runtime_dependencies()
    runtime_config = config or build_config()
    if content_element is None:
        return 0

    images = list(content_element.find_all('img'))
    if not images:
        return 0

    image_directory = Path(image_dir)
    image_directory.mkdir(parents=True, exist_ok=True)
    downloaded: Dict[str, str] = {}
    saved_count = 0

    for index, image_node in enumerate(images):
        src = image_node.get('src')
        if not src or src.startswith('data:'):
            continue

        absolute_url = urljoin(page_url, src)
        if absolute_url in downloaded:
            saved_name = downloaded[absolute_url]
        else:
            try:
                response = _download_binary(absolute_url, runtime_config)
                filename = build_image_filename(absolute_url, index, response.headers.get('Content-Type'))

                stem = Path(filename).stem
                extension = Path(filename).suffix
                content_type = response.headers.get('Content-Type', '').lower()
                is_webp = extension.lower() == '.webp' or 'webp' in content_type

                if is_webp and PILLOW_AVAILABLE and Image is not None:
                    try:
                        image_bytes = io.BytesIO(response.content)
                        pil_image = Image.open(image_bytes)
                        output_path = _resolve_unique_path(image_directory, f'{stem}.png')
                        pil_image.save(output_path, 'PNG', optimize=False)
                        pil_image.close()
                        filename = output_path.name
                        print(f'   [INFO] Converted webp to png: {filename}')
                    except Exception as exc:
                        print(f'   [WARN] Failed to convert webp: {exc}; saving original payload.')
                        output_path = _resolve_unique_path(image_directory, f'{stem}{extension or ".webp"}')
                        output_path.write_bytes(response.content)
                        filename = output_path.name
                else:
                    output_path = _resolve_unique_path(image_directory, filename)
                    output_path.write_bytes(response.content)
                    filename = output_path.name

                downloaded[absolute_url] = filename
                saved_name = filename
                saved_count += 1
            except Exception as exc:
                print(f'   [WARN] Skip image {absolute_url}: {exc}')
                continue

        relative_path = Path(rel_prefix, saved_name).as_posix() if rel_prefix else saved_name
        image_node['src'] = relative_path

    return saved_count


def extract_metadata(soup: Any, url: str) -> Dict[str, str]:
    """Extract title, publication date, description, and author metadata."""

    title_tag = soup.title
    title = clean_title(title_tag.string if title_tag else '')

    metas: Dict[str, str] = {}
    for meta in soup.find_all('meta'):
        name = meta.get('name') or meta.get('property')
        content = meta.get('content')
        if name and content:
            metas[name.lower()] = content.strip()

    date = (
        metas.get('article:published_time')
        or metas.get('og:published_time')
        or metas.get('pubdate')
        or metas.get('publishdate')
        or metas.get('date')
    )

    text_content = soup.get_text()
    if not date:
        for pattern in DATE_PATTERNS:
            match = pattern.search(text_content)
            if match:
                date = match.group(1).replace('\u5e74', '-').replace('\u6708', '-').replace('\u65e5', '')
                break

    if not date:
        for index, pattern in enumerate(URL_DATE_PATTERNS):
            match = pattern.search(url)
            if not match:
                continue
            if index == 0:
                date = f'{match.group(1)}-{match.group(2)}'
            else:
                date = f'{match.group(1)}-{match.group(2)}-{match.group(3)}'
            break

    description = metas.get('description') or metas.get('og:description') or metas.get('twitter:description') or ''

    author = metas.get('author') or metas.get('article:author')
    if not author:
        for pattern in SOURCE_PATTERNS:
            match = pattern.search(text_content)
            if match:
                author = match.group(1)
                break

    metadata = PageMetadata(
        title=title or metas.get('og:title') or 'Untitled',
        date=date or '',
        description=description,
        author=author or '',
        source_url=url,
    )
    return metadata.as_dict()


def find_main_content(soup: Any, config: Optional[WebToMarkdownConfig] = None) -> Any:
    """Find the most likely article body using content selectors and scoring heuristics."""

    runtime_config = config or build_config()
    for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'noscript', 'iframe']):
        tag.decompose()

    best_element = None
    max_score = 0

    for selector in runtime_config.content_selectors:
        if 'name' in selector:
            elements = soup.find_all(selector['name'])
        else:
            elements = soup.find_all(attrs=selector)

        for element in elements:
            text = element.get_text(strip=True)
            length = len(text)
            if length < 100:
                continue

            chinese_count = len(CHINESE_CHAR_PATTERN.findall(text))
            score = length + (chinese_count * 2)
            if score > max_score:
                max_score = score
                best_element = element

    if not best_element or max_score < 200:
        for div in soup.find_all('div'):
            paragraph_count = len(div.find_all('p', recursive=False))
            text = div.get_text(strip=True)
            if len(text) <= 200 or paragraph_count < 1:
                continue

            chinese_count = len(CHINESE_CHAR_PATTERN.findall(text))
            score = len(text) + (chinese_count * 2) + (paragraph_count * 50)
            if score > max_score:
                max_score = score
                best_element = div

    return best_element if best_element is not None else soup.body


def element_to_markdown(element: Any) -> str:
    """Convert a single HTML element and its descendants to markdown."""

    if element is None:
        return ''

    if NavigableString is not None and isinstance(element, NavigableString):
        return str(element)

    tag_name = getattr(element, 'name', None)
    if not tag_name:
        return ''

    if tag_name in {'script', 'style', 'meta', 'link'}:
        return ''

    content = ''.join(element_to_markdown(child) for child in element.children)

    if tag_name in {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}:
        level = int(tag_name[1])
        return f"\n{'#' * level} {content.strip()}\n\n"
    if tag_name == 'p':
        content = re.sub(r'\s+', ' ', content).strip()
        return f'\n{content}\n\n' if content else ''
    if tag_name == 'br':
        return '  \n'
    if tag_name == 'hr':
        return '\n---\n'
    if tag_name == 'div':
        return f'\n{content}\n'
    if tag_name == 'blockquote':
        lines = content.strip().split('\n')
        quoted = '\n'.join(f'> {line}' for line in lines if line.strip())
        return f'\n{quoted}\n\n'
    if tag_name in {'ul', 'ol'}:
        return f'\n{content}\n'
    if tag_name == 'li':
        return f'- {content.strip()}\n'
    if tag_name == 'pre':
        return f'\n```\n{content}\n```\n\n'
    if tag_name == 'code':
        parent = element.parent
        if parent and getattr(parent, 'name', None) == 'pre':
            return content
        return f'`{content}`'
    if tag_name == 'a':
        href = element.get('href', '')
        if href and not href.startswith('javascript:'):
            return f'[{content}]({href})'
        return content
    if tag_name == 'img':
        src = element.get('src', '')
        alt = element.get('alt', '')
        return f'![{alt}]({src})' if src else ''
    if tag_name == 'table':
        return f'\n{content}\n'
    if tag_name == 'tr':
        return f'{content}|\n'
    if tag_name in {'td', 'th'}:
        return f'| {content.strip()} '
    if tag_name in {'strong', 'b'}:
        return f'**{content}**'
    if tag_name in {'em', 'i'}:
        return f'*{content}*'
    if tag_name in {'del', 's', 'strike'}:
        return f'~~{content}~~'

    return f'{content} '


def simple_html_to_markdown_traversal(root: Any) -> str:
    """Traverse a content subtree and convert it to markdown."""

    def traverse(node: Any) -> str:
        if NavigableString is not None and isinstance(node, NavigableString):
            text = re.sub(r'\s+', ' ', str(node))
            return text if text.strip() else ''

        tag_name = getattr(node, 'name', None)
        if tag_name in {'script', 'style', 'comment', 'meta', 'link'}:
            return ''

        if tag_name in {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}:
            level = int(tag_name[1])
            return f"\n\n{'#' * level} {''.join(traverse(child) for child in node.children)}\n\n"
        if tag_name == 'p':
            return f"\n\n{''.join(traverse(child) for child in node.children)}\n\n"
        if tag_name == 'li':
            return f"\n- {''.join(traverse(child) for child in node.children)}"
        if tag_name == 'blockquote':
            return f"\n> {''.join(traverse(child) for child in node.children)}\n"
        if tag_name == 'hr':
            return '\n\n---\n\n'
        if tag_name == 'br':
            return '  \n'
        if tag_name == 'pre':
            return f"\n\n```\n{node.get_text()}\n```\n\n"

        if tag_name in {'strong', 'b'}:
            return f"**{''.join(traverse(child) for child in node.children)}**"
        if tag_name in {'em', 'i'}:
            return f"*{''.join(traverse(child) for child in node.children)}*"
        if tag_name == 'code' and getattr(node.parent, 'name', None) != 'pre':
            return f"`{''.join(traverse(child) for child in node.children)}`"
        if tag_name == 'a':
            href = node.get('href')
            content = ''.join(traverse(child) for child in node.children)
            if href and not href.startswith('javascript:'):
                return f'[{content}]({href})'
            return content
        if tag_name == 'img':
            src = node.get('src')
            alt = node.get('alt', '')
            return f'![{alt}]({src})' if src else ''

        inner_text = ''.join(traverse(child) for child in node.children)

        if tag_name == 'tr':
            cells = [cell.get_text(strip=True) for cell in node.find_all(['td', 'th'], recursive=False)]
            return f"| {' | '.join(cells)} |\n"
        if tag_name == 'table':
            return f'\n\n{inner_text}\n\n'

        return inner_text

    markdown = traverse(root)
    markdown = re.sub(r'\n{3,}', '\n\n', markdown).strip() if markdown else ''
    return markdown or ''


def render_markdown_document(
    metadata: Dict[str, str],
    markdown_text: str,
    url: str,
    *,
    crawled_at: Optional[dt.datetime] = None,
) -> str:
    """Build the final markdown document including metadata header."""

    timestamp = (crawled_at or dt.datetime.now()).isoformat()
    output: List[str] = [
        '<!--',
        f'  Source: {url}',
        f'  Crawled: {timestamp}',
    ]

    if metadata.get('date'):
        output.append(f"  Published: {metadata['date']}")
    if metadata.get('author'):
        output.append(f"  Author: {metadata['author']}")
    output.append('-->\n')

    if metadata.get('title'):
        output.append(f"# {metadata['title']}\n")
    if metadata.get('description'):
        output.append(f"> {metadata['description']}\n")

    output.append(markdown_text)
    return '\n'.join(output)


def resolve_output_path(
    metadata: Dict[str, str],
    url: str,
    output_file: Optional[str | Path],
    config: Optional[WebToMarkdownConfig] = None,
) -> Path:
    """Resolve the markdown output path for a URL."""

    runtime_config = config or build_config()
    if output_file:
        return Path(output_file).expanduser()

    base_name = derive_base_name(metadata.get('title', ''), url)
    return runtime_config.output_dir / f'{base_name}.md'


def process_url(
    url: str,
    output_file: Optional[str | Path] = None,
    config: Optional[WebToMarkdownConfig] = None,
) -> tuple[bool, str, Optional[str]]:
    """Fetch, extract, convert, and save a single URL."""

    result = convert_url(url, output_file=output_file, config=config)
    return result.as_tuple()


def convert_url(
    url: str,
    output_file: Optional[str | Path] = None,
    config: Optional[WebToMarkdownConfig] = None,
) -> ProcessResult:
    """Fetch, extract, convert, and save a single URL with structured result metadata."""

    require_runtime_dependencies()
    disable_insecure_request_warnings()
    runtime_config = config or build_config()

    print(f'\n[Fetching] {url}')
    try:
        html = fetch_url(url, runtime_config)
        soup = BeautifulSoup(html, 'html.parser')

        metadata = extract_metadata(soup, url)
        print(f"   [OK] Title: {metadata['title']}")
        if metadata.get('date'):
            print(f"   [OK] Date: {metadata['date']}")

        output_path = resolve_output_path(metadata, url, output_file, runtime_config)
        output_directory = output_path.parent if output_path.parent != Path('') else Path('.')
        output_directory.mkdir(parents=True, exist_ok=True)
        base_name = output_path.stem
        image_dir = output_directory / f'{base_name}_files'
        rel_image_prefix = os.path.relpath(image_dir, output_directory)

        content_element = find_main_content(soup, runtime_config)
        image_count = download_and_rewrite_images(
            content_element,
            url,
            image_dir,
            rel_image_prefix,
            runtime_config,
        )
        if image_count:
            print(f'   [OK] Images: {image_count} saved to {image_dir}')

        markdown_text = simple_html_to_markdown_traversal(content_element)
        print(f'   [OK] Content: {len(markdown_text)} chars')

        document = render_markdown_document(metadata, markdown_text, url)
        output_path.write_text(document, encoding='utf-8')
        print(f'   [OK] Saved: {output_path}')

        return ProcessResult(
            success=True,
            url=url,
            output_path=output_path,
            image_count=image_count,
            content_length=len(markdown_text),
        )
    except Exception as exc:
        print(f'   [ERROR] {exc}')
        return ProcessResult(success=False, url=url, error=str(exc))


def load_targets(urls: Sequence[str], file_path: Optional[str | Path]) -> List[str]:
    """Load target URLs from CLI positional args and optional file input."""

    targets = [url for url in urls if url]
    if not file_path:
        return targets

    path = Path(file_path).expanduser()
    if not path.exists():
        print(f'Error: File {path} not found')
        return targets

    lines = [
        line.strip()
        for line in path.read_text(encoding='utf-8').splitlines()
        if line.strip() and not line.strip().startswith('#')
    ]
    targets.extend(lines)
    return targets


def process_targets(
    targets: Sequence[str],
    output_file: Optional[str | Path] = None,
    config: Optional[WebToMarkdownConfig] = None,
) -> List[ProcessResult]:
    """Process multiple URLs, applying single-output mode only when valid."""

    runtime_config = config or build_config()
    results: List[ProcessResult] = []
    for url in targets:
        resolved_output = output_file if len(targets) == 1 and output_file else None
        results.append(convert_url(url, output_file=resolved_output, config=runtime_config))
    return results


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for the Python web-to-Markdown converter."""

    parser = argparse.ArgumentParser(description='Web to Markdown Converter (Python)')
    parser.add_argument('urls', nargs='*', help='URLs to process')
    parser.add_argument('-f', '--file', help='File containing URLs (one per line)')
    parser.add_argument('-o', '--output', help='Output file (single URL only)')
    parser.add_argument('-d', '--dir', help='Output directory')
    return parser


def summarize_results(results: Sequence[ProcessResult]) -> None:
    """Print the same summary style as the legacy CLI."""

    success_count = sum(1 for result in results if result.success)
    fail_count = len(results) - success_count

    print(f"\n{'=' * 50}")
    print(f'[Done] Success: {success_count}/{len(results)}, Failed: {fail_count}')

    if fail_count > 0:
        print('\n[Failed URLs]:')
        for result in results:
            if not result.success:
                print(f'   - {result.url}: {result.error}')


def run_cli(argv: Optional[Sequence[str]] = None) -> int:
    """Execute the CLI entrypoint."""

    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.dir:
        CONFIG['output_dir'] = str(Path(args.dir).expanduser())

    targets = load_targets(args.urls, args.file)
    if not targets:
        parser.print_help()
        return 0

    results = process_targets(targets, output_file=args.output, config=build_config())
    summarize_results(results)
    return 0 if all(result.success for result in results) else 1


def main() -> None:
    raise SystemExit(run_cli())


__all__ = [
    'CONFIG',
    'DEFAULT_ACCEPT_LANGUAGE',
    'DEFAULT_CONFIG',
    'DEFAULT_OUTPUT_DIR',
    'DEFAULT_TIMEOUT',
    'DEFAULT_USER_AGENT',
    'GOVERNMENT_SUFFIX_PATTERN',
    'PageMetadata',
    'PILLOW_AVAILABLE',
    'ProcessResult',
    'SOURCE_PATTERNS',
    'DATE_PATTERNS',
    'URL_DATE_PATTERNS',
    'WebToMarkdownConfig',
    'build_config',
    'build_image_filename',
    'build_parser',
    'clean_title',
    'convert_url',
    'derive_base_name',
    'disable_insecure_request_warnings',
    'download_and_rewrite_images',
    'element_to_markdown',
    'extract_metadata',
    'fetch_url',
    'find_main_content',
    'load_targets',
    'main',
    'process_targets',
    'process_url',
    'render_markdown_document',
    'require_runtime_dependencies',
    'resolve_output_path',
    'run_cli',
    'sanitize_filename',
    'simple_html_to_markdown_traversal',
    'summarize_results',
]
