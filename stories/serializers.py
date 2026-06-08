from categories.models import Category
from categories.serializers import CategorySerializer
from comments.serializers import CommentSerializer
from users.serializers import UserSerializer
from writings.image_utils import save_writing_image
from writings.models import Writing, WritingLayout
from writings.serializers import WritingSerializer
from utils.serializers import CamelCaseSerializer
from stories.models import Story
from rest_framework import serializers

class StorySerializer(CamelCaseSerializer):
    categories = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False,
        default=list,
    )
    category_objects = CategorySerializer(
        many=True, read_only=True, source="categories"
    )
    writings = WritingSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    content = serializers.CharField(write_only=True, required=False, allow_blank=False)
    layout = serializers.ChoiceField(
        choices=WritingLayout.choices,
        write_only=True,
        required=False,
        default=WritingLayout.STACK,
    )
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Story
        fields = "__all__"
        read_only_fields = ("id", "created_at", "author")

    def create(self, validated_data):
        categories_data = validated_data.pop("categories", [])
        content = validated_data.pop("content", None)
        layout = validated_data.pop("layout", WritingLayout.STACK)
        request = self.context.get("request")
        user = request.user if request else None

        if not user or not user.is_authenticated:
            raise serializers.ValidationError(
                {"error": "User must be authenticated to create a story."}
            )

        if not content or not str(content).strip():
            raise serializers.ValidationError(
                {"content": "First writing is required."}
            )

        categories_data = [
            name.strip()
            for name in categories_data
            if name and str(name).strip()
        ]
        if not categories_data:
            raise serializers.ValidationError(
                {"categories": "At least one category is required."}
            )

        image_file = request.FILES.get("image") if request else None

        story = Story.objects.create(author=user, **validated_data)

        category_instances = []
        for category_name in categories_data:
            category, _ = Category.objects.get_or_create(name=category_name)
            category_instances.append(category)

        story.categories.set(category_instances)

        writing = Writing.objects.create(
            story=story,
            author=user,
            text=content.strip(),
            layout=layout,
        )
        if image_file:
            save_writing_image(writing, image_file)

        return story
