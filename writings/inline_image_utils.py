from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from utils.images import build_image_filename, process_writing_image


def save_inline_writing_image(user_id: int, uploaded) -> str:
    buffer = process_writing_image(uploaded)
    filename = build_image_filename("inline")
    path = f"writings/inline/{user_id}/{filename}"
    saved_path = default_storage.save(path, ContentFile(buffer.read()))
    return default_storage.url(saved_path)
