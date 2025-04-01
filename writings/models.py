from django.db import models
from stories.models import Story
from users.models import User


class Writing(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name="writings")
    created = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="writings")  # ✅ Link to User
    text = models.TextField()

    def __str__(self):
        return f"{self.author.author_name} - {self.story.title[:30]}"
