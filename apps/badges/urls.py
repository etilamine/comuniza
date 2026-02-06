"""
URL configuration for badges app.
"""

from django.urls import path

from apps.badges import views

app_name = 'badges'

urlpatterns = [
    path('', views.BadgeListView.as_view(), name='list'),
    path('my-badges/', views.UserBadgeListView.as_view(), name='my_badges'),
    path('leaderboard/', views.LeaderboardView.as_view(), name='leaderboard'),
    path('badge/<slug:slug>/', views.badge_detail, name='detail'),
]