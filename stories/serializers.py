from categories.serializers import CategorySerializer
from comments.serializers import CommentSerializer
from users.serializers import UserSerializer
from writings.serializers import WritingSerializer
from utils.serializers import CamelCaseSerializer
from stories.models import Story

class StorySerializer(CamelCaseSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    writings = WritingSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)

    class Meta:
        model = Story
        fields = '__all__'

