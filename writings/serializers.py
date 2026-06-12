from rest_framework import serializers

from stories.models import Story
from users.serializers import UserSerializer
from utils.media_urls import build_media_url
from .html_utils import is_writing_html_empty, looks_like_html, plain_text_to_html, sanitize_writing_html
from .image_utils import save_writing_image
from .models import Writing
from utils.serializers import CamelCaseSerializer


class WritingSerializer(CamelCaseSerializer):
    author = UserSerializer(read_only=True)
    story = serializers.PrimaryKeyRelatedField(queryset=Story.objects.all())
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Writing
        fields = [
            "id",
            "story",
            "created",
            "author",
            "text",
            "layout",
            "image_url",
            "image_updated",
        ]
        read_only_fields = ["id", "created", "author", "image_url", "image_updated"]

    def validate_text(self, value):
        raw = value or ""
        if not looks_like_html(raw):
            raw = plain_text_to_html(raw)
        cleaned = sanitize_writing_html(raw)
        if is_writing_html_empty(cleaned):
            raise serializers.ValidationError("Writing content is required.")
        return cleaned

    def get_image_url(self, obj):
        return build_media_url(obj.image, self.context.get("request"))


class WritingImageSerializer(serializers.Serializer):
    image = serializers.ImageField()

    def update(self, instance, validated_data):
        return save_writing_image(instance, validated_data["image"])


class WritingInlineImageSerializer(serializers.Serializer):
    image = serializers.ImageField()
