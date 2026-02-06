import uuid
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.crypto import get_random_string
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema


from .forms import GroupCreateForm, GroupInvitationForm
from .models import Group, GroupInvitation, GroupMembership

from django.contrib.auth import get_user_model
User = get_user_model()

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.http import JsonResponse
from django.db.models import Count

@extend_schema(
    description="Get group locations for map display",
    responses={200: {"type": "object", "properties": {"locations": {"type": "array"}}}}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def group_locations_api(request):
    """
    API endpoint that returns group locations for map.
    Returns aggregated data by city to protect privacy.
    Public endpoint - no authentication required for map functionality.
    """
    try:
        # Modify the query to be more lenient
        locations = (
            Group.objects.filter(is_active=True)
            .values("city", "state", "country", "latitude", "longitude")
            .annotate(group_count=Count("id"))
        )

        map_data = []
        for loc in locations:
            map_data.append({
                "city": loc["city"] or "Unknown",
                "state": loc["state"] or "",
                "country": loc["country"],
                "latitude": float(loc["latitude"] or 0),
                "longitude": float(loc["longitude"] or 0),
                "group_count": loc["group_count"],
                "display_name": f"{loc['city'] or 'Unknown'}, {loc['state'] or loc['country']}",
            })

        return JsonResponse({"locations": map_data})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# Add a debug view to help diagnose routing
@extend_schema(
    description="Debug endpoint for groups API",
    responses={200: {"type": "object"}}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def debug_groups_url(request):
    """
    Debugging endpoint to verify URL routing
    """
    return JsonResponse({
        "message": "Groups API URL is working!",
        "method": request.method,
        "path": request.path
    })


def geocode_location(city, state, country):
    """
    Geocode a location using Nominatim (OpenStreetMap) API.
    Returns dict with 'lat' and 'lng' keys, or None if geocoding fails.
    """
    import requests
    import time

    # Build location query
    query_parts = [city]
    if state:
        query_parts.append(state)
    query_parts.append(country)
    query = ', '.join(query_parts)

    try:
        # Use Nominatim API (OpenStreetMap)
        url = 'https://nominatim.openstreetmap.org/search'
        params = {
            'q': query,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1,
            'dedupe': 1
        }
        headers = {
            'User-Agent': 'Comuniza/1.0 (contact@comuniza.org)'  # Required by Nominatim
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        if data and len(data) > 0:
            location = data[0]
            return {
                'lat': float(location['lat']),
                'lng': float(location['lon'])
            }

    except (requests.RequestException, ValueError, KeyError) as e:
        pass

    return None


def index(request):
    """List all groups."""
    # Get public groups and groups where user is a member
    if request.user.is_authenticated:
        # Show public groups + groups where user is member (including private groups user belongs to)
        groups = Group.objects.filter(
            Q(privacy='public') | Q(members=request.user),
            is_active=True
        ).distinct().select_related('owner').prefetch_related('members')
    else:
        # Show only public groups for anonymous users
        groups = Group.objects.filter(privacy='public', is_active=True).select_related('owner').prefetch_related('members')

    # Get user's groups for quick access
    user_groups = []
    if request.user.is_authenticated:
        user_groups = request.user.comuniza_groups.filter(is_active=True)

    context = {
        'groups': groups,
        'user_groups': user_groups,
        'total_groups': groups.count(),
    }

    return render(request, "groups/group_list.html", context)


@login_required
def create_group(request):
    """Create a new group."""
    if request.method == 'POST':
        form = GroupCreateForm(request.POST, request.FILES)
        if form.is_valid():
            group = form.save(commit=False)
            group.owner = request.user

            # Generate slug from name
            import uuid
            from django.utils.text import slugify
            base_slug = slugify(group.name)
            slug = base_slug
            counter = 1

            # Ensure unique slug
            while Group.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            group.slug = slug
            # Geocode the location to get coordinates
            coordinates = geocode_location(group.city, group.state, group.country)
            if coordinates:
                group.latitude = coordinates['lat']
                group.longitude = coordinates['lng']

            group.save()

            # Add owner as admin member
            from .models import GroupMembership
            GroupMembership.objects.create(
                group=group,
                user=request.user,
                role='admin',
                status='active'
            )

            # Clear cache for map locations
            from apps.core.ultra_cache import get_ultimate_cache
            cache = get_ultimate_cache()
            cache_key = cache.generate_cache_key('group_locations_api')
            cache.delete(cache_key)

            return redirect('groups:detail', slug=group.slug)
    else:
        form = GroupCreateForm()

    return render(request, 'groups/group_form.html', {
        'form': form,
        'title': 'Create New Group'
    })

def group_detail(request, slug):
    """Display group details."""
    group = get_object_or_404(Group, slug=slug, is_active=True)

    # Check if user is member
    is_member = group.is_member(request.user) if request.user.is_authenticated else False
    is_admin = group.is_admin(request.user) if request.user.is_authenticated else False

    # Check privacy settings
    if group.privacy == 'private':
        # Private groups: only members can view
        if not is_member:
            if request.user.is_authenticated:
                # Check if user has a pending invitation
                has_pending_invitation = group.invitations.filter(
                    email=request.user.email,
                    status='pending'
                ).exists()

                if not has_pending_invitation:
                    messages.warning(request, f"{group.name} is a private group. You need an invitation to join.")
                    return redirect('groups:list')
            else:
                # Anonymous users cannot see private groups
                return redirect('groups:list')

    # Get group stats
    member_count = group.member_count
    item_count = group.item_count

    # Get recent items (only show items to members)
    if is_member:
        recent_items = group.items.filter(is_active=True).select_related('owner', 'category').prefetch_related('images')[:6]
    else:
        recent_items = []

    context = {
        'group': group,
        'is_member': is_member,
        'is_admin': is_admin,
        'member_count': member_count,
        'item_count': item_count,
        'recent_items': recent_items,
    }

    return render(request, 'groups/group_detail.html', context)


@login_required
def join_group(request, slug):
    """Join a group or request to join."""
    group = get_object_or_404(Group, slug=slug, is_active=True)

    # Check if user is already a member
    if group.is_member(request.user):
        messages.info(request, f"You are already a member of {group.name}.")
        return redirect('groups:detail', slug=group.slug)

    # Handle different privacy levels
    if group.privacy == 'private':
        messages.warning(request, f"{group.name} is a private group. Membership is by invitation only.")
        return redirect('groups:detail', slug=group.slug)

    elif group.privacy == 'public':
        # Create active membership immediately
        membership, created = GroupMembership.objects.get_or_create(
            group=group,
            user=request.user,
            defaults={
                'status': 'active',
                'role': 'member'
            }
        )

        if created:
            messages.success(request, f"Welcome to {group.name}!")
            # Clear relevant caches
            from apps.core.ultra_cache import get_ultimate_cache
            cache = get_ultimate_cache()
            cache.invalidate_pattern(f'user_groups:{request.user.id}:*')
            cache.invalidate_pattern('groups_list:*')
        else:
            # Membership exists but might be pending - activate it
            if membership.status == 'pending':
                membership.status = 'active'
                membership.save()
                messages.success(request, f"Your request to join {group.name} has been approved!")
            else:
                messages.info(request, f"You are already a member of {group.name}.")

    elif group.privacy == 'request':
        # Create pending membership request
        membership, created = GroupMembership.objects.get_or_create(
            group=group,
            user=request.user,
            defaults={
                'status': 'pending',
                'role': 'member'
            }
        )

        if created:
            messages.success(request, f"Your request to join {group.name} has been sent. You'll be notified when approved.")
            # Note: Notification to group admins not yet implemented
        else:
            if membership.status == 'pending':
                messages.info(request, f"You've already requested to join {group.name}. Please wait for approval.")
            elif membership.status == 'active':
                messages.info(request, f"You are already a member of {group.name}.")
            else:
                messages.warning(request, f"Your request to join {group.name} was denied.")

    return redirect('groups:detail', slug=group.slug)


@login_required
def leave_group(request, slug):
    return HttpResponse(f"Leave group {slug} - Coming soon!")


def accept_invitation(request, token):
    """Accept a group invitation."""
    invitation = get_object_or_404(
        GroupInvitation,
        token=token,
        status='pending'
    )

    # Check if invitation has expired
    if invitation.is_expired():
        invitation.status = 'expired'
        invitation.save()
        messages.error(request, "This invitation has expired.")
        return redirect('home')

    # If user is not authenticated, redirect to login with next parameter
    if not request.user.is_authenticated:
        login_url = f"/accounts/login/?next=/groups/invite/{token}/"
        return redirect(login_url)

    # Check if user email matches invitation email
    if request.user.email != invitation.email:
        messages.error(request, "This invitation is not for your email address.")
        return redirect('home')

    # Check if user is already a member
    if invitation.group.is_member(request.user):
        messages.info(request, "You are already a member of this group.")
        return redirect('groups:detail', slug=invitation.group.slug)

    if request.method == 'POST':
        if 'accept' in request.POST:
            # Accept invitation
            from .models import GroupMembership
            GroupMembership.objects.create(
                group=invitation.group,
                user=request.user,
                status='active'
            )

            invitation.status = 'accepted'
            invitation.responded_at = timezone.now()
            invitation.save()

            messages.success(request, f"Welcome to {invitation.group.name}!")
            return redirect('groups:detail', slug=invitation.group.slug)

        elif 'decline' in request.POST:
            # Decline invitation
            invitation.status = 'declined'
            invitation.responded_at = timezone.now()
            invitation.save()

            messages.info(request, "Invitation declined.")
            return redirect('home')

    context = {
        'invitation': invitation,
        'group': invitation.group,
    }

    return render(request, 'groups/accept_invitation.html', context)

@extend_schema(
    description="Search users by username",
    responses={200: {"type": "object", "properties": {"success": {"type": "boolean"}, "users": {"type": "array"}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_users_api(request):
    """API endpoint for searching users by username only.
    Protected endpoint - requires authentication for user search functionality."""
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({'success': True, 'users': []})

    # SECURITY: Reject queries containing '@' to prevent email enumeration attacks
    # Usernames should never contain '@' symbols
    if '@' in query:
        return JsonResponse({'success': True, 'users': []})

    # Search by username only (case-insensitive)
    # Do NOT search by email to prevent email address leakage
    users = User.objects.filter(
        username__icontains=query,
        is_active=True
    ).exclude(
        id=request.user.id  # Don't include current user
    ).order_by('username')[:10]  # Limit results

    # Format results (without email for privacy)
    results = []
    for user in users:
        results.append({
            'username': user.username,
            'display_name': user.get_display_name(),
            'avatar': user.avatar.url if user.avatar else None,
        })

    return JsonResponse({'success': True, 'users': results})

@login_required
def manage_group(request, slug):
    """Manage group members and pending requests."""
    group = get_object_or_404(Group, slug=slug, is_active=True)

    # Check if user is group admin
    if not group.is_admin(request.user):
        raise PermissionDenied("Only group administrators can manage the group.")

    # Handle invitation form submission
    if request.method == 'POST' and 'invite_user' in request.POST:
        invitation_form = GroupInvitationForm(group, request.POST)
        if invitation_form.is_valid():
            recipient_type = invitation_form.cleaned_data.get('recipient_type')
            email = invitation_form.cleaned_data['email']
            user = invitation_form.cleaned_data.get('user')
            message = invitation_form.cleaned_data.get('message', '')

            # Create invitation
            invitation = GroupInvitation.objects.create(
                group=group,
                email=email,
                invited_by=request.user,
                message=message,
                token=get_random_string(32),
                expires_at=timezone.now() + timezone.timedelta(days=7)  # 7 days expiry
            )

            # Send appropriate invitation based on recipient type
            if recipient_type == 'user' and user:
                # Registered user - send direct invitation
                invitation_url = request.build_absolute_uri(
                    f'/groups/invite/{invitation.token}/'
                )
                # Note: Email notification to invited user not yet implemented
                messages.success(request, f"Invitation sent to {user.get_display_name()}")
            else:
                # Unregistered user - send signup invitation
                signup_url = request.build_absolute_uri(
                    f'/groups/invite/{invitation.token}/'
                )
                # Note: Email notification for signup invitation not yet implemented
                messages.success(request, f"Signup invitation sent to {email}")

            return redirect('groups:manage', slug=group.slug)
    else:
        invitation_form = GroupInvitationForm(group)

    # Handle invitation cancellation
    if request.method == 'POST' and 'cancel_invitation' in request.POST:
        invitation_id = request.POST.get('invitation_id')
        try:
            invitation = GroupInvitation.objects.get(
                id=invitation_id,
                group=group,
                invited_by=request.user,
                status='pending'
            )
            invitation.status = 'expired'
            invitation.save()
            messages.success(request, "Invitation cancelled successfully.")
        except GroupInvitation.DoesNotExist:
            messages.error(request, "Invitation not found.")
        return redirect('groups:manage', slug=group.slug)

    # Handle member management actions
    if request.method == 'POST':
        if 'make_admin' in request.POST:
            user_id = request.POST.get('make_admin')
            try:
                membership = group.memberships.get(user_id=user_id, status='active')
                if membership.user != group.owner:  # Can't change owner
                    membership.role = 'admin'
                    membership.save()
                    messages.success(request, f"{membership.user.get_display_name} is now an admin.")
            except group.memberships.model.DoesNotExist:
                messages.error(request, "Member not found.")
            return redirect('groups:manage', slug=group.slug)

        elif 'remove_admin' in request.POST:
            user_id = request.POST.get('remove_admin')
            try:
                membership = group.memberships.get(user_id=user_id, status='active')
                if membership.user != group.owner:  # Can't change owner
                    membership.role = 'member'
                    membership.save()
                    messages.success(request, f"{membership.user.get_display_name} is no longer an admin.")
            except group.memberships.model.DoesNotExist:
                messages.error(request, "Member not found.")
            return redirect('groups:manage', slug=group.slug)

        elif 'remove_member' in request.POST:
            user_id = request.POST.get('remove_member')
            try:
                membership = group.memberships.get(user_id=user_id, status='active')
                if membership.user != group.owner:  # Can't remove owner
                    membership.delete()
                    messages.success(request, f"{membership.user.get_display_name} has been removed from the group.")
            except group.memberships.model.DoesNotExist:
                messages.error(request, "Member not found.")
            return redirect('groups:manage', slug=group.slug)

        elif 'approve_member' in request.POST:
            user_id = request.POST.get('approve_member')
            try:
                membership = group.memberships.get(user_id=user_id, status='pending')
                membership.status = 'active'
                membership.save()
                messages.success(request, f"{membership.user.get_display_name} has been approved as a member.")
            except group.memberships.model.DoesNotExist:
                messages.error(request, "Member not found.")
            return redirect('groups:manage', slug=group.slug)

        elif 'reject_member' in request.POST:
            user_id = request.POST.get('reject_member')
            try:
                membership = group.memberships.get(user_id=user_id, status='pending')
                membership.delete()
                messages.success(request, f"Membership request for {membership.user.get_display_name} has been rejected.")
            except group.memberships.model.DoesNotExist:
                messages.error(request, "Member not found.")
            return redirect('groups:manage', slug=group.slug)

    # Get members
    members = group.memberships.filter(status='active').select_related('user')
    pending_members = group.memberships.filter(status='pending').select_related('user')

    # Get pending invitations
    pending_invitations = group.invitations.filter(status='pending').select_related('invited_by')

    # Get pending join requests (for request-based groups)
    pending_requests = []
    if group.privacy == 'request':
        # This would need a separate model for join requests
        # For now, we'll show pending memberships
        pass

    context = {
        'group': group,
        'members': members,
        'pending_members': pending_members,
        'pending_invitations': pending_invitations,
        'pending_requests': pending_requests,
        'member_count': members.count(),
        'pending_count': pending_members.count(),
        'invitation_count': pending_invitations.count(),
        'invitation_form': invitation_form,
    }

    return render(request, 'groups/manage_group.html', context)


@login_required
def group_settings(request, slug):
    """Edit group settings."""
    group = get_object_or_404(Group, slug=slug, is_active=True)

    # Check if user is group admin
    if not group.is_admin(request.user):
        raise PermissionDenied("Only group administrators can edit group settings.")

    if request.method == 'POST':
        # Check if this is a delete action
        if 'delete_group' in request.POST:
            if group.owner != request.user:
                raise PermissionDenied("Only the group owner can delete the group.")

            # Soft delete by setting is_active to False
            group.is_active = False
            group.save()

            # Clear cache for map locations
            from apps.core.ultra_cache import get_ultimate_cache
            cache = get_ultimate_cache()
            cache.invalidate_pattern('group_locations:*')
            cache.invalidate_pattern('groups_list:*')

            messages.success(request, f"Group '{group.name}' has been deleted.")
            return redirect('groups:list')

        # Handle form submission for group settings
        group.name = request.POST.get('name', group.name)
        group.description = request.POST.get('description', group.description)
        group.privacy = request.POST.get('privacy', group.privacy)
        group.city = request.POST.get('city', group.city)
        group.state = request.POST.get('state', group.state)
        group.country = request.POST.get('country', group.country)
        group.allow_member_invites = request.POST.get('allow_member_invites') == 'on'
        group.require_approval_for_items = request.POST.get('require_approval_for_items') == 'on'
        group.loan_visibility = request.POST.get('loan_visibility', group.loan_visibility)

        # Handle image upload
        if request.FILES.get('image'):
            group.image = request.FILES['image']

        # Geocode the location if it changed
        coordinates = geocode_location(group.city, group.state, group.country)
        if coordinates:
            group.latitude = coordinates['lat']
            group.longitude = coordinates['lng']

        group.save()

        # Clear cache for map locations
        from apps.core.ultra_cache import get_ultimate_cache
        cache = get_ultimate_cache()
        cache_key = cache.generate_cache_key('group_locations_api')
        cache.delete(cache_key)

        messages.success(request, "Group settings updated successfully!")
        return redirect('groups:detail', slug=group.slug)

    context = {
        'group': group,
    }

    return render(request, 'groups/group_settings.html', context)

@extend_schema(
    description="Debug endpoint to check all group data",
    responses={200: {"type": "object", "properties": {"groups": {"type": "array"}}}}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def debug_groups_api(request):
    """
    Debugging endpoint to check group data
    """
    try:
        groups = Group.objects.all()
        group_data = []
        for group in groups:
            group_data.append({
                "id": group.id,
                "name": group.name,
                "city": group.city,
                "state": group.state,
                "country": group.country,
                "latitude": str(group.latitude),
                "longitude": str(group.longitude),
                "is_active": group.is_active
            })

        return JsonResponse({"groups": group_data})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
