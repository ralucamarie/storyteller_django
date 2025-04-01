from rest_framework import viewsets, request
from .models import Story
from .serializers import StorySerializer
from django.shortcuts import redirect

def home(request):
    return redirect('/api/stories/')

class StoryViewSet(viewsets .ModelViewSet):
    queryset = Story.objects.all()
    serializer_class = StorySerializer

    def perform_create(self, serializer):
        serializer.save()