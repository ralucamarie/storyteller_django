from django.conf import settings
from django.db import models
from django.utils import timezone

ALLOWED_REACTION_EMOJIS = ("👍", "❤️", "😂", "😮", "😢", "🔥")


class Comment(models.Model):
    story_id = models.ForeignKey(
        "stories.Story", related_name="comments", on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="comments", on_delete=models.CASCADE
    )
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Comment by {self.author.author_name} on {self.story_id.title}"


class CommentLike(models.Model):
    comment = models.ForeignKey(Comment, related_name="likes", on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="comment_likes", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("comment", "user")


class CommentReaction(models.Model):
    comment = models.ForeignKey(
        Comment, related_name="reactions", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="comment_reactions",
        on_delete=models.CASCADE,
    )
    emoji = models.CharField(max_length=8)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("comment", "user")
