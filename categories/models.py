from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Name of the category
    description = models.TextField(blank=True, null=True)  # Optional description for the category

    def __str__(self):
        return self.name
