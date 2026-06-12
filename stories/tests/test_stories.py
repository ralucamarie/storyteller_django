from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from categories.models import Category
from stories.models import Story
from utils.testing import auth_client, create_user
from writings.models import Writing


class StoryReadTests(APITestCase):
    def setUp(self):
        self.author = create_user(email="a@example.com", author_name="a")
        self.story = Story.objects.create(title="Public tale", author=self.author)
        Writing.objects.create(story=self.story, author=self.author, text="Hello world")

    def test_list_is_public(self):
        response = APIClient().get(reverse("story-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        # CamelCaseSerializer output.
        self.assertIn("createdAt", response.data[0])
        self.assertIn("categoryObjects", response.data[0])
        self.assertEqual(response.data[0]["title"], "Public tale")

    def test_home_redirects_to_story_api(self):
        response = APIClient().get(reverse("home"))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, "/api/stories/")


class StoryCreateTests(APITestCase):
    def setUp(self):
        self.user = create_user(email="creator@example.com", author_name="creator")
        self.url = reverse("story-list")
        self.payload = {
            "title": "A brand new story",
            "content": "Once upon a time...",
            "categories": ["Adventure", "Fantasy"],
            "layout": "stack",
        }

    def test_create_requires_authentication(self):
        response = APIClient().post(self.url, self.payload, format="json")
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_create_story_with_first_writing_and_categories(self):
        client = auth_client(self.user)
        response = client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        story = Story.objects.get(title="A brand new story")
        self.assertEqual(story.author, self.user)
        self.assertEqual(story.writings.count(), 1)
        self.assertEqual(story.writings.first().text, "<p>Once upon a time...</p>")
        self.assertEqual(story.categories.count(), 2)
        self.assertTrue(Category.objects.filter(name="Adventure").exists())

    def test_existing_categories_are_reused(self):
        Category.objects.create(name="Adventure")
        client = auth_client(self.user)
        client.post(self.url, self.payload, format="json")
        self.assertEqual(Category.objects.filter(name="Adventure").count(), 1)

    def test_create_requires_content(self):
        client = auth_client(self.user)
        payload = {**self.payload}
        payload.pop("content")
        response = client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("content", response.data)

    def test_create_requires_at_least_one_category(self):
        client = auth_client(self.user)
        payload = {**self.payload, "categories": []}
        response = client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("categories", response.data)


class StoryDeleteTests(APITestCase):
    def setUp(self):
        self.owner = create_user(email="owner@example.com", author_name="owner")
        self.intruder = create_user(email="intruder@example.com", author_name="intruder")
        self.story = Story.objects.create(title="Owned", author=self.owner)

    def test_owner_can_delete(self):
        client = auth_client(self.owner)
        response = client.delete(reverse("story-detail", args=[self.story.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Story.objects.filter(pk=self.story.id).exists())

    def test_non_owner_cannot_delete(self):
        client = auth_client(self.intruder)
        response = client.delete(reverse("story-detail", args=[self.story.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Story.objects.filter(pk=self.story.id).exists())


class StoryTypingTests(APITestCase):
    def setUp(self):
        self.user = create_user(email="typer@example.com", author_name="typer")
        self.story = Story.objects.create(title="Live", author=self.user)

    def test_typing_get_returns_empty_list_initially(self):
        response = auth_client(self.user).get(
            reverse("story-typing", args=[self.story.id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["typers"], [])

    def test_typing_post_excludes_self(self):
        client = auth_client(self.user)
        response = client.post(reverse("story-typing", args=[self.story.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The requesting user is excluded from the typers list.
        self.assertEqual(response.data["typers"], [])
