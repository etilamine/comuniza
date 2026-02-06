"""
API URLs for groups app.
"""

from django.urls import path
from . import views

app_name = 'groups_api'

urlpatterns = [
    path("locations/", views.group_locations_api, name="group_locations_api"),
    path("search-users/", views.search_users_api, name="search_users_api"),
    path("debug/", views.debug_groups_url, name="debug_groups_url"),  # Add this debug endpoint
]
