from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import CustomTokenObtainPairSerializer
from .dashboard import (
    FavoriteAuthorListView,
    FavoriteAuthorToggleView,
    FavoriteStoryListView,
    FavoriteStoryToggleView,
    ProfileDashboardView,
)
from .news import NewsFeedView
from .views import (
    PasswordResetConfirmView,
    PasswordResetRequestView,
    ProfileAvatarView,
    ProfileView,
    RegisterView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path(
        "login/",
        TokenObtainPairView.as_view(serializer_class=CustomTokenObtainPairSerializer),
        name="token_obtain_pair",
    ),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
  path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/avatar/", ProfileAvatarView.as_view(), name="profile_avatar"),
    path("profile/dashboard/", ProfileDashboardView.as_view(), name="profile_dashboard"),
    path("news/", NewsFeedView.as_view(), name="news_feed"),
    path("favorites/", FavoriteStoryListView.as_view(), name="favorite_story_list"),
    path("favorites/<int:story_id>/", FavoriteStoryToggleView.as_view(), name="favorite_story"),
    path("favorite-authors/", FavoriteAuthorListView.as_view(), name="favorite_author_list"),
    path(
        "favorite-authors/<int:author_id>/",
        FavoriteAuthorToggleView.as_view(),
        name="favorite_author",
    ),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password_reset"),
    path(
        "password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
]
