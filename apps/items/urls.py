"""
URL patterns for Items app.
"""

from django.urls import path

from . import views

app_name = "items"

urlpatterns = [
    # List and browse
    path("", views.ItemListView.as_view(), name="list"),
    path("my-items/", views.MyItemsView.as_view(), name="my_items"),
    # Create
    path("create/", views.ItemCreateView.as_view(), name="create"),
    # Deactivate/Reactivate (must come before identifier patterns)
    path("deactivate/<str:identifier>/", views.item_deactivate, name="item_deactivate"),
    path("reactivate/<str:identifier>/", views.item_reactivate, name="item_reactivate"),
    # ISBN lookup (must come before identifier patterns)
    path("isbn-lookup/", views.isbn_lookup, name="isbn_lookup"),
    # Wishlist
    path("wishlist/", views.wishlist_view, name="wishlist"),
    path("wishlist/remove/<int:item_id>/", views.wishlist_remove, name="wishlist_remove"),
    # Image management
    path("image/<int:image_id>/delete/", views.delete_item_image, name="delete_image"),
    
    # Temporary image management for live upload
    path("upload-temp-image/", views.upload_temp_image, name="upload_temp_image"),
    path("delete-temp-image/<int:temp_image_id>/", views.delete_temp_image, name="delete_temp_image"),
    path("reorder-temp-images/", views.reorder_temp_images, name="reorder_temp_images"),
    path("load-temp-images/", views.load_temp_images, name="load_temp_images"),
    path("cleanup-temp-images/", views.cleanup_temp_images, name="cleanup_temp_images"),
    path("reset-temp-images/", views.reset_temp_images, name="reset_temp_images"),
]
