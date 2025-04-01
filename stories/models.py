from django.contrib.auth import get_user_model
from django.db import models
from categories.models import Category  # Import the Category model from the 'category' app

User = get_user_model()

def get_default_author():
   return User.objects.first().id  # Pick the first user as default (change as needed)

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
