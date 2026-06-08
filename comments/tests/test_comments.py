from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from comments.models import Comment, CommentLike, CommentReaction
from stories.models import Story
from utils.testing import auth_client, create_user


class CommentCrudTests(APITestCase):
    def setUp(self):
        self.author = create_user(email="c@example.com", author_name="c")
        self.story = Story.objects.create(title="Discussed", author=self.author)
        self.url = reverse("comment-list")

    def test_create_requires_authentication(self):
        response = APIClient().post(
            self.url, {"story_id": self.story.id, "content": "Hi"}, format="json"
        )
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_create_comment(self):
        client = auth_client(self.author)
        response = client.post(
            self.url, {"story_id": self.story.id, "content": "  Great!  "}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Content is trimmed by the serializer.
        self.assertEqual(response.data["content"], "Great!")
        self.assertEqual(response.data["isMine"], True)
        self.assertEqual(response.data["likesCount"], 0)
        comment = Comment.objects.get(pk=response.data["id"])
        self.assertEqual(comment.author, self.author)

    def test_create_rejects_empty_content(self):
        client = auth_client(self.author)
        response = client.post(
            self.url, {"story_id": self.story.id, "content": "   "}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_requires_story(self):
        client = auth_client(self.author)
        response = client.post(self.url, {"content": "Orphan comment"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("story_id", response.data)

    def test_update_only_own_comment(self):
        intruder = create_user(email="x@example.com", author_name="x")
        comment = Comment.objects.create(
            story_id=self.story, author=self.author, content="Mine"
        )
        detail = reverse("comment-detail", args=[comment.id])

        owner_resp = auth_client(self.author).patch(
            detail, {"content": "Edited"}, format="json"
        )
        self.assertEqual(owner_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(owner_resp.data["content"], "Edited")

        intruder_resp = auth_client(intruder).patch(
            detail, {"content": "Hacked"}, format="json"
        )
        self.assertEqual(intruder_resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_only_own_comment(self):
        intruder = create_user(email="y@example.com", author_name="y")
        comment = Comment.objects.create(
            story_id=self.story, author=self.author, content="Mine"
        )
        detail = reverse("comment-detail", args=[comment.id])

        self.assertEqual(
            auth_client(intruder).delete(detail).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            auth_client(self.author).delete(detail).status_code,
            status.HTTP_204_NO_CONTENT,
        )


class CommentFilterTests(APITestCase):
    def setUp(self):
        self.user_a = create_user(email="ua@example.com", author_name="ua")
        self.user_b = create_user(email="ub@example.com", author_name="ub")
        self.story1 = Story.objects.create(title="S1", author=self.user_a)
        self.story2 = Story.objects.create(title="S2", author=self.user_a)
        Comment.objects.create(story_id=self.story1, author=self.user_a, content="a1")
        Comment.objects.create(story_id=self.story2, author=self.user_b, content="b2")

    def test_filter_by_story(self):
        response = self.client.get(reverse("comment-list"), {"story": self.story1.id})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["content"], "a1")

    def test_filter_by_user(self):
        response = self.client.get(
            reverse("comment-list"), {"user_id": self.user_b.id}
        )
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["content"], "b2")


class CommentLikeTests(APITestCase):
    def setUp(self):
        self.author = create_user(email="auth@example.com", author_name="cauth")
        self.reader = create_user(email="read@example.com", author_name="creader")
        self.story = Story.objects.create(title="Likeable", author=self.author)
        self.comment = Comment.objects.create(
            story_id=self.story, author=self.author, content="Like me"
        )
        self.url = reverse("comment-like", args=[self.comment.id])

    def test_like_toggles_on_and_off(self):
        client = auth_client(self.reader)

        on = client.post(self.url)
        self.assertEqual(on.status_code, status.HTTP_200_OK)
        self.assertEqual(on.data["likesCount"], 1)
        self.assertTrue(on.data["likedByMe"])

        off = client.post(self.url)
        self.assertEqual(off.data["likesCount"], 0)
        self.assertFalse(off.data["likedByMe"])

    def test_cannot_like_own_comment(self):
        response = auth_client(self.author).post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CommentLike.objects.count(), 0)


class CommentReactionTests(APITestCase):
    def setUp(self):
        self.author = create_user(email="ra@example.com", author_name="rauthor")
        self.reader = create_user(email="rr@example.com", author_name="rreader")
        self.story = Story.objects.create(title="Reactable", author=self.author)
        self.comment = Comment.objects.create(
            story_id=self.story, author=self.author, content="React to me"
        )
        self.url = reverse("comment-react", args=[self.comment.id])

    def test_add_and_toggle_reaction(self):
        client = auth_client(self.reader)

        add = client.post(self.url, {"emoji": "❤️"}, format="json")
        self.assertEqual(add.status_code, status.HTTP_200_OK)
        reactions = {r["emoji"]: r for r in add.data["reactions"]}
        self.assertEqual(reactions["❤️"]["count"], 1)
        # Inner keys of a SerializerMethodField stay snake_case.
        self.assertTrue(reactions["❤️"]["reacted_by_me"])

        # Same emoji again removes it.
        remove = client.post(self.url, {"emoji": "❤️"}, format="json")
        self.assertEqual(remove.data["reactions"], [])

    def test_changing_emoji_replaces_reaction(self):
        client = auth_client(self.reader)
        client.post(self.url, {"emoji": "❤️"}, format="json")
        client.post(self.url, {"emoji": "🔥"}, format="json")
        self.assertEqual(CommentReaction.objects.filter(comment=self.comment).count(), 1)
        self.assertEqual(
            CommentReaction.objects.get(comment=self.comment).emoji, "🔥"
        )

    def test_invalid_emoji_is_rejected(self):
        response = auth_client(self.reader).post(
            self.url, {"emoji": "💩"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_react_to_own_comment(self):
        response = auth_client(self.author).post(
            self.url, {"emoji": "❤️"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
