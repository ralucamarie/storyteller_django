from django.apps import AppConfig
from django.db.models.signals import post_migrate


def populate_categories(sender, **kwargs):
    from .models import Category  # Import inside to avoid circular imports
    categories = [
        "fantasy", "scienceFiction", "mysteryThriller", "romance", "horror",
        "historicalFiction", "adventure", "biography", "memoir", "selfHelp",
        "travel", "trueCrime", "scienceTechnology", "history", "politics",
        "business", "sports", "entertainment", "health", "opinionEssays",
        "socialIssues", "inspirational", "fanFiction", "childrenStories", "youngAdult"
    ]

    for category in categories:
        Category.objects.get_or_create(name=category)

class CategoriesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'categories'

    def ready(self):
        post_migrate.connect(populate_categories, sender=self)
