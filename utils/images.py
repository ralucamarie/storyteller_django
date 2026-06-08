import io
import uuid

from django.core.exceptions import ValidationError
from PIL import Image

ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

MAX_AVATAR_BYTES = 2 * 1024 * 1024
MAX_WRITING_IMAGE_BYTES = 8 * 1024 * 1024
AVATAR_SIZE = (256, 256)
WRITING_IMAGE_MAX_WIDTH = 1920


def validate_uploaded_image(uploaded_file, *, max_bytes: int) -> None:
    content_type = getattr(uploaded_file, "content_type", "") or ""
    if content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise ValidationError("Only JPG, PNG, and WebP images are allowed.")

    size = getattr(uploaded_file, "size", 0) or 0
    if size > max_bytes:
        raise ValidationError(f"Image must be {max_bytes // (1024 * 1024)} MB or smaller.")


def _save_image_as_webp(image: Image.Image, *, max_width: int | None = None) -> io.BytesIO:
    processed = image.convert("RGB")

    if max_width and processed.width > max_width:
        ratio = max_width / processed.width
        new_height = max(1, int(processed.height * ratio))
        processed = processed.resize((max_width, new_height), Image.Resampling.LANCZOS)

    buffer = io.BytesIO()
    processed.save(buffer, format="WEBP", quality=85, method=6)
    buffer.seek(0)
    return buffer


def process_avatar(uploaded_file) -> io.BytesIO:
    validate_uploaded_image(uploaded_file, max_bytes=MAX_AVATAR_BYTES)
    image = Image.open(uploaded_file)
    image = ImageOps_exif_transpose(image)
    image.thumbnail(AVATAR_SIZE, Image.Resampling.LANCZOS)
    return _save_image_as_webp(image)


def process_writing_image(uploaded_file) -> io.BytesIO:
    validate_uploaded_image(uploaded_file, max_bytes=MAX_WRITING_IMAGE_BYTES)
    image = Image.open(uploaded_file)
    image = ImageOps_exif_transpose(image)
    return _save_image_as_webp(image, max_width=WRITING_IMAGE_MAX_WIDTH)


def ImageOps_exif_transpose(image: Image.Image) -> Image.Image:
    try:
        from PIL import ImageOps

        return ImageOps.exif_transpose(image)
    except Exception:
        return image


def build_image_filename(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}.webp"
