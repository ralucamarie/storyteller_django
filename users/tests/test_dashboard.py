from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from comments.models import Comment
from stories.models import Story
from users.dashboard import _gamification
from utils.testing import auth_client, create_user
from writings.models import Writing


class GamificationUnitTests(APITestCase):
    def test_points_and_level_calculation(self):
        result = _gamification(stories_count=2, contributions_count=3, comments_count=5)
        # 2*50 + 3*20 + 5*10 = 210
        self.assertEqual(result["points"], 210)
        self.assertEqual(result["level"], 3)  # 210 // 100 + 1
        self.assertEqual(result["level_progress"], 10)

    def test_badges_awarded_by_thresholds(self):
        result = _gamification(stories_count=5, contributions_count=3, comments_count=5)
        badge_ids = {badge["id"] for badge in result["badges"]}
        self.assertIn("storyteller", badge_ids)
        self.assertIn("author", badge_ids)
        self.assertIn("contributor", badge_ids)
        self.assertIn("critic", badge_ids)


class DashboardViewTests(APITestCase):
    def setUp(self):
        self.user = create_user(email="dash@example.com", author_name="dash")
        self.other = create_user(email="other@example.com", author_name="other")

        self.story = Story.objects.create(title="My story", author=self.user)
        Writing.objects.create(story=self.story, author=self.user, text="Opening line")

        other_story = Story.objects.create(title="Other story", author=self.other)
        Comment.objects.create(
            story_id=other_story, author=self.user, content="Nice work!"
        )

        self.client = auth_client(self.user)
        self.url = reverse("profile_dashboard")

    def test_dashboard_requires_authentication(self):
        response = APIClient().get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_dashboard_returns_stats_and_gamification(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        stats = response.data["stats"]
        self.assertEqual(stats["stories_written"], 1)
        self.assertEqual(stats["contributions"], 0)  # own-story writings don't count
        self.assertEqual(stats["comments"], 1)

        # 1*50 + 0 + 1*10 = 60
        self.assertEqual(response.data["gamification"]["points"], 60)
        self.assertEqual(response.data["user"]["author_name"], "dash")
        self.assertIn("daily", response.data["activity"])
        self.assertIn("weekly", response.data["activity"])


class NewsFeedTests(APITestCase):
    def setUp(self):
        self.user = create_user(email="news@example.com", author_name="newsuser")
        self.other = create_user(email="contrib@example.com", author_name="contrib")
        self.story = Story.objects.create(title="Shared story", author=self.user)
        self.client = auth_client(self.user)
        self.url = reverse("news_feed")

    def test_contribution_on_my_story_appears_in_feed(self):
        Writing.objects.create(
            story=self.story, author=self.other, text="A new chapter"
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)
        types = {item["type"] for item in response.data["items"]}
        self.assertIn("contribution_on_my_story", types)

    def test_my_own_activity_is_excluded(self):
        Writing.objects.create(story=self.story, author=self.user, text="My own chapter")
        response = self.client.get(self.url)
        self.assertEqual(response.data["count"], 0)
