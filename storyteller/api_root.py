"""Browsable API root listing all top-level resources."""

from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView


class ApiRootView(APIView):
    """Human-friendly index of the public HTTP API (DRF browsable API landing page)."""

    def get(self, request, *args, **kwargs):
        return Response(
            {
                "stories": reverse("story-list", request=request),
                "writings": request.build_absolute_uri("/api/writings/"),
                "writingAssist": request.build_absolute_uri("/api/writings/assist/"),
                "comments": request.build_absolute_uri("/api/comments/"),
                "users": {
                    "register": request.build_absolute_uri("/api/users/register/"),
                    "login": request.build_absolute_uri("/api/users/login/"),
                    "tokenRefresh": request.build_absolute_uri("/api/users/token/refresh/"),
                    "profile": request.build_absolute_uri("/api/users/profile/"),
                    "profileAvatar": request.build_absolute_uri("/api/users/profile/avatar/"),
                    "dashboard": request.build_absolute_uri("/api/users/profile/dashboard/"),
                    "news": request.build_absolute_uri("/api/users/news/"),
                    "favorites": request.build_absolute_uri("/api/users/favorites/"),
                    "favoriteAuthors": request.build_absolute_uri(
                        "/api/users/favorite-authors/"
                    ),
                    "passwordReset": request.build_absolute_uri("/api/users/password-reset/"),
                    "passwordResetConfirm": request.build_absolute_uri(
                        "/api/users/password-reset/confirm/"
                    ),
                },
            }
        )
