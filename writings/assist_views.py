from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from stories.models import Story

from .gemini_assist import (
    WritingAssistError,
    generate_new_story_assist,
    generate_writing_assist,
)


class WritingAssistView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        story_id = request.data.get("story_id") or request.data.get("storyId")
        mode = (request.data.get("mode") or "suggestion").strip().lower()
        lang = (request.data.get("lang") or "ro").strip().lower()
        draft_text = request.data.get("draft_text") or request.data.get("draftText") or ""

        title = (request.data.get("title") or "").strip()
        categories = request.data.get("categories") or request.data.get("category_names") or []

        if mode not in ("suggestion", "game"):
            return Response(
                {"detail": "mode must be 'suggestion' or 'game'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if lang not in ("ro", "en"):
            lang = "ro"

        try:
            if story_id:
                try:
                    story = (
                        Story.objects.prefetch_related("categories")
                        .prefetch_related("writings__author")
                        .get(pk=story_id)
                    )
                except Story.DoesNotExist:
                    return Response(
                        {"detail": "Story not found."},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                writings = story.writings.all()
                result = generate_writing_assist(
                    mode=mode,
                    lang=lang,
                    story=story,
                    writings=writings,
                    draft_text=str(draft_text),
                )
            else:
                if not isinstance(categories, list):
                    categories = []
                result = generate_new_story_assist(
                    mode=mode,
                    lang=lang,
                    title=title,
                    categories=categories,
                    draft_text=str(draft_text),
                )
        except WritingAssistError as exc:
            return Response(
                {"detail": exc.message},
                status=exc.status_code,
            )

        return Response(result, status=status.HTTP_200_OK)
