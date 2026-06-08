"""Shared helpers for the test suite.

Keeping object creation in one place keeps the individual test modules short
and focused on behaviour rather than boilerplate.
"""

import io

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

User = get_user_model()

DEFAULT_PASSWORD = "StrongPass123"


def create_user(
    *,
    email="author@example.com",
    author_name="author",
    password=DEFAULT_PASSWORD,
    name="Test",
    surname="User",
    **extra,
):
    """Create and return a persisted user via the custom manager."""
    return User.objects.create_user(
        email=email,
        password=password,
        author_name=author_name,
        name=name,
        surname=surname,
        **extra,
    )


def auth_client(user):
    """Return an APIClient already authenticated as ``user``."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def make_image_file(name="test.png", *, size=(16, 16), image_format="PNG"):
    """Return a real (tiny) in-memory image as an upload, including content type."""
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", size, color=(120, 80, 200)).save(buffer, format=image_format)
    buffer.seek(0)
    content_type = f"image/{image_format.lower()}"
    if image_format.upper() == "JPEG":
        content_type = "image/jpeg"
    return SimpleUploadedFile(name, buffer.read(), content_type=content_type)
