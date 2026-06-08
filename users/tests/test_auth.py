from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase

from utils.testing import create_user

User = get_user_model()


class RegisterTests(APITestCase):
    def setUp(self):
        self.url = reverse("register")
        self.payload = {
            "name": "Ana",
            "surname": "Pop",
            "email": "ana@example.com",
            "password": "StrongPass123",
            "author_name": "ana_writes",
        }

    def test_register_creates_user_and_returns_tokens(self):
        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["email"], "ana@example.com")
        self.assertEqual(response.data["user"]["author_name"], "ana_writes")
        # Password must never be echoed back.
        self.assertNotIn("password", response.data["user"])

        user = User.objects.get(email="ana@example.com")
        self.assertTrue(user.check_password("StrongPass123"))

    def test_register_rejects_duplicate_email(self):
        create_user(email="ana@example.com", author_name="other")
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_register_rejects_duplicate_author_name(self):
        create_user(email="someone@example.com", author_name="ana_writes")
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("author_name", response.data)

    def test_register_rejects_short_password(self):
        payload = {**self.payload, "password": "short"}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)


class LoginTests(APITestCase):
    def setUp(self):
        self.url = reverse("token_obtain_pair")
        self.user = create_user(email="login@example.com", author_name="loginuser")

    def test_login_with_valid_credentials_returns_tokens(self):
        response = self.client.post(
            self.url,
            {"email": "login@example.com", "password": "StrongPass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_with_wrong_password_is_rejected(self):
        response = self.client.post(
            self.url,
            {"email": "login@example.com", "password": "wrong-password"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PasswordResetTests(APITestCase):
    def setUp(self):
        self.request_url = reverse("password_reset")
        self.confirm_url = reverse("password_reset_confirm")
        self.user = create_user(email="reset@example.com", author_name="resetuser")

    def test_request_sends_email_for_existing_user(self):
        response = self.client.post(
            self.request_url, {"email": "reset@example.com"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("reset@example.com", mail.outbox[0].to)

    def test_request_does_not_leak_unknown_email(self):
        response = self.client.post(
            self.request_url, {"email": "ghost@example.com"}, format="json"
        )
        # Same generic 200 response, but no email is actually sent.
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)

    def test_confirm_with_valid_token_changes_password(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        response = self.client.post(
            self.confirm_url,
            {"uid": uid, "token": token, "password": "BrandNewPass1"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("BrandNewPass1"))

    def test_confirm_with_invalid_token_is_rejected(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        response = self.client.post(
            self.confirm_url,
            {"uid": uid, "token": "not-a-valid-token", "password": "BrandNewPass1"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("StrongPass123"))
