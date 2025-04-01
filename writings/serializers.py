from rest_framework import serializers

from users.serializers import UserSerializer
from .models import Writing
from utils.serializers import CamelCaseSerializer


class WritingSerializer(CamelCaseSerializer):
    author = UserSerializer(read_only=True)  # ✅ Returns full user object

    class Meta:
        model = Writing
        fields = ["id", "story", "created", "author", "text"]
