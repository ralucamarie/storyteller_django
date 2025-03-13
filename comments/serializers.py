from comments.models import Comment
from utils.serializers import CamelCaseSerializer

class CommentSerializer(CamelCaseSerializer):
    class Meta:
        model = Comment
        fields = '__all__'
