from django.db import models
from stories.models import Story
from users.models import User


def writing_image_upload_to(instance, filename):
    return f"writings/{instance.story_id}/{instance.id}/{filename}"


class WritingLayout(models.TextChoices):
    STACK = "stack", "Image above text"
    IMAGE_LEFT_50 = "image_left_50", "Image left 50%, text right 50%"
    IMAGE_LEFT_30 = "image_left_30", "Image left 30%, text right 70%"
    TEXT_LEFT_70 = "text_left_70", "Text left 70%, image right 30%"


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
