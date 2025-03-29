from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a new superuser with email, name, surname, and author_name."

    def add_arguments(self, parser):
        parser.add_argument("--email", type=str, required=True, help="Superuser email")
        parser.add_argument("--name", type=str, required=True, help="Superuser name")
        parser.add_argument("--surname", type=str, required=True, help="Superuser surname")
        parser.add_argument("--author_name", type=str, required=True, help="Superuser author_name")
        parser.add_argument("--password", type=str, required=True, help="Superuser password")

    def handle(self, *args, **options):
        User = get_user_model()

        email = options["email"]
        name = options["name"]
        surname = options["surname"]
        author_name = options["author_name"]
        password = options["password"]

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.ERROR(f"User with email {email} already exists."))
            return

        user = User.objects.create_superuser(
            email=email,
            name=name,
            surname=surname,
            author_name=author_name,
            password=password,
        )

        self.stdout.write(self.style.SUCCESS(f"Superuser {user.email} created successfully!"))
