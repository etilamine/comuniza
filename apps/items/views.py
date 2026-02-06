"""
Views for Items app.
"""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import models
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string

from apps.groups.models import Group
from apps.loans.models import Loan
from apps.messaging.models import Conversation
from apps.core.ultra_cache import get_ultimate_cache
from apps.core.rate_limiting import content_creation_rate_limit, strict_api_rate_limit

from .models import Item, ItemCategory, ItemImage, ItemWishlist, TempItemImage
from .forms import ItemForm
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

logger = logging.getLogger(__name__)


class ItemListView(ListView):
    """
    List all available items with filtering.
    """

    model = Item
    template_name = "items/item_list.html"
    context_object_name = "items"
    paginate_by = 24

    def get_queryset(self):
        # Generate cache key from request parameters
        cache_params = {
            'q': self.request.GET.get("q", ""),
            'category': self.request.GET.get("category", ""),
            'status': self.request.GET.get("status", ""),
            'group': self.request.GET.get("group", ""),
            'page': getattr(self, 'page', 1),  # Current page number
        }

        # Add user-specific context for group filtering
        if self.request.user.is_authenticated:
            cache_params['user_id'] = self.request.user.id

        cache_key = get_ultimate_cache().generate_cache_key('items_list_v2', **cache_params)

        def loader():
            queryset = (
                Item.objects.filter(
                    is_active=True,
                    identifier__isnull=False
                ).exclude(identifier='')
                .select_related("owner", "category")
                .prefetch_related("images", "groups")
            )

            # Search query
            search_query = self.request.GET.get("q")
            if search_query:
                queryset = queryset.filter(
                    Q(title__icontains=search_query)
                    | Q(description__icontains=search_query)
                    | Q(author__icontains=search_query)
                )

            # Filter by category
            category_id = self.request.GET.get("category")
            if category_id:
                queryset = queryset.filter(category_id=category_id)

            # Filter by status
            status = self.request.GET.get("status")
            if status:
                queryset = queryset.filter(status=status)

            # Filter by group (if user is authenticated)
            group_id = self.request.GET.get("group")
            if group_id and self.request.user.is_authenticated:
                queryset = queryset.filter(groups__id=group_id)

            # Filter by visibility
            if self.request.user.is_authenticated:
                # Show public items + restricted items where user is in groups + user's own items
                queryset = queryset.filter(
                    Q(visibility='public') |
                    Q(visibility='restricted', groups__members=self.request.user) |
                    Q(owner=self.request.user)
                ).distinct()
            else:
                # Anonymous users only see public items
                queryset = queryset.filter(visibility='public')

            return list(queryset.order_by("-created_at"))

        # Different TTL based on search complexity
        has_search = bool(self.request.GET.get("q"))
        has_filters = bool(self.request.GET.get("category") or self.request.GET.get("status") or self.request.GET.get("group"))

        if has_search:
            ttl = 300  # 5 minutes for search results (change frequently)
        elif has_filters:
            ttl = 600  # 10 minutes for filtered results
        else:
            ttl = 900  # 15 minutes for main listing

        cached_queryset = get_ultimate_cache().get(cache_key, loader_func=loader, ttl=ttl, segment='warm')

        # Filter out any items with invalid identifiers that might be in cached data
        cached_queryset = [item for item in cached_queryset if item.identifier and item.identifier.strip()]

        # Convert back to queryset-like behavior for pagination
        # Note: We return the cached list, Django's ListView will handle pagination
        return cached_queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = ItemCategory.objects.filter(is_active=True)

        # Get user's groups if authenticated
        if self.request.user.is_authenticated:
            context["user_groups"] = self.request.user.comuniza_groups.filter(
                is_active=True
            )

        return context


class ItemDetailView(DetailView):
    """
    Display item details.
    """

    model = Item
    template_name = "items/item_detail.html"
    context_object_name = "item"
    slug_field = "identifier"
    slug_url_kwarg = "identifier"

    def get_queryset(self):
        # For detail view, we don't cache the queryset directly since we need the object
        # But we'll cache the context data which contains the expensive queries
        return (
            Item.objects.filter(is_active=True)
            .select_related("owner", "owner__reputation", "category")
            .prefetch_related("images", "groups", "reviews")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = self.object

        # Generate cache key for item context - include user's group memberships for can_borrow accuracy
        if self.request.user.is_authenticated:
            user_groups = list(self.request.user.comuniza_groups.values_list('id', flat=True))
            cache_key = get_ultimate_cache().generate_cache_key(
                'item_detail_v3',
                item.id,
                user_id=self.request.user.id,
                user_groups_hash=hash(tuple(sorted(user_groups)))  # Include group membership in cache key
            )
        else:
            cache_key = get_ultimate_cache().generate_cache_key(
                'item_detail_v3',
                item.id,
                user_id='anonymous'
            )

        def loader():
            # Check if user can borrow this item
            if self.request.user.is_authenticated:
                can_borrow = item.can_borrow(self.request.user)
                # Get current loan for this item (active loans and items awaiting return confirmation)
                current_loan = Loan.objects.filter(
                    item=item,
                    status__in=['approved', 'active', 'borrower_returned']
                ).select_related('borrower', 'lender').first()
            else:
                can_borrow = False
                current_loan = None

            return {
                'can_borrow': can_borrow,
                'current_loan': current_loan,
                'item_id': item.id,
                'cached_at': timezone.now().isoformat()
            }

        # Cache item context for 10 minutes (reduced from 30 to ensure fresh can_borrow values)
        cached_context = get_ultimate_cache().get(cache_key, loader_func=loader, ttl=600, segment='warm')

        # Add cached context to template context
        context.update(cached_context)

        # Check for existing conversation about this item
        if self.request.user.is_authenticated and self.request.user != item.owner:
            logger.info(f"Checking conversations for user {self.request.user.username} and item owner {item.owner.username} about item {item.id}")
            # Find conversations that include both the current user and the item owner
            existing_conversation = Conversation.objects.filter(
                participants__in=[self.request.user, item.owner],
                related_item=item
            ).annotate(
                num_participants=models.Count('participants')
            ).filter(num_participants=2).first()

            logger.info(f"Found existing conversation: {existing_conversation}")
            context['existing_item_conversation'] = existing_conversation

        # Increment view count (do this asynchronously in production)
        # Note: This is not cached as it needs to happen every time
        Item.objects.filter(pk=item.pk).update(views_count=item.views_count + 1)

        # Invalidate item cache when view count changes significantly
        if item.views_count % 10 == 0:  # Every 10 views
            get_ultimate_cache().invalidate_pattern(f'item_detail:{item.id}:*')

        return context


class ItemCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new item.
    """

    model = Item
    form_class = ItemForm
    template_name = "items/item_form.html"

    @content_creation_rate_limit
    def post(self, request, *args, **kwargs):
        """Rate limited item creation"""
        return super().post(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Pass user to form for default visibility and groups handling
        form.user = self.request.user
        # Only show groups where user is a member
        form.fields["groups"].queryset = self.request.user.comuniza_groups.filter(
            is_active=True
        )
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = self.get_form()

        # Determine category for field ordering
        category_name = self.request.GET.get('category')
        if category_name:
            try:
                category = ItemCategory.objects.get(name=category_name, is_active=True)
                category_name = category.name
            except ItemCategory.DoesNotExist:
                category_name = None

        # Get field ordering from database for current category
        from apps.items.templatetags.item_tags import get_item_details_field_order
        item_details_field_order = get_item_details_field_order(category_name)

        # Get field ordering for ALL categories for dynamic JavaScript access
        all_categories = ItemCategory.objects.filter(is_active=True)
        all_field_orders = {}
        for category in all_categories:
            order = get_item_details_field_order(category.name)
            if order:  # Only include if there's a custom ordering
                all_field_orders[category.name] = order

        # Convert to JSON for JavaScript
        import json
        item_details_field_order_json = json.dumps(item_details_field_order)
        all_field_orders_json = json.dumps(all_field_orders)

        context.update({
            'form_config': {
                'category_configs': form.get_category_fields,
                'field_labels': form.get_field_labels,
                'field_help_text': form.get_field_help_text,
            },
            'item_details_field_order': item_details_field_order,
            'item_details_field_order_json': item_details_field_order_json,
            'all_field_orders_json': all_field_orders_json,
        })
        return context

    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.status = "available"
        response = super().form_valid(form)

        # Process temporary images uploaded via AJAX
        temp_image_ids = self.request.POST.get('temp_image_ids', '')
        if temp_image_ids:
            temp_ids = [int(id) for id in temp_image_ids.split(',') if id.isdigit()]

            # Move temp images to permanent item images
            for idx, temp_id in enumerate(temp_ids):
                try:
                    temp_image = TempItemImage.objects.get(
                        id=temp_id,
                        user=self.request.user
                    )

                    # Create permanent image from temp image
                    ItemImage.objects.create(
                        item=self.object,
                        image=temp_image.image,
                        order=idx,
                        is_primary=(idx == 0)  # First image is primary/cover
                    )

                    # Delete temp image after conversion
                    temp_image.delete()
                    logger.info(f"Converted temp image {temp_id} to permanent image for item {self.object.id}")

                except TempItemImage.DoesNotExist:
                    logger.warning(f"Temp image {temp_id} not found, skipping")
                    continue

        # Handle cover from ISBN lookup
        cover_url = self.request.POST.get('cover_url')
        if cover_url and not self.request.FILES.getlist("images"):
            try:
                from apps.books.services import BookCoverService
                success, message = BookCoverService.download_and_save_cover(cover_url, self.object)
                if success:
                    pass
            except Exception as e:
                pass

        # Handle image uploads
        images = self.request.FILES.getlist("images")
        for idx, image in enumerate(images):
            ItemImage.objects.create(
                item=self.object,
                image=image,
                is_primary=(idx == 0),
                order=idx,
            )

        # Invalidate relevant caches
        self._invalidate_item_caches()

        messages.success(
            self.request, f'Item "{self.object.title}" has been added successfully!'
        )
        return response

    def get_success_url(self):
        return reverse("item_detail", kwargs={"identifier": self.object.identifier})

    def _invalidate_item_caches(self):
        """Invalidate relevant caches when item is created/updated"""
        # Invalidate main item list cache (both v1 and v2)
        get_ultimate_cache().invalidate_pattern('items_list:*')
        get_ultimate_cache().invalidate_pattern('items_list_v2:*')

        # Invalidate user-specific caches
        if self.request.user.is_authenticated:
            get_ultimate_cache().invalidate_pattern(f'user_item_stats:{self.request.user.id}:*')

        # Invalidate item detail cache for this item (both v2 and v3)
        get_ultimate_cache().invalidate_pattern(f'item_detail:{self.object.id}:*')
        get_ultimate_cache().invalidate_pattern(f'item_detail_v2:{self.object.id}:*')
        get_ultimate_cache().invalidate_pattern(f'item_detail_v3:{self.object.id}:*')


class ItemUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Update an existing item (owner only).
    """

    model = Item
    form_class = ItemForm
    template_name = "items/item_form.html"
    slug_field = "identifier"
    slug_url_kwarg = "identifier"

    def test_func(self):
        item = self.get_object()
        return item.owner == self.request.user

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Pass user to form for groups handling
        form.user = self.request.user
        # Only show groups where user is a member
        form.fields["groups"].queryset = self.request.user.comuniza_groups.filter(
            is_active=True
        )
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = self.get_form()

        # Determine category for field ordering (from existing item)
        category_name = None
        if hasattr(self, 'object') and self.object and self.object.category:
            category_name = self.object.category.name

        # Get field ordering from database for current category
        from apps.items.templatetags.item_tags import get_item_details_field_order
        item_details_field_order = get_item_details_field_order(category_name)

        # Get field ordering for ALL categories for dynamic JavaScript access
        all_categories = ItemCategory.objects.filter(is_active=True)
        all_field_orders = {}
        for category in all_categories:
            order = get_item_details_field_order(category.name)
            if order:  # Only include if there's a custom ordering
                all_field_orders[category.name] = order

        # Convert to JSON for JavaScript
        import json
        item_details_field_order_json = json.dumps(item_details_field_order)
        all_field_orders_json = json.dumps(all_field_orders)

        context.update({
            'form_config': {
                'category_configs': form.get_category_fields,
                'field_labels': form.get_field_labels,
                'field_help_text': form.get_field_help_text,
            },
            'item_details_field_order': item_details_field_order,
            'item_details_field_order_json': item_details_field_order_json,
            'all_field_orders_json': all_field_orders_json,
        })
        return context

    def form_valid(self, form):
        # First save the item to get an ID
        response = super().form_valid(form)
        item = self.object

        # Check total image count (including newly uploaded ones)
        temp_image_ids_str = self.request.POST.get('temp_image_ids', '')
        temp_ids = [int(id) for id in temp_image_ids_str.split(',') if id.isdigit()] if temp_image_ids_str else []
        direct_uploads = len(self.request.FILES.getlist('images'))

        # Count existing images (excluding those marked for deletion)
        images_to_delete_str = self.request.POST.get('images_to_delete', '')
        deleted_ids = [int(id) for id in images_to_delete_str.split(',') if id.isdigit()] if images_to_delete_str else []
        existing_count = item.images.exclude(id__in=deleted_ids).count()

        total_images = existing_count + len(temp_ids) + direct_uploads
        if total_images > 8:
            messages.error(self.request, f'Maximum 8 images allowed. You are trying to save {total_images} images.')
            # Re-render the form with errors
            return self.form_invalid(form)

        # Process images marked for deletion
        images_to_delete = self.request.POST.get('images_to_delete', '')
        if images_to_delete:
            image_ids = [int(id) for id in images_to_delete.split(',') if id.isdigit()]

            # Delete marked images
            for image_id in image_ids:
                try:
                    image = ItemImage.objects.get(id=image_id, item=item)
                    # Check if this is the only image
                    if item.images.count() > 1:
                        image.delete()
                        logger.info(f"Deleted image {image_id} from item {item.id}")
                    else:
                        logger.warning(f"Cannot delete image {image_id} - it's the last image for item {item.id}")
                except ItemImage.DoesNotExist:
                    logger.warning(f"Image {image_id} not found for deletion")
                    continue

        # Process temporary images
        temp_image_ids_str = self.request.POST.get('temp_image_ids', '')
        temp_id_to_item_id_map = {}  # Track mapping of temp image IDs to ItemImage IDs
        if temp_image_ids_str:
            temp_ids = [int(id) for id in temp_image_ids_str.split(',') if id.isdigit()]

            # Move temp images to permanent item images
            # Order will be adjusted by the reordering logic that runs after this
            for idx, temp_id in enumerate(temp_ids):
                try:
                    temp_image = TempItemImage.objects.get(
                        id=temp_id,
                        user=self.request.user
                    )

                    # Create permanent image with temporary order
                    # This order will be updated by the reordering logic below
                    item_image = ItemImage.objects.create(
                        item=item,
                        image=temp_image.image,
                        order=idx,  # Temporary, will be reordered
                        is_primary=False  # Don't override primary image on update
                    )

                    # Map temp image ID to ItemImage ID for later reference
                    temp_id_to_item_id_map[temp_id] = item_image.id

                    # Delete temp image
                    temp_image.delete()

                except TempItemImage.DoesNotExist:
                    continue

        # Handle regular file uploads (fallback)
        if self.request.FILES.getlist('images'):
            images = self.request.FILES.getlist('images')
            for idx, image_file in enumerate(images):
                ItemImage.objects.create(
                    item=item,
                    image=image_file,
                    order=idx,
                    is_primary=(idx == 0 and not item.images.exists())
                )

        # Handle image reordering (both existing and newly uploaded temp images)
        # Use all_images_order which contains the complete reordered list
        all_images_order = self.request.POST.get("all_images_order", "")

        # If we have a complete order list, use it for all images
        if all_images_order:
            all_image_ids = [int(id) for id in all_images_order.split(',') if id.isdigit()]

            # Reorder all images based on their final position in the unified gallery
            for idx, image_id in enumerate(all_image_ids):
                try:
                    # Check if this is a temp image ID that we need to map
                    # If it's in our mapping, use the ItemImage ID instead
                    actual_image_id = temp_id_to_item_id_map.get(image_id, image_id)

                    ItemImage.objects.filter(id=actual_image_id, item=item).update(
                        order=idx,
                        is_primary=(idx == 0)
                    )
                except (ValueError, ItemImage.DoesNotExist):
                    pass  # Skip invalid IDs
        else:
            # Fallback: use image_order for backward compatibility
            image_order = self.request.POST.get("image_order", "")
            if image_order:
                existing_ids = [int(id) for id in image_order.split(',') if id.isdigit()]
                for idx, image_id in enumerate(existing_ids):
                    try:
                        ItemImage.objects.filter(id=image_id, item=item).update(
                            order=idx,
                            is_primary=(idx == 0)
                        )
                    except (ValueError, ItemImage.DoesNotExist):
                        pass  # Skip invalid IDs

        # Handle ISBN cover assignment
        use_isbn_cover = self.request.POST.get("use_isbn_cover") == "true"
        if use_isbn_cover and not self.request.FILES.getlist("images"):
            # Check if item has any images, if so shift them down
            existing_images = self.object.images.all().order_by('order')
            if existing_images.exists():
                # Shift all existing images down by 1
                for img in existing_images:
                    img.order += 1
                    img.is_primary = False
                    img.save()

            # Add ISBN cover as primary (order 0)
            cover_url = self.request.POST.get('cover_url')
            if cover_url:
                try:
                    from apps.books.services import BookCoverService
                    success, message = BookCoverService.download_and_save_cover(cover_url, self.object, order=0, is_primary=True)
                    if success:
                        pass
                except Exception as e:
                    pass

        # Handle new image uploads
        images = self.request.FILES.getlist("images")
        if images:
            # Get current max order
            max_order = (
                ItemImage.objects.filter(item=self.object).order_by("-order").first()
            )
            start_order = (max_order.order + 1) if max_order else 0

            for idx, image in enumerate(images):
                ItemImage.objects.create(
                    item=self.object,
                    image=image,
                    order=start_order + idx,
                    is_primary=(start_order == 0 and idx == 0 and not self.object.images.exists())
                )

        # Invalidate relevant caches
        self._invalidate_item_caches()

        messages.success(
            self.request, f'Item "{self.object.title}" has been updated successfully!'
        )
        return response

    def get_success_url(self):
        return reverse("item_detail", kwargs={"identifier": self.object.identifier})

    def _invalidate_item_caches(self):
        """Invalidate relevant caches when item is created/updated"""
        # Invalidate main item list cache (both v1 and v2)
        get_ultimate_cache().invalidate_pattern('items_list:*')
        get_ultimate_cache().invalidate_pattern('items_list_v2:*')

        # Invalidate user-specific caches
        if self.request.user.is_authenticated:
            get_ultimate_cache().invalidate_pattern(f'user_item_stats:{self.request.user.id}:*')

        # Invalidate item detail cache for this item (both v2 and v3)
        get_ultimate_cache().invalidate_pattern(f'item_detail:{self.object.id}:*')
        get_ultimate_cache().invalidate_pattern(f'item_detail_v2:{self.object.id}:*')
        get_ultimate_cache().invalidate_pattern(f'item_detail_v3:{self.object.id}:*')


class ItemDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Delete an item (owner only).
    """

    model = Item
    template_name = "items/item_confirm_delete.html"
    success_url = reverse_lazy("items:my_items")
    slug_field = "identifier"
    slug_url_kwarg = "identifier"

    def test_func(self):
        item = self.get_object()
        return item.owner == self.request.user

    def get(self, request, *args, **kwargs):
        """Check if item can be deleted or should be deactivated."""
        item = self.get_object()
        if item.current_borrower:
            # Item is currently borrowed, redirect to deactivate instead
            messages.warning(
                request,
                f'"{item.title}" is currently borrowed and cannot be deleted. You can deactivate it instead.'
            )
            return redirect("items:item_deactivate", identifier=item.identifier)
        return super().get(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        item = self.get_object()

        # Invalidate caches before deletion
        self._invalidate_item_caches_for_delete(item)

        messages.success(request, f'Item "{item.title}" has been deleted.')
        return super().delete(request, *args, **kwargs)

    def _invalidate_item_caches_for_delete(self, item):
        """Invalidate relevant caches when item is deleted"""
        # Invalidate main item list cache (both v1 and v2)
        get_ultimate_cache().invalidate_pattern('items_list:*')
        get_ultimate_cache().invalidate_pattern('items_list_v2:*')

        # Invalidate user-specific caches
        if self.request.user.is_authenticated:
            get_ultimate_cache().invalidate_pattern(f'user_item_stats:{self.request.user.id}:*')

        # Invalidate item detail cache for this item
        get_ultimate_cache().invalidate_pattern(f'item_detail:{item.id}:*')


class MyItemsView(LoginRequiredMixin, ListView):
    """
    List user's own items.
    """

    model = Item
    template_name = "items/my_items.html"
    context_object_name = "items"
    paginate_by = 24

    def get_queryset(self):
        return (
            Item.objects.filter(owner=self.request.user, is_active=True)
            .select_related("category")
            .prefetch_related("images", "groups")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        # Ensure object_list is available by calling get_queryset first
        if not hasattr(self, 'object_list'):
            self.object_list = self.get_queryset()

        context = super().get_context_data(**kwargs)

        # Generate cache key for user item stats
        cache_key = get_ultimate_cache().generate_cache_key('user_item_stats', self.request.user.id)

        def loader():
            # Active items stats
            active_items = Item.objects.filter(owner=self.request.user, is_active=True)
            stats = {
                "total_items": active_items.count(),
                "available_items": active_items.filter(status="available").count(),
                "borrowed_items": active_items.filter(status="borrowed").count(),
            }

            # Inactive items
            inactive_items = list(
                Item.objects.filter(owner=self.request.user, is_active=False)
                .select_related("category")
                .prefetch_related("images", "groups")
                .order_by("-updated_at")
            )

            return {
                'stats': stats,
                'inactive_items': inactive_items,
                'cached_at': timezone.now().isoformat()
            }

        # Cache user stats for 15 minutes
        cached_data = get_ultimate_cache().get(cache_key, loader_func=loader, ttl=900, segment='warm')

        # Add cached data to context
        context.update(cached_data['stats'])
        context["inactive_items"] = cached_data['inactive_items']

        return context


@login_required
def wishlist_view(request):
    """
    Display user's wishlist.
    """
    wishlist_items = (
        ItemWishlist.objects.filter(user=request.user)
        .select_related("item", "item__owner")
        .prefetch_related("item__images")
    )

    return render(
        request,
        "items/wishlist.html",
        {
            "wishlist_items": wishlist_items,
        },
    )


@login_required
def wishlist_add(request, identifier):
    """
    Add item to wishlist.
    """
    item = get_object_or_404(Item, identifier=identifier, is_active=True)

    if item.owner == request.user:
        messages.warning(request, "You cannot add your own item to wishlist.")
        return redirect("item_detail", identifier=identifier)

    wishlist_item, created = ItemWishlist.objects.get_or_create(
        user=request.user, item=item
    )

    if created:
        messages.success(request, f'"{item.title}" has been added to your wishlist.')
    else:
        messages.info(request, f'"{item.title}" is already in your wishlist.')

    return redirect("item_detail", identifier=identifier)


@login_required
def wishlist_remove(request, item_id):
    """
    Remove item from wishlist.
    """
    wishlist_item = get_object_or_404(ItemWishlist, id=item_id, user=request.user)
    item_title = wishlist_item.item.title
    wishlist_item.delete()

    messages.success(request, f'"{item_title}" has been removed from your wishlist.')
    return redirect("items:wishlist")


@login_required
def item_deactivate(request, identifier):
    """
    Deactivate an item (soft delete) instead of hard delete when it's loaned.
    """
    item = get_object_or_404(Item, identifier=identifier, owner=request.user)

    if request.method == 'POST':
        item.is_active = False
        item.save()

        # Invalidate caches
        get_ultimate_cache().invalidate_pattern('items_list:*')
        get_ultimate_cache().invalidate_pattern('items_list_v2:*')
        get_ultimate_cache().invalidate_pattern(f'user_item_stats:{request.user.id}:*')
        get_ultimate_cache().invalidate_pattern(f'item_detail:{item.id}:*')

        messages.success(request, f'Item "{item.title}" has been deactivated.')
        return redirect("items:my_items")

    # GET request - redirect to delete confirmation which will show deactivate option
    return redirect("item_delete", identifier=identifier)


@login_required
def item_reactivate(request, identifier):
    """
    Reactivate a deactivated item.
    """
    item = get_object_or_404(Item, identifier=identifier, owner=request.user, is_active=False)

    if request.method == 'POST':
        item.is_active = True
        item.save()

        # Invalidate caches
        get_ultimate_cache().invalidate_pattern('items_list:*')
        get_ultimate_cache().invalidate_pattern('items_list_v2:*')
        get_ultimate_cache().invalidate_pattern(f'user_item_stats:{request.user.id}:*')
        get_ultimate_cache().invalidate_pattern(f'item_detail:{item.id}:*')

        messages.success(request, f'Item "{item.title}" has been reactivated.')
        return redirect("items:my_items")

    return redirect("items:my_items")


@require_http_methods(["POST"])
@login_required
@strict_api_rate_limit
def delete_item_image(request, image_id):
    """
    Delete an item image (AJAX endpoint).
    """
    try:
        # Check if image exists and belongs to user
        try:
            image = ItemImage.objects.get(id=image_id, item__owner=request.user)
        except ItemImage.DoesNotExist:
            logger.warning(f"User {request.user.id} tried to delete non-existent image {image_id}")
            return JsonResponse({
                'success': False,
                'error': 'Image not found'
            }, status=404)

        if image.item.images.count() <= 1:
            return JsonResponse({
                'success': False,
                'error': 'Cannot delete the last image'
            }, status=400)

        image.delete()
        return JsonResponse({'success': True, 'message': 'Image deleted successfully'})
    except Exception as e:
        logger.error(f"Error deleting image {image_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to delete image'
        }, status=500)


@require_http_methods(["GET"])
def isbn_lookup(request):
    """
    AJAX endpoint to look up ISBN and return book metadata.
    """
    isbn = request.GET.get('isbn', '').strip()

    if not isbn:
        return JsonResponse({
            'success': False,
            'error': 'Invalid ISBN format'
        }, status=400)

    try:
        from apps.books.services import BookCoverService

        # Normalize ISBN
        clean_isbn = BookCoverService.normalize_isbn(isbn)

        if not clean_isbn:
            return JsonResponse({
                'success': False,
                'error': 'Invalid ISBN format'
            }, status=400)

        if not BookCoverService.is_valid_isbn(clean_isbn):
            return JsonResponse({
                'success': False,
                'error': 'Invalid ISBN format'
            }, status=400)

        metadata = BookCoverService.fetch_book_metadata(clean_isbn)

        if metadata:
            cover_url = BookCoverService.fetch_cover_url(clean_isbn, 'M')

            response_data = {
                'success': True,
                'metadata': metadata,
                'cover_url': cover_url,
                'message': f"Found: {metadata['title']}"
            }
        else:
            response_data = {
                'success': False,
                'error': 'No book found with this ISBN'
            }

    except Exception as e:
        response_data = {
            'success': False,
            'error': f"Lookup failed: {str(e)}"
        }

    return JsonResponse(response_data)


@require_http_methods(["POST"])
@login_required
def upload_temp_image(request):
    """
    HTMX endpoint for live image upload before item is saved.
    """
    if 'images' not in request.FILES:
        return HttpResponse(
            '<div class="alert alert-danger">No image selected</div>',
            status=400
        )

    image_file = request.FILES['images']

    # Validate image
    if not image_file.content_type.startswith('image/'):
        return HttpResponse(
            '<div class="alert alert-danger">File must be an image</div>',
            status=400
        )

    if image_file.size > 5 * 1024 * 1024:  # 5MB limit
        return HttpResponse(
            '<div class="alert alert-danger">Image must be smaller than 5MB</div>',
            status=400
        )

    # Get session key
    if not request.session.session_key:
        request.session.create()
        request.session.save()

    session_key = request.session.session_key or ''

    # Get max order from temp images in this session
    max_order_image = TempItemImage.objects.filter(
        user=request.user,
        session_key=session_key
    ).order_by('-order').first()

    new_order = (max_order_image.order + 1) if max_order_image else 0

    # Create temporary image
    temp_image = TempItemImage.objects.create(
        user=request.user,
        image=image_file,
        session_key=session_key,
        order=new_order
    )

    logger.info(f"Created temp image ID {temp_image.id} with session key {session_key} for user {request.user.id}")

    # Return HTML fragment for the uploaded image
    html = render_to_string('items/partials/temp_image.html', {
        'temp_image': temp_image,
        'request': request
    })

    return HttpResponse(html)


@require_http_methods(["POST"])
@login_required
def delete_temp_image(request, temp_image_id):
    """
    Delete a temporary image.
    """
    try:
        logger.info(f"Attempting to delete temp image {temp_image_id} for user {request.user.id}")

        # List all temp images for this user for debugging
        all_temp_images = TempItemImage.objects.filter(user=request.user).values_list('id', 'session_key')
        logger.info(f"All temp images for user {request.user.id}: {list(all_temp_images)}")

        temp_image = TempItemImage.objects.get(
            id=temp_image_id,
            user=request.user
        )

        logger.info(f"Found temp image {temp_image_id}, deleting... Session key: {temp_image.session_key}")

        # Delete the image file
        if temp_image.image:
            temp_image.image.delete()

        temp_image.delete()

        logger.info(f"Successfully deleted temp image {temp_image_id}")
        return JsonResponse({'success': True, 'message': 'Image deleted'})

    except TempItemImage.DoesNotExist:
        logger.warning(f"Temp image {temp_image_id} not found for user {request.user.id}")
        # List what we do have
        all_temp_images = TempItemImage.objects.filter(user=request.user).values_list('id')
        logger.warning(f"Available temp images: {list(all_temp_images)}")
        return JsonResponse({'success': False, 'error': 'Image not found'}, status=404)
    except Exception as e:
        logger.error(f"Error deleting temp image {temp_image_id}: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
@login_required
def reorder_temp_images(request):
    """
    Reorder temporary images.
    """
    image_order = request.POST.get('image_order', '')
    if not image_order:
        return JsonResponse({'success': False})

    order_ids = image_order.split(',')
    session_key = request.session.session_key or ''

    for idx, temp_image_id in enumerate(order_ids):
        try:
            TempItemImage.objects.filter(
                id=temp_image_id,
                user=request.user,
                session_key=session_key
            ).update(order=idx)
        except (ValueError, TempItemImage.DoesNotExist):
            pass

    return JsonResponse({'success': True})


@require_http_methods(["GET"])
@login_required
def load_temp_images(request):
    """
    Load existing temporary images for the current session.
    """
    session_key = request.session.session_key or ''

    temp_images = TempItemImage.objects.filter(
        user=request.user,
        session_key=session_key
    ).order_by('order')

    images_data = []
    for img in temp_images:
        images_data.append({
            'id': img.id,
            'image_url': img.image.url,
            'order': img.order
        })

    return JsonResponse({
        'success': True,
        'images': images_data
    })


@require_http_methods(["POST"])
@login_required
def cleanup_temp_images(request):
    """
    Clean up temporary images for the current user.
    Deletes all temp images for the current session.
    """
    session_key = request.session.session_key or ''

    deleted_count, _ = TempItemImage.objects.filter(
        user=request.user,
        session_key=session_key
    ).delete()

    return JsonResponse({
        'success': True,
        'deleted_count': deleted_count
    })


@require_http_methods(["POST"])
@login_required
def reset_temp_images(request):
    """
    Reset temporary images by cleaning up ALL old ones.
    Called when user loads the item form to start fresh.
    This ensures a clean slate for new uploads.
    """
    from django.utils import timezone

    # Delete ALL temp images for this user (both from current and previous sessions)
    # This ensures a completely clean state when loading the form
    deleted_count, _ = TempItemImage.objects.filter(
        user=request.user
    ).delete()

    logger.info(f"Cleaned up {deleted_count} temp images for user {request.user.id}")

    return JsonResponse({
        'success': True,
        'deleted_count': deleted_count
    })
