from django.db import migrations, models


def migrate_layout_values(apps, schema_editor):
    Writing = apps.get_model("writings", "Writing")
    Writing.objects.filter(layout__in=["image_left_50", "image_left_30"]).update(
        layout="image_left"
    )
    Writing.objects.filter(layout="text_left_70").update(layout="image_right")


def revert_layout_values(apps, schema_editor):
    Writing = apps.get_model("writings", "Writing")
    Writing.objects.filter(layout="image_left").update(layout="image_left_30")
    Writing.objects.filter(layout="image_right").update(layout="text_left_70")


class Migration(migrations.Migration):
    dependencies = [
        ("writings", "0004_writing_layout"),
    ]

    operations = [
        migrations.RunPython(migrate_layout_values, revert_layout_values),
        migrations.AlterField(
            model_name="writing",
            name="layout",
            field=models.CharField(
                choices=[
                    ("stack", "Image above text"),
                    ("image_left", "Image left, text wraps (max 40%)"),
                    ("image_right", "Image right, text wraps (max 40%)"),
                ],
                default="stack",
                max_length=20,
            ),
        ),
    ]
