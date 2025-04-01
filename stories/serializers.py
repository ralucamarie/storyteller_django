from categories.models import Category
from categories.serializers import CategorySerializer
from comments.serializers import CommentSerializer
from users.serializers import UserSerializer
from writings.models import Writing
from writings.serializers import WritingSerializer
from utils.serializers import CamelCaseSerializer
from stories.models import Story
from rest_framework import serializers

class StorySerializer(CamelCaseSerializer):
    categories = serializers.ListField(child=serializers.CharField(),
                                       write_only=True)  # Accept category names as a list
    category_objects = CategorySerializer(many=True, read_only=True,
                                          source="categories")  # Return full category objects
    writings = WritingSerializer(many=True, read_only=True)
    author = serializers.SerializerMethodField(read_only=True)  # Read-only author field
    content = serializers.CharField(write_only=True)
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Story
        fields = '__all__'

    def get_author(self, obj):
        """Returns author's name in response."""
        return obj.author.author_name if obj.author else None

    def create(self, validated_data):
        """Create a story with the authenticated user as the author and link categories."""
        categories_data = validated_data.pop("categories", [])  # Extract category names
        content = validated_data.pop("content", None)  # ✅ Extract content for Writing
        request = self.context.get("request")  # Get the request context
        user = request.user if request else None  # Get authenticated user
        print(f"Validated data received in create: {validated_data}")

        if not user or not user.is_authenticated:
            raise serializers.ValidationError({"error": "User must be authenticated to create a story."})

        # Create the story and assign the authenticated user as author
        story = Story.objects.create(author=user, **validated_data)

        # Link categories
        category_instances = []
        for category_name in categories_data:
            category, _ = Category.objects.get_or_create(name=category_name)
            category_instances.append(category)

        story.categories.set(category_instances)  # Assign categories to the story
        print(f"content: {content}")  # Debugging info

        if content:
            writing = Writing.objects.create(
                story=story,
                author=user,  # ✅ Use ForeignKey to User
                text=content,
            )
            print(f"Writing created: {writing}")  # Debugging info

        return story

