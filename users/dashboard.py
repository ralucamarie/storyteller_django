from collections import defaultdict
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from comments.models import Comment
from stories.models import FavoriteStory, Story
from users.models import FavoriteAuthor
from users.serializers import UserSerializer
from writings.models import Writing

POINTS_STORY = 50
POINTS_CONTRIBUTION = 20
POINTS_COMMENT = 10
LEVEL_STEP = 100


def _story_summary(story):
    first_writing = story.writings.order_by("created").first()
    return {
        "id": story.id,
        "title": story.title,
        "created_at": story.created_at,
        "author_name": story.author.author_name,
        "intro": first_writing.text[:160] if first_writing else "",
        "writings_count": story.writings.count(),
        "comments_count": story.comments.count(),
    }


def _build_activity(user, days):
    start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(
        days=days - 1
    )
    buckets = {
        (start + timedelta(days=i)).date().isoformat(): 0 for i in range(days)
    }

    for created in Story.objects.filter(author=user, created_at__gte=start).values_list(
        "created_at", flat=True
    ):
        buckets[created.date().isoformat()] += 1

    for created in Writing.objects.filter(author=user, created__gte=start).values_list(
        "created", flat=True
    ):
        buckets[created.date().isoformat()] += 1

    for created in Comment.objects.filter(author=user, created_at__gte=start).values_list(
        "created_at", flat=True
    ):
        buckets[created.date().isoformat()] += 1

    return [{"label": key, "count": buckets[key]} for key in sorted(buckets.keys())]


def _build_weekly_activity(user, weeks):
    start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(
        weeks=weeks - 1
    )
    start -= timedelta(days=start.weekday())
    buckets = defaultdict(int)
    week_labels = []

    for i in range(weeks):
        week_start = start + timedelta(weeks=i)
        label = week_start.strftime("W%U %d %b")
        week_labels.append(label)
        buckets[label] = 0

    def week_label_for(dt):
        week_start = dt - timedelta(days=dt.weekday())
        return week_start.strftime("W%U %d %b")

    for created in Story.objects.filter(author=user, created_at__gte=start).values_list(
        "created_at", flat=True
    ):
        buckets[week_label_for(created)] += 1

    for created in Writing.objects.filter(author=user, created__gte=start).values_list(
        "created", flat=True
    ):
        buckets[week_label_for(created)] += 1

    for created in Comment.objects.filter(author=user, created_at__gte=start).values_list(
        "created_at", flat=True
    ):
        buckets[week_label_for(created)] += 1

    return [{"label": label, "count": buckets[label]} for label in week_labels]


def _gamification(stories_count, contributions_count, comments_count):
    points = (
        stories_count * POINTS_STORY
        + contributions_count * POINTS_CONTRIBUTION
        + comments_count * POINTS_COMMENT
    )
    level = max(1, points // LEVEL_STEP + 1)
    progress = points % LEVEL_STEP
    badges = []
    if stories_count >= 1:
        badges.append({"id": "storyteller", "label": "Storyteller", "icon": "pi-book"})
    if stories_count >= 5:
        badges.append({"id": "author", "label": "Pro Author", "icon": "pi-star"})
    if contributions_count >= 3:
        badges.append({"id": "contributor", "label": "Co-Writer", "icon": "pi-pencil"})
    if comments_count >= 5:
        badges.append({"id": "critic", "label": "Active Reader", "icon": "pi-comments"})
    if points >= 200:
        badges.append({"id": "legend", "label": "Story Legend", "icon": "pi-bolt"})

    return {
        "points": points,
        "level": level,
        "level_progress": progress,
        "level_max": LEVEL_STEP,
        "badges": badges,
    }


class ProfileDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        own_stories_qs = Story.objects.filter(author=user).prefetch_related("writings", "comments")
        contributions_qs = (
            Writing.objects.filter(author=user)
            .exclude(story__author=user)
            .select_related("story", "story__author")
            .order_by("-created")[:6]
        )
        commented_stories_qs = (
            Story.objects.filter(comments__author=user)
            .distinct()
            .prefetch_related("writings", "comments")
            .order_by("-created_at")[:6]
        )
        favorites_qs = (
            FavoriteStory.objects.filter(user=user)
            .select_related("story", "story__author")
            .prefetch_related("story__writings", "story__comments")
            .order_by("-created_at")[:6]
        )

        stories_count = own_stories_qs.count()
        contributions_count = Writing.objects.filter(author=user).exclude(
            story__author=user
        ).count()
        comments_count = Comment.objects.filter(author=user).count()

        contributions = [
            {
                "id": writing.id,
                "text": writing.text[:160],
                "created": writing.created,
                "story": _story_summary(writing.story),
            }
            for writing in contributions_qs
        ]

        return Response(
            {
                "user": UserSerializer(user, context={"request": request}).data,
                "stats": {
                    "stories_written": stories_count,
                    "contributions": contributions_count,
                    "comments": comments_count,
                },
                "gamification": _gamification(
                    stories_count, contributions_count, comments_count
                ),
                "activity": {
                    "daily": _build_activity(user, 7),
                    "weekly": _build_weekly_activity(user, 6),
                },
                "own_stories": [_story_summary(story) for story in own_stories_qs[:6]],
                "contributions": contributions,
                "commented_stories": [
                    _story_summary(story) for story in commented_stories_qs
                ],
                "favorite_stories": [
                    _story_summary(favorite.story) for favorite in favorites_qs
                ],
            }
        )


class FavoriteAuthorListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        favorites = FavoriteAuthor.objects.filter(user=request.user).select_related("author")
        authors = [
            {"id": favorite.author.id, "author_name": favorite.author.author_name}
            for favorite in favorites
        ]
        return Response(
            {
                "author_ids": [author["id"] for author in authors],
                "authors": authors,
            }
        )


class FavoriteAuthorToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, author_id):
        if request.user.id == author_id:
            return Response(
                {"detail": "You cannot favorite yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        author = get_object_or_404(get_user_model(), pk=author_id)
        FavoriteAuthor.objects.get_or_create(user=request.user, author=author)
        return Response({"detail": "Author added to favorites."}, status=status.HTTP_201_CREATED)

    def delete(self, request, author_id):
        FavoriteAuthor.objects.filter(user=request.user, author_id=author_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteStoryListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        story_ids = list(
            FavoriteStory.objects.filter(user=request.user).values_list("story_id", flat=True)
        )
        return Response({"story_ids": story_ids})


class FavoriteStoryToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, story_id):
        story = get_object_or_404(Story, pk=story_id)
        FavoriteStory.objects.get_or_create(user=request.user, story=story)
        return Response({"detail": "Story added to favorites."}, status=status.HTTP_201_CREATED)

    def delete(self, request, story_id):
        FavoriteStory.objects.filter(user=request.user, story_id=story_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
