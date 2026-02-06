"""
URL patterns for Users app.
"""

from django.urls import path

from . import views
from .views_account import EmailConfirmationView

app_name = "users"

urlpatterns = [
    # Profile
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("profile/privacy/", views.privacy_settings, name="privacy_settings"),
    # Username change confirmation
    path("confirm-username/<str:token>/", views.confirm_username_change, name="confirm_username_change"),
    # Email confirmation
    path("confirm-email/<str:key>/", EmailConfirmationView.as_view(), name="account_confirm_email"),
    # 2FA setup (if implementing custom 2FA)
    path("security/", views.security_settings, name="security"),
    # API
    path("api/search/", views.user_search_api, name="user_search_api"),
]
