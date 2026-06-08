from django.contrib.auth import get_user_model
from django.db import models
from categories.models import Category  # Import the Category model from the 'category' app

User = get_user_model()

def get_default_author():
   # Fallback author id. The app always sets the author explicitly via the
   # serializer, so this default is effectively unused at runtime. It must not
   # run any DB query: as a callable default it is also evaluated while
   # migrations run, and querying the (possibly half-migrated) users table
   # there aborts the migration transaction.
   return None

class Story(models.Model):
   title = models.CharField(max_length=255)
   created_at = models.DateTimeField(auto_now_add=True)
   categories = models.ManyToManyField(Category, related_name='stories', blank=True)
   author = models.ForeignKey(
      User,  # Reference to the user model
      on_delete=models.CASCADE,  # Delete stories if the author is deleted
      related_name="stories",  # Allows reverse access via `user.stories.all()`
      default=get_default_author
   )
   def __str__(self):
       return self.title if self.title else "Untitled Story"


class FavoriteStory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="story_favorites")
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name="favorites")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "story")

    def __str__(self):
        return f"{self.user.author_name} ♥ {self.story.title}"
