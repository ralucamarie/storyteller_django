import random
from django.utils.lorem_ipsum import paragraphs
from django.apps import AppConfig
from django.db.models.signals import post_migrate

def add_stories_and_writings_and_comments(sender, **kwargs):
    from django.apps import apps
    Story = apps.get_model('stories', 'Story')
    Category = apps.get_model('categories', 'Category')
    Writing = apps.get_model('writings', 'Writing')
    Comment = apps.get_model('comments', 'Comment')

    categories = list(Category.objects.all())
    if not categories:  # Ensure categories exist before proceeding
        return

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
        {"title": "Success and You", "author_name": "Julia"}
    ]

    for story_data in stories_data:
        story = Story.objects.create(**story_data)
        story_categories = random.sample(categories, random.randint(1, 3))  # Assign 1 to 3 categories
        story.categories.set(story_categories)

        # Create 3-10 writings per story
        for _ in range(random.randint(3, 10)):
            Writing.objects.create(
                story=story,
                author_name=random.choice(["Alice", "Bob", "Charlie", "Diana", "Ethan"]),
                text=" ".join(paragraphs(3))[:random.randint(1000, 5000)]
            )

        # Create 3-10 writings per story
        for _ in range(random.randint(3, 20)):
            Comment.objects.create(
                story=story,
                author_name=random.choice(["Alice", "Bob", "Charlie", "Diana", "Ethan"]),
                content=" ".join(paragraphs(3))[:random.randint(50, 1000)]
            )


class StoriesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stories'

    def ready(self):
        post_migrate.connect(add_stories_and_writings_and_comments, sender=self)
