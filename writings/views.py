from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import Writing
from .serializers import WritingImageSerializer, WritingSerializer


class WritingViewSet(viewsets.ModelViewSet):
    queryset = Writing.objects.select_related("author", "story").all()
    serializer_class = WritingSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        story_id = self.request.query_params.get("story")
        if story_id:
            queryset = queryset.filter(story_id=story_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=["post", "delete"],
        url_path="image",
        permission_classes=[IsAuthenticated],
        parser_classes=[MultiPartParser, FormParser],
    )
    def image(self, request, pk=None):
        writing = self.get_object()

        if writing.author_id != request.user.id:
            raise PermissionDenied("You can only manage images on your own writings.")

        if request.method == "DELETE":
            if writing.image:
                writing.image.delete(save=False)
                writing.image = None
                writing.image_updated = None
                writing.save(update_fields=["image", "image_updated"])
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = WritingImageSerializer(
            writing,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        writing = serializer.save()
        return Response(
            WritingSerializer(writing, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )
