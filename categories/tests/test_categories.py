from django.test import TestCase

from categories.models import Category
from categories.serializers import CategorySerializer


class CategoryModelTests(TestCase):
    def test_str_returns_name(self):
        category = Category.objects.create(name="Adventure")
        self.assertEqual(str(category), "Adventure")

    def test_name_is_unique(self):
        Category.objects.create(name="Mystery")
        with self.assertRaises(Exception):
            Category.objects.create(name="Mystery")


class CategorySerializerTests(TestCase):
    def test_serializes_expected_fields(self):
        category = Category.objects.create(name="Sci-Fi", description="Robots & space")
        data = CategorySerializer(category).data

        self.assertEqual(data["id"], category.id)
        self.assertEqual(data["name"], "Sci-Fi")
        self.assertEqual(data["description"], "Robots & space")
