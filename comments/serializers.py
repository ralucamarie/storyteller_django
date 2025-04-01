from comments.models import Comment
from users.models import User
from utils.serializers import CamelCaseSerializer
from rest_framework import serializers
from stories.models import Story

class CommentSerializer(CamelCaseSerializer):
    story_id = serializers.PrimaryKeyRelatedField(
        queryset=Story.objects.all(), write_only=True, required=True
    )
    author = serializers.SerializerMethodField()  # Full author details in response
    author_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, required=True
    )
    content = serializers.CharField(required=True)

    class Meta:
        model = Comment
        fields = ['id', 'story_id', 'author', 'author_id', 'content']

    def get_author(self, obj):
        """Returns the full author object in response."""
        from users.serializers import UserSerializer  # Avoid circular import
        return UserSerializer(obj.author).data

    def create(self, validated_data):
        """Convert story_id and author_id into actual model instances."""
        story_id = validated_data.pop('story_id')  # Convert story_id to Story instance
        author = validated_data.pop('author_id')  # Convert author_id to User instance

        comment = Comment.objects.create(story_id=story_id, author=author, **validated_data)
        return comment