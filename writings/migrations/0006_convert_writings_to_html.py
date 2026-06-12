from django.db import migrations


def convert_writings_to_html(apps, schema_editor):
    Writing = apps.get_model("writings", "Writing")

    for writing in Writing.objects.iterator():
        text = writing.text or ""
        if text.lstrip().startswith("<") and ">" in text:
            continue

        image_url = writing.image.url if writing.image else None
        layout = writing.layout or "stack"

        html_parts = []
        if image_url:
            if layout in {"image_left", "image_left_50", "image_left_30"}:
                img_class = "writing-img-left"
            elif layout in {"image_right", "text_left_70"}:
                img_class = "writing-img-right"
            else:
                img_class = "writing-img-block"
            html_parts.append(
                f'<p><img src="{image_url}" class="{img_class}" alt="" loading="lazy" /></p>'
            )

        paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
        if paragraphs:
            for paragraph in paragraphs:
                escaped = (
                    paragraph.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace('"', "&quot;")
                    .replace("\n", "<br>")
                )
                html_parts.append(f"<p>{escaped}</p>")
        elif not html_parts:
            html_parts.append("<p></p>")

        writing.text = "".join(html_parts)
        writing.layout = "stack"
        writing.save(update_fields=["text", "layout"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("writings", "0005_writing_layout_three_options"),
    ]

    operations = [
        migrations.RunPython(convert_writings_to_html, noop),
    ]
