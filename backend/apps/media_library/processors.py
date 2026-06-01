"""
Image processing pipeline — thumbnails, WebP conversion, optimization.

Processing presets:
- thumbnail: 150x150 (cover, for lists)
- medium: 768x (responsive)
- large: 1920x (full-width hero)

All variants also generate WebP versions for modern browsers.
"""

import io
import os
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings


@dataclass
class ProcessingPreset:
    name: str
    max_width: int
    max_height: int | None
    suffix: str
    quality: int = 85


PRESETS = [
    ProcessingPreset("thumbnail", 150, 150, "_thumb", 80),
    ProcessingPreset("medium", 768, None, "_medium", 85),
    ProcessingPreset("large", 1920, None, "_large", 85),
]


class ImageProcessor:
    """
    Process uploaded images — generate thumbnails, WebP variants.

    Usage:
        processor = ImageProcessor(original_path)
        results = processor.process()
        # results = [{"name": "thumbnail", "path": "...", "url": "...", "width": 150, "height": 150}, ...]
    """

    def __init__(self, original_file_path: str):
        self.original_path = Path(original_file_path)
        self.original_dir = self.original_path.parent
        self.original_stem = self.original_path.stem  # filename without extension
        self.results: list[dict] = []

    def process(self) -> list[dict]:
        """Run the full processing pipeline. Returns list of generated variants."""
        try:
            from PIL import Image
        except ImportError:
            return []

        try:
            img = Image.open(self.original_path)
        except Exception:
            return []

        # Convert RGBA/CMYK to RGB for JPEG/WebP compatibility
        original_mode = img.mode
        if img.mode in ("RGBA", "P", "CMYK"):
            img = img.convert("RGB")

        for preset in PRESETS:
            variant = self._generate_variant(img.copy(), preset)
            if variant:
                self.results.append(variant)

            # Also generate WebP version
            webp_variant = self._generate_webp(img.copy(), preset)
            if webp_variant:
                self.results.append(webp_variant)

        img.close()
        return self.results

    def _generate_variant(self, img, preset: ProcessingPreset) -> dict | None:
        """Resize and save a single variant."""
        width, height = self._calculate_size(img.size, preset.max_width, preset.max_height)

        try:
            resized = img.resize((width, height), self._get_filter())
        except Exception:
            return None

        filename = f"{self.original_stem}{preset.suffix}.jpg"
        filepath = self.original_dir / filename

        resized.save(filepath, "JPEG", quality=preset.quality, optimize=True)
        resized.close()

        return {
            "name": preset.name,
            "path": str(filepath),
            "filename": filename,
            "format": "jpeg",
            "width": width,
            "height": height,
            "file_size": filepath.stat().st_size,
        }

    def _generate_webp(self, img, preset: ProcessingPreset) -> dict | None:
        """Generate WebP version of a variant."""
        width, height = self._calculate_size(img.size, preset.max_width, preset.max_height)

        try:
            resized = img.resize((width, height), self._get_filter())
        except Exception:
            return None

        filename = f"{self.original_stem}{preset.suffix}.webp"
        filepath = self.original_dir / filename

        try:
            resized.save(filepath, "WEBP", quality=preset.quality, method=6)
        except Exception:
            # WebP may not be supported; skip
            resized.close()
            return None

        resized.close()

        return {
            "name": f"{preset.name}_webp",
            "path": str(filepath),
            "filename": filename,
            "format": "webp",
            "width": width,
            "height": height,
            "file_size": filepath.stat().st_size,
        }

    @staticmethod
    def _calculate_size(original: tuple[int, int], max_w: int, max_h: int | None) -> tuple[int, int]:
        """Calculate proportional resize dimensions."""
        w, h = original
        if max_h is not None:
            # Crop to cover for fixed dimensions (thumbnail)
            ratio = max(max_w / w, max_h / h)
            new_w = int(w * ratio)
            new_h = int(h * ratio)
            return new_w, new_h
        # Width-constrained, proportional height
        if w <= max_w:
            return w, h
        ratio = max_w / w
        return max_w, int(h * ratio)

    @staticmethod
    def _get_filter():
        """Best downscaling filter based on Pillow version."""
        try:
            from PIL import Image
            return Image.Resampling.LANCZOS
        except AttributeError:
            return 1  # PIL.Image.LANCZOS fallback


def process_uploaded_image(file_path: str) -> list[dict]:
    """Convenience function — process an image and return variant metadata."""
    processor = ImageProcessor(file_path)
    return processor.process()


def generate_thumbnail(file_path: str, size: tuple[int, int] = (150, 150)) -> str | None:
    """Quick single thumbnail generation. Returns path or None."""
    try:
        from PIL import Image
        img = Image.open(file_path)
        img = img.convert("RGB")
        img.thumbnail(size, Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else 1)

        thumb_path = Path(file_path).parent / f"{Path(file_path).stem}_thumb.jpg"
        img.save(thumb_path, "JPEG", quality=80, optimize=True)
        img.close()
        return str(thumb_path)
    except Exception:
        return None
