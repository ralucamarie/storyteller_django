from rest_framework import serializers
from .models import Writing
from utils.serializers import CamelCaseSerializer


class WritingSerializer(CamelCaseSerializer):

    class Meta:
        model = Writing
        fields = '__all__'
