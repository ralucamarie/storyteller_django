from django.core.files.base import ContentFile
from django.utils import timezone

from utils.images import build_image_filename, process_writing_image


def save_writing_image(writing, uploaded):
    buffer = process_writing_image(uploaded)
    filename = build_image_filename("writing")

    if writing.image:
        writing.image.delete(save=False)

    writing.image.save(filename, ContentFile(buffer.read()), save=False)
    writing.image_updated = timezone.now()
    writing.save(update_fields=["image", "image_updated"])
    return writing
