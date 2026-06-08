from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('writings', '0003_writing_image_writing_image_updated'),
    ]

    operations = [
        migrations.AddField(
            model_name='writing',
            name='layout',
            field=models.CharField(
                choices=[
                    ('stack', 'Image above text'),
                    ('image_left_50', 'Image left 50%, text right 50%'),
                    ('image_left_30', 'Image left 30%, text right 70%'),
                    ('text_left_70', 'Text left 70%, image right 30%'),
                ],
                default='stack',
                max_length=20,
            ),
        ),
    ]
