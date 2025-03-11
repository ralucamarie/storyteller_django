from rest_framework import serializers
from .models import Story
from categories.serializers import CategorySerializer  # Import this!
from categories.models import Category  # Ensure you import the model

class StorySerializer(serializers.ModelSerializer):

    categories = CategorySerializer(many=True, read_only=True)  # Include categories in the story serializer

    class Meta:
        model = Story
        fields = ['id', 'title', 'author', 'created_at', 'categories']
