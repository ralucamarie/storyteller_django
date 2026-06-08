import shutil
import tempfile

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from stories.models import FavoriteStory, Story
from users.models import FavoriteAuthor
from utils.testing import auth_client, create_user, make_image_file

TEMP_MEDIA = tempfile.mkdtemp(prefix="storyteller-avatar-test-")


class ProfileViewTests(APITestCase):
    def setUp(self):
        self.user = create_user(email="me@example.com", author_name="me")
        self.url = reverse("profile")

    def test_profile_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_returns_current_user(self):
        client = auth_client(self.user)
        response = client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "me@example.com")
        self.assertEqual(response.data["author_name"], "me")


class FavoriteStoryTests(APITestCase):
    def setUp(self):
        self.user = create_user(email="reader@example.com", author_name="reader")
        self.author = create_user(email="writer@example.com", author_name="writer")
        self.story = Story.objects.create(title="A tale", author=self.author)
        self.client = auth_client(self.user)

    def test_toggle_and_list_favorite_stories(self):
        toggle_url = reverse("favorite_story", args=[self.story.id])

        add = self.client.post(toggle_url)
        self.assertEqual(add.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            FavoriteStory.objects.filter(user=self.user, story=self.story).exists()
        )

        listing = self.client.get(reverse("favorite_story_list"))
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(listing.data["story_ids"], [self.story.id])

        remove = self.client.delete(toggle_url)
        self.assertEqual(remove.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            FavoriteStory.objects.filter(user=self.user, story=self.story).exists()
        )

    def test_adding_same_favorite_twice_is_idempotent(self):
        toggle_url = reverse("favorite_story", args=[self.story.id])
        self.client.post(toggle_url)
        self.client.post(toggle_url)
        self.assertEqual(
            FavoriteStory.objects.filter(user=self.user, story=self.story).count(), 1
        )


class FavoriteAuthorTests(APITestCase):
    def setUp(self):
        self.user = create_user(email="fan@example.com", author_name="fan")
        self.author = create_user(email="star@example.com", author_name="star")
        self.client = auth_client(self.user)

    def test_favorite_author_flow(self):
        toggle_url = reverse("favorite_author", args=[self.author.id])

        add = self.client.post(toggle_url)
        self.assertEqual(add.status_code, status.HTTP_201_CREATED)

        listing = self.client.get(reverse("favorite_author_list"))
        self.assertEqual(listing.data["author_ids"], [self.author.id])
        self.assertEqual(listing.data["authors"][0]["author_name"], "star")

        remove = self.client.delete(toggle_url)
        self.assertEqual(remove.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            FavoriteAuthor.objects.filter(user=self.user, author=self.author).exists()
        )

    def test_cannot_favorite_self(self):
        response = self.client.post(reverse("favorite_author", args=[self.user.id]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class ProfileAvatarTests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = create_user(email="avatar@example.com", author_name="avataruser")
        self.client = auth_client(self.user)
        self.url = reverse("profile_avatar")

    def test_upload_avatar_returns_url(self):
        response = self.client.post(
            self.url,
            {"image": make_image_file("avatar.png")},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data["avatar_url"])
        self.user.refresh_from_db()
        self.assertTrue(bool(self.user.avatar))

    def test_delete_avatar(self):
        self.client.post(
            self.url, {"image": make_image_file("avatar.png")}, format="multipart"
        )
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.user.refresh_from_db()
        self.assertFalse(bool(self.user.avatar))

    def test_avatar_rejects_non_image(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        bad = SimpleUploadedFile("note.txt", b"not an image", content_type="text/plain")
        response = self.client.post(self.url, {"image": bad}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
