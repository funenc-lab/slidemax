from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, List, Optional, Sequence, Union

from PIL import ExifTags, Image

ORIENTATION_TAG_ID = 274
DEFAULT_OUTPUT_FILENAME = 'image_orientation_tool.html'
AUTO_FIX_EXTENSIONS = {'.jpg', '.jpeg', '.webp'}
PREVIEW_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}


@dataclass(frozen=True)
class PreviewImageItem:
    src: str
    path: str


@dataclass(frozen=True)
class RotationTask:
    path: str
    rotation: Optional[int]


@dataclass(frozen=True)
class RotationStats:
    total: int
    success: int

    def to_dict(self) -> Dict[str, int]:
        return {'total': self.total, 'success': self.success}


USAGE = dedent(
    """
    SlideMax image orientation helper.

    Usage:
        python3 skills/slidemax_workflow/commands/rotate_images.py auto <images_directory>
        python3 skills/slidemax_workflow/commands/rotate_images.py gen <images_directory>
        python3 skills/slidemax_workflow/commands/rotate_images.py fix <fixes.json>
    """
).strip()


HTML_TEMPLATE = dedent(
    """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Image Orientation Review</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; background: #f0f2f5; color: #333; }
            .header {
                position: sticky; top: 0; background: rgba(255,255,255,0.95); padding: 20px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.08); z-index: 100;
                border-radius: 12px; margin-bottom: 20px;
                backdrop-filter: blur(10px);
                display: flex; justify-content: space-between; align-items: center; gap: 16px;
            }
            h2 { margin: 0; font-size: 1.5rem; color: #1a1a1a; }
            .instructions { color: #666; margin-top: 5px; font-size: 0.9rem; }
            .grid {
                display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
                gap: 15px;
            }
            .card {
                background: white; border-radius: 12px; overflow: hidden;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05); text-align: center;
                cursor: pointer; transition: all 0.2s ease;
                position: relative; border: 2px solid transparent;
            }
            .card:hover { transform: translateY(-4px); box-shadow: 0 8px 16px rgba(0,0,0,0.1); }
            .card.modified { border-color: #007bff; background: #f8fbff; }
            .img-wrapper {
                height: 180px; width: 100%; display: flex; align-items: center; justify-content: center;
                background: #e9ecef; overflow: hidden; position: relative;
            }
            img {
                max-width: 100%; max-height: 100%; object-fit: contain;
                transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
            }
            .info { padding: 10px; font-size: 11px; color: #555; word-break: break-all; border-top: 1px solid #eee; }
            .badge {
                position: absolute; top: 10px; right: 10px;
                background: #007bff; color: white; padding: 4px 8px;
                border-radius: 20px; font-size: 11px; font-weight: bold;
                opacity: 0; transform: scale(0.8); transition: all 0.2s;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }
            .card.modified .badge { opacity: 1; transform: scale(1); }
            .btn {
                background: #007bff; color: white; border: none; padding: 10px 24px;
                border-radius: 8px; font-weight: 600; cursor: pointer; transition: background 0.2s;
            }
            .btn:hover { background: #0056b3; }
            #output-modal {
                display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0,0,0,0.5); z-index: 1000; align-items: center; justify-content: center;
            }
            .modal-content {
                background: white; padding: 30px; border-radius: 16px; width: 80%; max-width: 600px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            }
            textarea {
                width: 100%; height: 200px; padding: 10px; border: 1px solid #ddd; border-radius: 8px;
                font-family: inherit; resize: vertical; margin: 15px 0;
                background: #f8f9fa;
            }
        </style>
    </head>
    <body>
    <div class="header">
        <div>
            <h2>Image Orientation Review</h2>
            <div class="instructions">Click a card to rotate the preview (90° → 180° → 270° → 0°). Cards are listed in natural filename order.</div>
        </div>
        <button class="btn" onclick="showCode()">Export Fixes JSON</button>
    </div>

    <div class="grid" id="grid"></div>

    <div id="output-modal" onclick="if(event.target===this)this.style.display='none'">
        <div class="modal-content">
            <h3>Copy the generated JSON</h3>
            <p style="color:#666; font-size: 0.9em;">Send this JSON to the CLI helper or save it as <code>fixes.json</code>.</p>
            <textarea id="output-area" readonly></textarea>
            <div style="text-align: right;">
                <button class="btn" onclick="document.getElementById('output-modal').style.display='none'">Close</button>
            </div>
        </div>
    </div>

    <script>
        const images = __IMAGES__;
        const grid = document.getElementById('grid');

        images.forEach((item) => {
            const card = document.createElement('div');
            card.className = 'card';
            card.setAttribute('data-rotation', 0);
            card.setAttribute('data-path', item.path);

            const filename = item.src.split('/').pop();

            card.innerHTML = `
                <div class="img-wrapper">
                    <img src="${item.src}" alt="${filename}" loading="lazy">
                    <div class="badge">0°</div>
                </div>
                <div class="info">${filename}</div>
            `;

            card.onclick = function () {
                let rotation = parseInt(this.getAttribute('data-rotation'), 10);
                rotation = (rotation + 90) % 360;
                this.setAttribute('data-rotation', rotation);

                const img = this.querySelector('img');
                img.style.transform = `rotate(${rotation}deg)`;

                const badge = this.querySelector('.badge');
                badge.innerText = `${rotation}°`;

                if (rotation > 0) {
                    this.classList.add('modified');
                } else {
                    this.classList.remove('modified');
                }
            };

            grid.appendChild(card);
        });

        async function copyText(text) {
            if (navigator.clipboard && window.isSecureContext) {
                await navigator.clipboard.writeText(text);
                return;
            }

            const area = document.getElementById('output-area');
            area.select();
            document.execCommand('copy');
        }

        async function showCode() {
            const tasks = [];
            document.querySelectorAll('.card').forEach((card) => {
                const rotation = parseInt(card.getAttribute('data-rotation'), 10);
                if (rotation > 0) {
                    tasks.push({
                        path: card.getAttribute('data-path'),
                        rotation,
                    });
                }
            });

            const jsonStr = JSON.stringify(tasks, null, 2);
            const modal = document.getElementById('output-modal');
            const area = document.getElementById('output-area');

            modal.style.display = 'flex';
            area.value = jsonStr;

            try {
                await copyText(jsonStr);
            } catch (error) {
                console.warn('Copy failed:', error);
            }
        }
    </script>
    </body>
    </html>
    """
).strip()


def natural_sort_key(value: Union[str, Path]) -> List[Union[int, str]]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r'(\d+)', str(value))]


def normalize_task_path(path_str: str) -> str:
    normalized = (path_str or '').strip()
    if not normalized:
        return normalized

    normalized = re.sub(r'^file:(?:///?)+', '', normalized, flags=re.IGNORECASE)
    normalized = normalized.replace('\\', '/')
    normalized = re.sub(r'^\./', '', normalized)
    return normalized


def discover_repository_root(start: Path) -> Path:
    start = start.expanduser().resolve()
    for candidate in (start, *start.parents):
        if (candidate / '.git').exists():
            return candidate
    return start.parent.parent


def render_html_tool(items: Sequence[PreviewImageItem]) -> str:
    payload = [{'src': item.src, 'path': item.path} for item in items]
    return HTML_TEMPLATE.replace('__IMAGES__', json.dumps(payload))


class ImageRotator:
    """Manage image orientation fixes for downloaded assets."""

    def __init__(
        self,
        *,
        skill_root: Optional[Path] = None,
        repo_root: Optional[Path] = None,
        working_dir: Optional[Path] = None,
    ) -> None:
        self.skill_root = (skill_root or Path(__file__).resolve().parents[1]).expanduser().resolve()
        self.repo_root = (repo_root or discover_repository_root(self.skill_root)).expanduser().resolve()
        self.working_dir = (working_dir or Path.cwd()).expanduser().resolve()

    @staticmethod
    def _repo_root() -> Path:
        return discover_repository_root(Path(__file__).resolve())

    def _save_in_place(
        self,
        img: Image.Image,
        file_path: Path,
        src_format: Optional[str],
        *,
        exif_bytes: Optional[bytes] = None,
        icc_profile: Optional[bytes] = None,
    ) -> None:
        format_name = (src_format or '').upper()
        save_kwargs: Dict[str, Any] = {}

        if icc_profile:
            save_kwargs['icc_profile'] = icc_profile
        if exif_bytes:
            save_kwargs['exif'] = exif_bytes

        if format_name in {'JPEG', 'JPG'}:
            save_kwargs['quality'] = 95
            if img.mode not in {'RGB', 'L'}:
                img = img.convert('RGB')
        elif format_name == 'WEBP':
            save_kwargs['quality'] = 95

        try:
            img.save(file_path, **save_kwargs)
        except TypeError:
            save_kwargs.pop('exif', None)
            save_kwargs.pop('icc_profile', None)
            img.save(file_path, **save_kwargs)

    def auto_fix_exif(self, target_dir: Union[str, Path]) -> int:
        target_path = Path(target_dir).expanduser().resolve()
        if not target_path.exists() or not target_path.is_dir():
            return 0

        print('[AUTO] Inspecting EXIF orientation metadata...')
        fixed_count = 0
        files = [
            path for path in target_path.iterdir() if path.is_file() and path.suffix.lower() in AUTO_FIX_EXTENSIONS
        ]

        for file_path in files:
            if self._fix_single_exif(file_path):
                fixed_count += 1

        if fixed_count > 0:
            print(f'[OK] Auto-fixed EXIF orientation on {fixed_count} image(s).')
        else:
            print('[INFO] No EXIF orientation fixes were required.')

        return fixed_count

    def generate_html_tool(
        self,
        target_dir: Union[str, Path],
        output_filename: str = DEFAULT_OUTPUT_FILENAME,
    ) -> str:
        target_path = Path(target_dir).expanduser().resolve()
        if not target_path.exists():
            raise FileNotFoundError(f'Directory not found: {target_path}')
        if not target_path.is_dir():
            raise NotADirectoryError(f'Not a directory: {target_path}')

        self.auto_fix_exif(target_path)

        project_root = target_path.parent
        output_path = project_root / output_filename
        preview_items = self._collect_preview_items(target_path, project_root)
        output_path.write_text(render_html_tool(preview_items), encoding='utf-8')
        return str(output_path)

    def apply_fixes(self, json_source: Union[str, Path, List[Dict[str, Any]]]) -> Dict[str, int]:
        tasks, json_file_dir = self._load_tasks(json_source)
        print(f'[WORK] Processing {len(tasks)} rotation task(s)...')
        print('=' * 60)

        success_count = 0
        for task in tasks:
            rel_path = normalize_task_path(task.path)
            rotation = task.rotation
            if not rel_path or rotation is None:
                continue

            target_file = self._resolve_task_file(rel_path, json_file_dir=json_file_dir)
            if target_file is None or not target_file.exists():
                print(f'[SKIP] File not found: {rel_path}')
                continue

            try:
                self._rotate_single_image(target_file, rotation)
                print(f'[OK] {target_file.name} rotated by {rotation}°')
                success_count += 1
            except Exception as exc:
                print(f'[ERROR] {target_file.name}: {exc}')

        return RotationStats(total=len(tasks), success=success_count).to_dict()

    def _load_tasks(
        self,
        json_source: Union[str, Path, List[Dict[str, Any]]],
    ) -> tuple[List[RotationTask], Optional[Path]]:
        json_file_dir: Optional[Path] = None

        if isinstance(json_source, list):
            raw_tasks = json_source
        else:
            source_text = str(json_source)
            source_path = Path(source_text).expanduser()
            if source_text.endswith('.json') or source_path.exists():
                json_file = source_path.resolve()
                json_file_dir = json_file.parent
                with json_file.open('r', encoding='utf-8') as handle:
                    raw_tasks = json.load(handle)
            else:
                try:
                    raw_tasks = json.loads(source_text)
                except json.JSONDecodeError as exc:
                    raise ValueError('Input must be a JSON file path or a valid JSON string.') from exc

        if not isinstance(raw_tasks, list):
            raise ValueError('Rotation tasks must be a JSON array.')

        tasks: List[RotationTask] = []
        for item in raw_tasks:
            if not isinstance(item, dict):
                tasks.append(RotationTask(path='', rotation=None))
                continue

            rotation: Optional[int]
            raw_rotation = item.get('rotation')
            if raw_rotation is None:
                rotation = None
            else:
                try:
                    rotation = int(raw_rotation)
                except (TypeError, ValueError):
                    rotation = None

            tasks.append(RotationTask(path=str(item.get('path', '')), rotation=rotation))

        return tasks, json_file_dir

    def _resolve_task_file(self, rel_path: str, *, json_file_dir: Optional[Path]) -> Optional[Path]:
        target_file = Path(rel_path)
        if target_file.is_absolute():
            return target_file

        candidates = [
            self.repo_root / rel_path,
            self.working_dir / rel_path,
            self.skill_root / rel_path,
        ]
        if json_file_dir is not None:
            candidates.append(json_file_dir / rel_path)

        workspace_candidates = [
            self.repo_root / 'workspace' / rel_path,
            self.working_dir / 'workspace' / rel_path,
            self.skill_root / 'workspace' / rel_path,
        ]
        candidates.extend(workspace_candidates)
        if json_file_dir is not None:
            candidates.append(json_file_dir / 'workspace' / rel_path)

        return next((candidate for candidate in candidates if candidate.exists()), candidates[0])

    def _collect_preview_items(self, target_path: Path, project_root: Path) -> List[PreviewImageItem]:
        print(f'[SCAN] Scanning image directory for preview generation: {target_path}')
        preview_items: List[PreviewImageItem] = []
        files = sorted(target_path.iterdir(), key=lambda path: natural_sort_key(path.name))

        for file_path in files:
            if not file_path.is_file() or file_path.suffix.lower() not in PREVIEW_EXTENSIONS:
                continue

            try:
                src_rel_path = file_path.relative_to(project_root).as_posix()
            except ValueError:
                print(f'[WARN] Skipping {file_path.name}: unable to compute preview path.')
                continue

            try:
                repo_rel_path = file_path.relative_to(self.repo_root).as_posix()
            except ValueError:
                repo_rel_path = str(file_path.resolve())

            preview_items.append(PreviewImageItem(src=src_rel_path, path=repo_rel_path))

        if not preview_items:
            raise ValueError('No supported image files were found.')

        return preview_items

    def _fix_single_exif(self, file_path: Path) -> bool:
        try:
            fixed_img: Optional[Image.Image] = None
            exif_bytes: Optional[bytes] = None
            icc_profile: Optional[bytes] = None
            src_format: Optional[str] = None

            with Image.open(file_path) as img:
                exif = img.getexif()
                orientation = exif.get(ORIENTATION_TAG_ID, 1) if exif else None
                if not orientation or orientation == 1:
                    return False

                print(f'  [EXIF] Fixing {file_path.name} (orientation={orientation})')
                fixed_img = self._apply_exif_orientation(img, orientation)
                fixed_img.load()

                if exif:
                    exif[ORIENTATION_TAG_ID] = 1
                    exif_bytes = exif.tobytes()

                icc_profile = img.info.get('icc_profile')
                src_format = img.format

            if fixed_img is None:
                return False

            self._save_in_place(
                fixed_img,
                file_path,
                src_format,
                exif_bytes=exif_bytes,
                icc_profile=icc_profile,
            )
            return True
        except Exception as exc:
            print(f'  [WARN] Failed to read EXIF metadata from {file_path.name}: {exc}')
            return False

    def _get_exif_orientation(self, img: Image.Image) -> Optional[int]:
        try:
            exif = img._getexif()
            if exif:
                for tag, value in exif.items():
                    if ExifTags.TAGS.get(tag) == 'Orientation':
                        return value
        except Exception:
            return None
        return None

    def _apply_exif_orientation(self, img: Image.Image, orientation: int) -> Image.Image:
        transpose = getattr(Image, 'Transpose', Image)
        if orientation == 2:
            return img.transpose(transpose.FLIP_LEFT_RIGHT)
        if orientation == 3:
            return img.transpose(transpose.ROTATE_180)
        if orientation == 4:
            return img.transpose(transpose.FLIP_TOP_BOTTOM)
        if orientation == 5:
            return img.transpose(transpose.TRANSPOSE)
        if orientation == 6:
            return img.transpose(transpose.ROTATE_270)
        if orientation == 7:
            return img.transpose(transpose.TRANSVERSE)
        if orientation == 8:
            return img.transpose(transpose.ROTATE_90)
        return img

    def _rotate_single_image(self, file_path: Path, rotation_deg: int) -> None:
        transpose = getattr(Image, 'Transpose', Image)
        with Image.open(file_path) as img:
            counter_clockwise_angle = (360 - int(rotation_deg)) % 360
            if counter_clockwise_angle == 0:
                return

            if counter_clockwise_angle == 90:
                rotated = img.transpose(transpose.ROTATE_90)
            elif counter_clockwise_angle == 180:
                rotated = img.transpose(transpose.ROTATE_180)
            elif counter_clockwise_angle == 270:
                rotated = img.transpose(transpose.ROTATE_270)
            else:
                rotated = img.rotate(counter_clockwise_angle, expand=True)

            rotated.load()
            exif = img.getexif()
            exif_bytes: Optional[bytes] = None
            if exif:
                exif[ORIENTATION_TAG_ID] = 1
                exif_bytes = exif.tobytes()

            icc_profile = img.info.get('icc_profile')
            src_format = img.format

        self._save_in_place(
            rotated,
            file_path,
            src_format,
            exif_bytes=exif_bytes,
            icc_profile=icc_profile,
        )


def run_cli(argv: Optional[Sequence[str]] = None) -> int:
    import sys

    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print(USAGE)
        return 1

    command = args[0]
    rotator = ImageRotator()

    if command == 'gen':
        if len(args) < 2:
            print('[ERROR] Missing images directory path.')
            print(USAGE)
            return 1
        try:
            output_path = rotator.generate_html_tool(args[1])
            print(f'[OK] HTML review tool created: {output_path}')
            print(f'[LINK] Open in your browser: file:///{Path(output_path).as_posix()}')
            return 0
        except Exception as exc:
            print(f'[ERROR] Failed to generate review tool: {exc}')
            return 1

    if command == 'fix':
        if len(args) < 2:
            print('[ERROR] Missing fixes JSON path.')
            print(USAGE)
            return 1
        try:
            stats = rotator.apply_fixes(args[1])
            print(f"\n[DONE] Completed: {stats['success']} succeeded out of {stats['total']} task(s).")
            return 0
        except Exception as exc:
            print(f'[ERROR] Failed to apply fixes: {exc}')
            return 1

    if command == 'auto':
        if len(args) < 2:
            print('[ERROR] Missing images directory path.')
            print(USAGE)
            return 1
        try:
            count = rotator.auto_fix_exif(args[1])
            if count == 0:
                print('[INFO] No auto-fixable EXIF issues were found.')
            return 0
        except Exception as exc:
            print(f'[ERROR] Auto-fix failed: {exc}')
            return 1

    print(f"[ERROR] Unknown command: '{command}'")
    print(USAGE)
    return 1


def main() -> None:
    raise SystemExit(run_cli())


__all__ = [
    'AUTO_FIX_EXTENSIONS',
    'DEFAULT_OUTPUT_FILENAME',
    'HTML_TEMPLATE',
    'ImageRotator',
    'ORIENTATION_TAG_ID',
    'PREVIEW_EXTENSIONS',
    'PreviewImageItem',
    'RotationStats',
    'RotationTask',
    'USAGE',
    'discover_repository_root',
    'main',
    'natural_sort_key',
    'normalize_task_path',
    'render_html_tool',
    'run_cli',
]
