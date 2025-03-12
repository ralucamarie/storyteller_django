from rest_framework import serializers
from .models import Story
from categories.serializers import CategorySerializer  # Import this!
from categories.models import Category  # Ensure you import the model
from writings.serializers import WritingSerializer
from utils.serializers import CamelCaseSerializer


class StorySerializer(CamelCaseSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    writings = WritingSerializer(many=True, read_only=True)

    class Meta:
        model = Story
        fields = '__all__'
