from rest_framework import viewsets
from .models import Story
from .serializers import StorySerializer
from django.shortcuts import redirect

def home(request):
    return redirect('/api/stories/')

class StoryViewSet(viewsets.ModelViewSet):
    queryset = Story.objects.all()
    serializer_class = StorySerializer
