from django.db import models

class Comment(models.Model):
    story = models.ForeignKey("stories.Story", related_name="comments", on_delete=models.CASCADE)  # ✅ String reference avoids import issues
    author_name = models.CharField(max_length=100)
    content = models.TextField()

    def __str__(self):
        return f'Comment by {self.author_name} on {self.story.title}'  # ✅ Access story.title directly
