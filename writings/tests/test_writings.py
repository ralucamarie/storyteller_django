import shutil
import tempfile

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from stories.models import Story
from utils.testing import auth_client, create_user, make_image_file
from writings.models import Writing, WritingLayout

TEMP_MEDIA = tempfile.mkdtemp(prefix="storyteller-writing-img-")


class WritingCrudTests(APITestCase):
    def setUp(self):
        self.author = create_user(email="w@example.com", author_name="w")
        self.story = Story.objects.create(title="Continuing", author=self.author)
        self.url = reverse("writing-list")

    def test_create_requires_authentication(self):
        response = APIClient().post(
            self.url, {"story": self.story.id, "text": "Hi"}, format="json"
        )
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_authenticated_user_can_add_writing(self):
        client = auth_client(self.author)
        response = client.post(
            self.url,
            {"story": self.story.id, "text": "Next chapter", "layout": "stack"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["text"], "<p>Next chapter</p>")
        # CamelCase output from the serializer.
        self.assertIn("imageUrl", response.data)
        self.assertIn("imageUpdated", response.data)

        writing = Writing.objects.get(pk=response.data["id"])
        self.assertEqual(writing.author, self.author)
        self.assertEqual(writing.layout, WritingLayout.STACK)

    def test_list_can_be_filtered_by_story(self):
        other_story = Story.objects.create(title="Other", author=self.author)
        Writing.objects.create(story=self.story, author=self.author, text="A")
        Writing.objects.create(story=other_story, author=self.author, text="B")

        response = self.client.get(self.url, {"story": self.story.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["text"], "A")


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class WritingImageTests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.author = create_user(email="imgowner@example.com", author_name="imgowner")
        self.intruder = create_user(email="nope@example.com", author_name="nope")
        self.story = Story.objects.create(title="Pictured", author=self.author)
        self.writing = Writing.objects.create(
            story=self.story, author=self.author, text="With picture"
        )
        self.url = reverse("writing-image", args=[self.writing.id])

    def test_owner_can_upload_image(self):
        client = auth_client(self.author)
        response = client.post(
            self.url, {"image": make_image_file("w.png")}, format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data["imageUrl"])
        self.writing.refresh_from_db()
        self.assertTrue(bool(self.writing.image))

    def test_non_owner_cannot_upload_image(self):
        client = auth_client(self.intruder)
        response = client.post(
            self.url, {"image": make_image_file("w.png")}, format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_image_action_requires_authentication(self):
        response = APIClient().post(
            self.url, {"image": make_image_file("w.png")}, format="multipart"
        )
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )
