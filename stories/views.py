import time

from django.core.cache import cache
from django.db.models import Prefetch
from django.shortcuts import redirect
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from writings.models import Writing

from .models import Story
from .serializers import StorySerializer

TYPING_TTL_SECONDS = 5
STORY_TYPING_PREFIX = "story_typing_"


def home(request):
    return redirect("/api/stories/")


def _get_story_typers(story_id):
    return cache.get(f"{STORY_TYPING_PREFIX}{story_id}", {})


def _save_story_typers(story_id, typers):
    cache.set(f"{STORY_TYPING_PREFIX}{story_id}", typers, TYPING_TTL_SECONDS + 5)


def _get_active_typers(story_id, exclude_user_id=None):
    typers = _get_story_typers(story_id)
    now = time.time()
    active = []
    cleaned = {}

    for user_id, data in typers.items():
        if now - data["updated_at"] < TYPING_TTL_SECONDS:
            cleaned[user_id] = data
            if exclude_user_id is None or str(user_id) != str(exclude_user_id):
                active.append({"author_name": data["author_name"]})

    if cleaned != typers:
        _save_story_typers(story_id, cleaned)

    return active


class StoryViewSet(viewsets.ModelViewSet):
    queryset = (
        Story.objects.select_related("author")
        .prefetch_related(
            "categories",
            Prefetch(
                "writings",
                queryset=Writing.objects.select_related("author").order_by("created", "id"),
            ),
            "comments__author",
            "comments__likes",
            "comments__reactions",
        )
        .order_by("-created_at")
    )
    serializer_class = StorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied("You can only delete your own stories.")
        instance.delete()

    @action(detail=True, methods=["get", "post"], url_path="typing")
    def typing(self, request, pk=None):
        story = self.get_object()

        if request.method == "POST":
            if not request.user.is_authenticated:
                return Response({"detail": "Authentication required."}, status=401)

            typers = _get_story_typers(story.id)
            typers[str(request.user.id)] = {
                "author_name": request.user.author_name,
                "updated_at": time.time(),
            }
            _save_story_typers(story.id, typers)

        exclude_user_id = request.user.id if request.user.is_authenticated else None
        return Response({"typers": _get_active_typers(story.id, exclude_user_id)})
