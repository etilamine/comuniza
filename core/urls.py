"""
URL configuration for Comuniza project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from django.http import JsonResponse

from .views import home_view, report_bug, bug_report_page
from apps.items import views as item_views
from apps.groups import views as group_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home_view, name="home"),
    path(
        "style-preview/",
        TemplateView.as_view(template_name="style_preview.html"),
        name="style_preview",
    ),
    # Allauth (must come before users URLs)
    path("accounts/", include("allauth.urls")),
    path("accounts/mfa/", include("allauth.mfa.urls")),
    # Item detail URLs (using identifiers)
    path("i/<str:identifier>/", item_views.ItemDetailView.as_view(), name="item_detail"),
    path("i/<str:identifier>/edit/", item_views.ItemUpdateView.as_view(), name="item_edit"),
    path("i/<str:identifier>/delete/", item_views.ItemDeleteView.as_view(), name="item_delete"),
    path("i/<str:identifier>/wishlist/add/", item_views.wishlist_add, name="item_wishlist_add"),
    path("items/", include("apps.items.urls")),
    path("users/", include("apps.users.urls")),
    path("badges/", include("apps.badges.urls")),
     # API and Groups
     path("api/", include("apps.api.urls")),
     path("api/groups-api/", include("apps.groups.api_urls")),
    # Simple test endpoint
    path("api/test/", lambda request: JsonResponse({"status": "ok"}), name="test_api"),
    path("loans/", include("apps.loans.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("messages/", include("apps.messaging.urls")),
    # FAQ
    path("faq/", TemplateView.as_view(template_name="faq.html"), name="faq"),
    # Bug reporting
    path("report-bug/", report_bug, name="report_bug"),
    path("bug-report/", bug_report_page, name="bug_report_page"),
    path("i18n/", include("django.conf.urls.i18n"), name="set_language"),
    path("groups/", include(("apps.groups.urls", "groups"), namespace="groups")),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Debug toolbar
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns += [
            path("__debug__/", include(debug_toolbar.urls)),
        ]

    # Browser reload for development
    if "django_browser_reload" in settings.INSTALLED_APPS:
        urlpatterns += [
            path("__reload__/", include("django_browser_reload.urls")),
        ]
