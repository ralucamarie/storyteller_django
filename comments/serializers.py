from collections import Counter

from rest_framework import serializers

from comments.models import ALLOWED_REACTION_EMOJIS, Comment
from stories.models import Story
from users.serializers import UserSerializer
from utils.serializers import CamelCaseSerializer


class CommentSerializer(CamelCaseSerializer):
    story_id = serializers.PrimaryKeyRelatedField(
        queryset=Story.objects.all(), write_only=True, required=False
    )
    author = UserSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    liked_by_me = serializers.SerializerMethodField()
    reactions = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "story_id",
            "author",
            "content",
            "created_at",
            "updated_at",
            "likes_count",
            "liked_by_me",
            "reactions",
            "is_mine",
        ]
        read_only_fields = ["id", "author", "created_at", "updated_at"]

    def get_likes_count(self, obj):
        if hasattr(obj, "likes_count"):
            return obj.likes_count
        return obj.likes.count()

    def get_liked_by_me(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        if hasattr(obj, "liked_by_me"):
            return obj.liked_by_me
        return obj.likes.filter(user=request.user).exists()

    def get_reactions(self, obj):
        request = self.context.get("request")
        user_id = (
            request.user.id
            if request and request.user.is_authenticated
            else None
        )

        reaction_rows = list(obj.reactions.all())
        emoji_counts = Counter(row.emoji for row in reaction_rows)
        user_emoji = next(
            (row.emoji for row in reaction_rows if user_id and row.user_id == user_id),
            None,
        )

        return [
            {
                "emoji": emoji,
                "count": count,
                "reacted_by_me": emoji == user_emoji,
            }
            for emoji, count in sorted(emoji_counts.items())
        ]

    def get_is_mine(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.author_id == request.user.id

    def validate(self, attrs):
        if self.instance is None and not attrs.get("story_id"):
            raise serializers.ValidationError({"story_id": "This field is required."})
        if "content" in attrs:
            content = attrs["content"].strip()
            if not content:
                raise serializers.ValidationError({"content": "Comment cannot be empty."})
            attrs["content"] = content
        return attrs


class CommentReactionSerializer(serializers.Serializer):
    emoji = serializers.CharField(max_length=8)

    def validate_emoji(self, value):
        if value not in ALLOWED_REACTION_EMOJIS:
            raise serializers.ValidationError("Invalid reaction emoji.")
        return value
