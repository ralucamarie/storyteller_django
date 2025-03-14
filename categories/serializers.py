from rest_framework import serializers
from categories.models import Category
from utils.serializers import CamelCaseSerializer

class CategorySerializer(CamelCaseSerializer):

    class Meta:
        model = Category
        fields = '__all__'
