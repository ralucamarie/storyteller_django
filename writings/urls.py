from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .assist_views import WritingAssistView
from .views import WritingViewSet

router = DefaultRouter()
router.register(r"", WritingViewSet, basename="writing")

urlpatterns = [
    path("assist/", WritingAssistView.as_view(), name="writing-assist"),
    path("", include(router.urls)),
]
