"""
URL patterns for Groups app.
"""

from django.urls import path

from . import views

app_name = "groups"

urlpatterns = [
    # List and browse
    path("", views.index, name="list"),
    # Create
    path("create/", views.create_group, name="create"),
    # Detail, join, leave (slug-based)
    path("<slug:slug>/", views.group_detail, name="detail"),
    path("<slug:slug>/join/", views.join_group, name="join"),
    path("<slug:slug>/leave/", views.leave_group, name="leave"),
    # Management
    path("<slug:slug>/manage/", views.manage_group, name="manage"),
    path("<slug:slug>/settings/", views.group_settings, name="settings"),
    # Invitations
    path("invite/<str:token>/", views.accept_invitation, name="accept_invitation"),
]
