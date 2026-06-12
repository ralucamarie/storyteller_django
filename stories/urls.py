from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import StoryViewSet, home

router = DefaultRouter()
router.register(r"", StoryViewSet, basename="story")

urlpatterns = [
    path("", home, name="home"),
    path("api/stories/", include(router.urls)),
]
