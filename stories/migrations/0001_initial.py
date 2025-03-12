# Generated by Django 5.1.7 on 2025-03-11 12:17

from django.db import migrations, models

def add_stories_and_writings(apps, schema_editor):
    Story = apps.get_model('stories', 'Story')
    Category = apps.get_model('categories', 'Category')
    Writing = apps.get_model('writings', 'Writing')

    categories = list(Category.objects.all())  # Fetch all categories

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
                text=lorem.paragraph()[:random.randint(1000, 5000)]
            )


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('categories', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Story',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('author_name', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('categories', models.ManyToManyField(blank=True, related_name='stories', to='categories.category')),
            ],
        ),
        migrations.RunPython(add_stories_and_writings)
    ]
