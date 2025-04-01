from rest_framework import viewsets
from .models import Comment
from .serializers import CommentSerializer

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def get_queryset(self):
        queryset = Comment.objects.all()  # Default to all comments

        story_id = self.request.query_params.get('story')  # Example: /comments/?story=2
        if story_id:
            queryset = queryset.filter(story_id=story_id)

        user_id = self.request.query_params.get('user_id')  # Example: /comments/?user_id=2
        if user_id:
            queryset = queryset.filter(author__id=user_id)

        return queryset  # Ensures queryset exists for all request types
