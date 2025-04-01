from django.db import models
from django.conf import settings

class Comment(models.Model):
    story_id = models.ForeignKey("stories.Story", related_name="comments", on_delete=models.CASCADE)  # ✅ String reference avoids import issues
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="comments", on_delete=models.CASCADE)  # 🔹 Connects to User model
    content = models.TextField()

    def __str__(self):
        return f'Comment by {self.author.username} on {self.story.title}'  # Use author's username
