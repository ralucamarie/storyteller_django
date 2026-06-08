import random
from django.utils.lorem_ipsum import paragraphs
from django.apps import AppConfig
from django.db.models.signals import post_migrate

def add_stories_and_writings_and_comments(sender, **kwargs):
    from django.conf import settings

    # Skip demo seeding during tests (and anywhere SEED_DEMO_DATA is disabled),
    # so the test database starts empty and tests stay isolated.
    if not getattr(settings, "SEED_DEMO_DATA", True):
        return

    from django.apps import apps
    Story = apps.get_model('stories', 'Story')
    Category = apps.get_model('categories', 'Category')
    Writing = apps.get_model('writings', 'Writing')
    Comment = apps.get_model('comments', 'Comment')
    User = apps.get_model('users', 'User')

    if Story.objects.exists():
        return

    categories = list(Category.objects.all())
    if not categories:
        return

    authors = {}
    for author_name in ["Alice", "Bob", "Charlie", "Diana", "Ethan", "Fiona", "George", "Hannah", "Ian", "Julia"]:
        user, _ = User.objects.get_or_create(
            author_name=author_name,
            defaults={
                "email": f"{author_name.lower()}@example.com",
                "name": author_name,
                "surname": "Author",
                "password": "unused",
            },
        )
        authors[author_name] = user

    stories_data = [
        {"title": "The Enchanted Forest", "author_name": "Alice"},
        {"title": "Space Odyssey", "author_name": "Bob"},
        {"title": "The Secret Code", "author_name": "Charlie"},
        {"title": "Love in Paris", "author_name": "Diana"},
        {"title": "Haunted Mansion", "author_name": "Ethan"},
        {"title": "The Lost Kingdom", "author_name": "Fiona"},
        {"title": "Journey to the Unknown", "author_name": "George"},
        {"title": "The Diary of a Scientist", "author_name": "Hannah"},
        {"title": "My Life Memoir", "author_name": "Ian"},
        {"title": "Success and You", "author_name": "Julia"},
    ]

    author_names = list(authors.keys())
    for story_data in stories_data:
        author_name = story_data.pop("author_name")
        story = Story.objects.create(author=authors[author_name], **story_data)
        story.categories.set(random.sample(categories, random.randint(1, 3)))

        for _ in range(random.randint(3, 10)):
            writer = authors[random.choice(author_names)]
            Writing.objects.create(
                story=story,
                author=writer,
                text=" ".join(paragraphs(3))[:random.randint(1000, 5000)],
            )

        for _ in range(random.randint(3, 20)):
            Comment.objects.create(
                story_id=story,
                author=random.choice(list(authors.values())),
                content=" ".join(paragraphs(3))[:random.randint(50, 1000)],
            )


class StoriesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stories'

    def ready(self):
        post_migrate.connect(add_stories_and_writings_and_comments, sender=self)
