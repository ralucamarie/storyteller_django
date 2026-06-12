from django.db import models
from stories.models import Story
from users.models import User


def writing_image_upload_to(instance, filename):
    return f"writings/{instance.story_id}/{instance.id}/{filename}"


class WritingLayout(models.TextChoices):
    STACK = "stack", "Image above text"
    IMAGE_LEFT = "image_left", "Image left, text wraps (max 40%)"
    IMAGE_RIGHT = "image_right", "Image right, text wraps (max 40%)"


class Writing(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name="writings")
    created = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="writings")  # ✅ Link to User
    text = models.TextField()
    layout = models.CharField(
        max_length=20,
        choices=WritingLayout.choices,
        default=WritingLayout.STACK,
    )
    image = models.ImageField(upload_to=writing_image_upload_to, blank=True, null=True)
    image_updated = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["created", "id"]

    def __str__(self):
        return f"{self.author.author_name} - {self.story.title[:30]}"
