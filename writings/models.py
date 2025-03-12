from django.db import models
from stories.models import Story

class Writing(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name="writings")
    created = models.DateTimeField(auto_now_add=True)
    author_name = models.CharField(max_length=255)
    text = models.TextField()

    def __str__(self):
        return f"{self.author_name} - {self.story.title[:30]}"
