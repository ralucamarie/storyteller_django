from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StoryViewSet, home

router = DefaultRouter()
router.register(r'stories', StoryViewSet, basename='story')

urlpatterns = [
    path('', home, name='home'),
    path('api/', include(router.urls)),
]
