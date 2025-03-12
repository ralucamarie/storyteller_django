from django.db import models
from django.contrib.auth.models import User
from categories.models import Category  # Import the Category model from the 'category' app


# Create your models here.
class Story(models.Model):
   title = models.CharField(max_length=255)
   author_name = models.CharField(max_length=100)
   created_at = models.DateTimeField(auto_now_add=True)
   categories = models.ManyToManyField(Category, related_name='stories', blank=True)  # Many-to-many relationship

   def __str__(self):
       return self.title if self.title else "Untitled Story"
