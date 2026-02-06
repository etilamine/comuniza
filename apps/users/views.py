"""
Views for Users app.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.db.models import Q


@login_required
def profile(request):
    """Display user profile."""
    user = request.user

    # Get public items
    public_items = user.owned_items.filter(visibility='public', is_active=True).order_by('-created_at')[:6]

    # Get public groups (groups that are not private)
    from apps.groups.models import Group
    public_groups = Group.objects.filter(
        members=user,
        privacy__in=['public', 'request'],
        is_active=True
    ).order_by('-created_at')[:6]

    context = {
        "user": user,
        "public_items": public_items,
        "public_groups": public_groups,
    }

    return render(request, "users/profile.html", context)


@login_required
def edit_profile(request):
    """Edit user profile."""
    from apps.loans.models import UserLoanSettings

    if request.method == "POST":
        user = request.user

        # Get or create loan settings for notification preferences
        loan_settings, created = UserLoanSettings.objects.get_or_create(user=user)

        user.first_name = request.POST.get("first_name", "")
        user.last_name = request.POST.get("last_name", "")
        user.phone = request.POST.get("phone", "")

        # Handle username change
        new_username = request.POST.get("new_username", "").strip()
        current_password = request.POST.get("current_password", "")

        if new_username and new_username != user.username:
            # Validate current password for sensitive changes
            if not current_password or not user.check_password(current_password):
                messages.error(request, "Current password is required and must be correct to change username.")
                loan_settings, _ = UserLoanSettings.objects.get_or_create(user=user)
                return render(request, "users/edit_profile.html", {"user": request.user, "loan_settings": loan_settings})

            # Validate new username
            if len(new_username) < 5 or len(new_username) > 50:
                messages.error(request, "Username must be 5-50 characters.")
                loan_settings, _ = UserLoanSettings.objects.get_or_create(user=user)
                return render(request, "users/edit_profile.html", {"user": request.user, "loan_settings": loan_settings})

            from django.contrib.auth import get_user_model
            User = get_user_model()
            if User.objects.filter(username=new_username).exclude(pk=user.pk).exists():
                messages.error(request, "This username is already taken.")
                loan_settings, _ = UserLoanSettings.objects.get_or_create(user=user)
                return render(request, "users/edit_profile.html", {"user": request.user, "loan_settings": loan_settings})

            # Generate confirmation token
            import secrets
            token = secrets.token_urlsafe(32)

            # Store in session for confirmation
            request.session['pending_username_change'] = {
                'new_username': new_username,
                'token': token,
                'user_id': user.id
            }

            # Send confirmation email
            from django.core.mail import send_mail
            from django.conf import settings

            confirmation_url = request.build_absolute_uri(
                f"/users/confirm-username/{token}/"
            )

            subject = "Confirm Username Change"
            message = f"""
            Hi {user.get_display_name()},

            You requested to change your username to: {new_username}

            Click the link below to confirm this change:
            {confirmation_url}

            If you didn't request this change, please ignore this email.

            Best,
            Comuniza Team
            """

            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                messages.info(request, f"A confirmation email has been sent to {user.email}. Please check your email to confirm the username change.")
            except Exception as e:
                messages.error(request, "Failed to send confirmation email. Please try again.")
                loan_settings, _ = UserLoanSettings.objects.get_or_create(user=user)
                return render(request, "users/edit_profile.html", {"user": request.user, "loan_settings": loan_settings})

            # Don't save other changes yet - wait for username confirmation
            return redirect("users:profile")

        # Update notification settings
        loan_settings.email_notifications = 'email_notifications' in request.POST
        loan_settings.message_notifications = 'message_notifications' in request.POST
        loan_settings.save()

        # Privacy settings
        user.profile_visibility = request.POST.get("profile_visibility", "private")
        user.email_visibility = request.POST.get("email_visibility", "private")
        user.activity_visibility = request.POST.get("activity_visibility", "private")

        # Handle avatar upload
        if request.FILES.get("avatar"):
            user.avatar = request.FILES["avatar"]

        user.save()
        messages.success(request, "Profile updated successfully!")
        return redirect("users:profile")

    # Get loan settings for template
    loan_settings, created = UserLoanSettings.objects.get_or_create(user=request.user)

    return render(request, "users/edit_profile.html", {"user": request.user, "loan_settings": loan_settings})


def confirm_username_change(request, token):
    """Confirm username change with token."""
    pending_change = request.session.get('pending_username_change')

    if not pending_change or pending_change.get('token') != token:
        messages.error(request, "Invalid or expired confirmation link.")
        return redirect("account_login")

    if str(request.user.id) != str(pending_change.get('user_id')):
        messages.error(request, "This confirmation link is for a different user.")
        return redirect("account_login")

    # Apply the username change
    new_username = pending_change['new_username']
    try:
        request.user.username = new_username
        request.user.save()

        # Clear the pending change
        del request.session['pending_username_change']

        messages.success(request, f"Your username has been changed to {new_username}.")
    except Exception as e:
        messages.error(request, "Failed to change username. It may already be taken.")

    return redirect("users:profile")


@login_required
def privacy_settings(request):
    """Privacy settings view."""
    if request.method == "POST":
        user = request.user

        # Update privacy settings
        user.profile_visibility = request.POST.get("profile_visibility", user.profile_visibility)
        user.groups_visibility = request.POST.get("groups_visibility", user.groups_visibility)
        user.location_visibility = request.POST.get("location_visibility", user.location_visibility)
        user.default_item_visibility = request.POST.get("default_item_visibility", user.default_item_visibility)

        user.save()
        messages.success(request, "Privacy settings updated successfully.")

    return render(request, "users/privacy_settings.html", {"user": request.user})

@login_required
def security_settings(request):
    """Manage security settings including 2FA."""
    # This is a stub for future 2FA implementation
    # You can add django-allauth-2fa or implement custom 2FA here
    return render(
        request,
        "users/security.html",
        {
            "user": request.user,
            "has_2fa": False,  # Note: 2FA not yet implemented - this is a stub for future implementation
        },
    )


@login_required
def user_search_api(request):
    """API endpoint for searching users by username only (used by messaging autocomplete)."""
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({'success': True, 'users': []})

    # SECURITY: Reject queries containing '@' to prevent email enumeration attacks
    # Usernames should never contain '@' symbols
    if '@' in query:
        return JsonResponse({'success': True, 'users': []})

    User = get_user_model()
    # Only search by username - do NOT search email, first_name, or last_name
    # to prevent leaking personal information
    users = User.objects.filter(
        username__icontains=query,
        is_active=True
    ).exclude(
        id=request.user.id  # Don't include current user
    ).order_by('username')[:10]  # Limit results

    user_data = []
    for user in users:
        user_data.append({
            'username': user.username,
            'display_name': user.get_display_name(),
            'avatar': user.avatar.url if user.avatar else None,
            # NOTE: email is intentionally NOT included to prevent information leakage
        })

    return JsonResponse({
        'success': True,
        'users': user_data
    })
