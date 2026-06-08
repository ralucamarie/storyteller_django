from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from stories.models import Story
from utils.testing import auth_client, create_user

FAKE_RESULT = {"mode": "suggestion", "title": "Idea", "content": "Try a twist."}


class WritingAssistViewTests(APITestCase):
    def setUp(self):
        self.user = create_user(email="assist@example.com", author_name="assist")
        self.url = reverse("writing-assist")

    def test_requires_authentication(self):
        response = APIClient().post(self.url, {"mode": "suggestion"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_mode_returns_400(self):
        response = auth_client(self.user).post(
            self.url, {"mode": "nonsense"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("writings.assist_views.generate_new_story_assist", return_value=FAKE_RESULT)
    def test_new_story_assist_without_story_id(self, mock_generate):
        response = auth_client(self.user).post(
            self.url,
            {"mode": "suggestion", "title": "Quest", "categories": ["Adventure"]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Idea")
        mock_generate.assert_called_once()
        # Title and categories are forwarded to the generator.
        self.assertEqual(mock_generate.call_args.kwargs["title"], "Quest")
        self.assertEqual(mock_generate.call_args.kwargs["categories"], ["Adventure"])

    @patch("writings.assist_views.generate_writing_assist", return_value=FAKE_RESULT)
    def test_existing_story_assist(self, mock_generate):
        story = Story.objects.create(title="Existing", author=self.user)
        response = auth_client(self.user).post(
            self.url, {"mode": "game", "story_id": story.id}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_generate.assert_called_once()

    def test_unknown_story_returns_404(self):
        response = auth_client(self.user).post(
            self.url, {"mode": "suggestion", "story_id": 999999}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
