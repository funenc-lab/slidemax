"""Finalize step handlers for SlideMax."""

from .crop_images import run as crop_images
from .embed_icons import run as embed_icons
from .embed_images import run as embed_images
from .fix_aspect import run as fix_aspect
from .fix_rounded import run as fix_rounded
from .flatten_text import run as flatten_text

__all__ = [
    "crop_images",
    "embed_icons",
    "embed_images",
    "fix_aspect",
    "fix_rounded",
    "flatten_text",
]
