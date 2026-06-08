from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class UserManagerTests(TestCase):
    def test_create_user_normalizes_email_and_hashes_password(self):
        user = User.objects.create_user(
            email="Person@Example.COM",
            password="secret123",
            author_name="person",
            name="P",
            surname="Q",
        )

        # Domain part is lower-cased by normalize_email.
        self.assertEqual(user.email, "Person@example.com")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        # Password is stored hashed, not in clear text.
        self.assertNotEqual(user.password, "secret123")
        self.assertTrue(user.check_password("secret123"))

    def test_create_user_without_email_raises(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="x", author_name="noemail")

    def test_create_superuser_sets_flags(self):
        admin = User.objects.create_superuser(
            email="admin@example.com",
            password="secret123",
            author_name="admin",
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_create_superuser_requires_staff_flag(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="bad@example.com",
                password="x",
                author_name="bad",
                is_staff=False,
            )

    def test_str_is_email(self):
        user = User.objects.create_user(
            email="str@example.com", password="x", author_name="strname"
        )
        self.assertEqual(str(user), "str@example.com")

    def test_username_field_is_email(self):
        self.assertEqual(User.USERNAME_FIELD, "email")
        self.assertIn("author_name", User.REQUIRED_FIELDS)
