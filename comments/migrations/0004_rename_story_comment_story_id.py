# Generated by Django 5.1.7 on 2025-03-29 06:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('comments', '0003_remove_comment_author_name_comment_author'),
    ]

    operations = [
        migrations.RenameField(
            model_name='comment',
            old_name='story',
            new_name='story_id',
        ),
    ]
