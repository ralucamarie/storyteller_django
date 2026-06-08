from django.db.models import Count, Exists, OuterRef
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import Comment, CommentLike, CommentReaction
from .serializers import CommentReactionSerializer, CommentSerializer


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        queryset = (
            Comment.objects.select_related("author")
            .prefetch_related("likes", "reactions")
            .annotate(likes_count=Count("likes", distinct=True))
        )

        if user.is_authenticated:
            queryset = queryset.annotate(
                liked_by_me=Exists(
                    CommentLike.objects.filter(
                        comment_id=OuterRef("pk"), user_id=user.id
                    )
                )
            )
        else:
            queryset = queryset.annotate(liked_by_me=Exists(CommentLike.objects.none()))

        story_id = self.request.query_params.get("story")
        if story_id:
            queryset = queryset.filter(story_id=story_id)

        user_id = self.request.query_params.get("user_id")
        if user_id:
            queryset = queryset.filter(author__id=user_id)

        return queryset.order_by("-created_at")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentication required.")
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        if serializer.instance.author != self.request.user:
            raise PermissionDenied("You can only edit your own comments.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied("You can only delete your own comments.")
        instance.delete()

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="like",
    )
    def like(self, request, pk=None):
        comment = self.get_object()
        if comment.author_id == request.user.id:
            return Response(
                {"detail": "You cannot like your own comment."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        like = CommentLike.objects.filter(comment=comment, user=request.user).first()
        if like:
            like.delete()
        else:
            CommentLike.objects.create(comment=comment, user=request.user)

        comment = self.get_queryset().get(pk=comment.pk)
        return Response(self.get_serializer(comment).data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="react",
    )
    def react(self, request, pk=None):
        comment = self.get_object()
        if comment.author_id == request.user.id:
            return Response(
                {"detail": "You cannot react to your own comment."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payload = CommentReactionSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        emoji = payload.validated_data["emoji"]

        existing = CommentReaction.objects.filter(
            comment=comment, user=request.user
        ).first()
        if existing and existing.emoji == emoji:
            existing.delete()
        elif existing:
            existing.emoji = emoji
            existing.save()
        else:
            CommentReaction.objects.create(
                comment=comment, user=request.user, emoji=emoji
            )

        comment = self.get_queryset().get(pk=comment.pk)
        return Response(self.get_serializer(comment).data)
