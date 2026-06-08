from rest_framework import serializers

from stories.models import Story
from users.serializers import UserSerializer
from utils.media_urls import build_media_url
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

    def get_image_url(self, obj):
        return build_media_url(obj.image, self.context.get("request"))


class WritingImageSerializer(serializers.Serializer):
    image = serializers.ImageField()

    def update(self, instance, validated_data):
        return save_writing_image(instance, validated_data["image"])
