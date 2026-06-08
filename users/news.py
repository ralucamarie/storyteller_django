from datetime import timedelta

from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from comments.models import Comment
from stories.models import Story
from users.models import FavoriteAuthor
from writings.models import Writing

NEWS_LIMIT = 50
NEWS_LOOKBACK_DAYS = 60


def _event(
    event_id,
    event_type,
    occurred_at,
    story,
    actor,
    preview="",
):
    return {
        "id": event_id,
        "type": event_type,
        "occurredAt": occurred_at.isoformat() if occurred_at else None,
        "storyId": story.id,
        "storyTitle": story.title,
        "actorId": actor.id if actor else None,
        "actorName": actor.author_name if actor else None,
        "preview": (preview or "")[:160],
    }


class NewsFeedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        since = timezone.now() - timedelta(days=NEWS_LOOKBACK_DAYS)

        my_story_ids = set(
            Story.objects.filter(author=user).values_list("id", flat=True)
        )
        followed_story_ids = set(
            Story.objects.filter(comments__author=user)
            .exclude(author=user)
            .values_list("id", flat=True)
        )
        favorite_author_ids = set(
            FavoriteAuthor.objects.filter(user=user).values_list("author_id", flat=True)
        )

        events = []

        if my_story_ids:
            for writing in (
                Writing.objects.filter(story_id__in=my_story_ids, created__gte=since)
                .exclude(author=user)
                .select_related("author", "story")
                .order_by("-created")[:NEWS_LIMIT]
            ):
                events.append(
                    _event(
                        f"writing-my-{writing.id}",
                        "contribution_on_my_story",
                        writing.created,
                        writing.story,
                        writing.author,
                        writing.text,
                    )
                )

            for comment in (
                Comment.objects.filter(story_id__in=my_story_ids, created_at__gte=since)
                .exclude(author=user)
                .select_related("author", "story_id")
                .order_by("-created_at")[:NEWS_LIMIT]
            ):
                story = comment.story_id
                events.append(
                    _event(
                        f"comment-my-{comment.id}",
                        "comment_on_my_story",
                        comment.created_at,
                        story,
                        comment.author,
                        comment.content,
                    )
                )

        if followed_story_ids:
            for writing in (
                Writing.objects.filter(story_id__in=followed_story_ids, created__gte=since)
                .exclude(author=user)
                .select_related("author", "story")
                .order_by("-created")[:NEWS_LIMIT]
            ):
                events.append(
                    _event(
                        f"writing-followed-{writing.id}",
                        "contribution_on_followed_story",
                        writing.created,
                        writing.story,
                        writing.author,
                        writing.text,
                    )
                )

            for comment in (
                Comment.objects.filter(
                    story_id__in=followed_story_ids, created_at__gte=since
                )
                .exclude(author=user)
                .select_related("author", "story_id")
                .order_by("-created_at")[:NEWS_LIMIT]
            ):
                story = comment.story_id
                events.append(
                    _event(
                        f"comment-followed-{comment.id}",
                        "comment_on_followed_story",
                        comment.created_at,
                        story,
                        comment.author,
                        comment.content,
                    )
                )

        if favorite_author_ids:
            for story in (
                Story.objects.filter(
                    author_id__in=favorite_author_ids, created_at__gte=since
                )
                .exclude(author=user)
                .select_related("author")
                .prefetch_related("writings")
                .order_by("-created_at")[:NEWS_LIMIT]
            ):
                first_writing = story.writings.order_by("created", "id").first()
                preview = first_writing.text if first_writing else ""
                events.append(
                    _event(
                        f"story-fav-{story.id}",
                        "favorite_author_new_story",
                        story.created_at,
                        story,
                        story.author,
                        preview,
                    )
                )

        events.sort(
            key=lambda item: item["occurredAt"] or "",
            reverse=True,
        )
        events = events[:NEWS_LIMIT]

        return Response({"count": len(events), "items": events})
