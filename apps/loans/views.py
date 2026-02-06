"""
Views for Loans app.
"""

from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import Exists, OuterRef, Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import DetailView
from django.utils.translation import gettext_lazy as _

from apps.core.ultra_cache import get_ultimate_cache
from apps.items.models import Item
from apps.messaging.models import Conversation

from .models import Loan, LoanReview, UserLoanSettings, GroupLoanSettings
from .forms import LoanRequestForm, LoanReviewForm, ExtensionRequestForm, LoanActionForm
from .permissions import LoanParticipantMixin, LenderOnlyMixin, BorrowerOnlyMixin, get_visible_loans


@login_required
def my_loans(request):
    """Display user's loans (borrowed and lent)."""
    # Generate cache key for user loans context
    cache_key = get_ultimate_cache().generate_cache_key('my_loans_context', request.user.id)
    
    def loader():
        # Get user's loans with privacy filtering
        visible_loans = get_visible_loans(request.user)

        # Categorize loans
        valid_loans = visible_loans

        # Role-based categorization
        pending_requests = list(valid_loans.filter(borrower=request.user, status='requested').select_related('item', 'lender'))
        needs_approval = list(valid_loans.filter(lender=request.user, status='requested').select_related('item', 'borrower'))

        # Separate approved (waiting for pickup) from active (currently borrowing)
        waiting_pickup = list(valid_loans.filter(
            borrower=request.user,
            status='approved'
        ).select_related('item', 'borrower', 'lender'))

        borrowing_loans = list(valid_loans.filter(
            borrower=request.user,
            status='active'
        ).select_related('item', 'borrower', 'lender'))

        approved_loans = list(valid_loans.filter(
            lender=request.user,
            status='approved'
        ).select_related('item', 'borrower', 'lender'))

        # Items returned by borrower, waiting for lender confirmation
        awaiting_return_confirmation = list(valid_loans.filter(
            lender=request.user,
            status='borrower_returned'
        ).select_related('item', 'borrower', 'lender'))

        lending_loans = list(valid_loans.filter(
            lender=request.user,
            status='active'
        ).select_related('item', 'borrower', 'lender'))

        # Add rejected loans (visible to both parties)
        rejected_loans = list(valid_loans.filter(
            Q(borrower=request.user) | Q(lender=request.user),
            status='rejected'
        ).select_related('item', 'borrower', 'lender'))

        completed_loans = list(valid_loans.filter(status='returned').annotate(
            user_has_reviewed=Exists(
                LoanReview.objects.filter(
                    loan=OuterRef('pk'),
                    reviewer=request.user
                )
            )
        ).select_related('item', 'borrower', 'lender'))

        # Build conversation URL mapping for all loans
        from apps.messaging.models import Conversation
        all_loans = pending_requests + needs_approval + waiting_pickup + borrowing_loans + approved_loans + lending_loans + rejected_loans + completed_loans
        all_loan_ids = [loan.id for loan in all_loans if loan.id]
        all_other_users = {}
        
        for loan in all_loans:
            if loan.id:
                other_user = loan.lender if loan.borrower == request.user else loan.borrower
                all_other_users[loan.id] = other_user
        
        conversation_urls = {}
        if all_loan_ids:
            existing_conversations = Conversation.objects.filter(
                related_loan__in=all_loan_ids
            ).prefetch_related('participants')
            
            for conv in existing_conversations:
                if conv.related_loan and conv.related_loan.id:
                    loan_id = conv.related_loan.id
                    conversation_urls[loan_id] = reverse('messaging:conversation_detail', args=[conv.id])
        
        # Helper function to get conversation URL
        def get_conversation_url(loan):
            if not loan.id:
                return '#'
            if loan.id in conversation_urls:
                return conversation_urls[loan.id]
            other_user = all_other_users.get(loan.id)
            if other_user:
                return reverse('messaging:start_conversation_loan', args=[other_user.username, loan.id])
            return '#'
        
        # Add conversation URL to each loan
        for loan in pending_requests:
            loan.conversation_url = get_conversation_url(loan)
        for loan in needs_approval:
            loan.conversation_url = get_conversation_url(loan)
        for loan in waiting_pickup:
            loan.conversation_url = get_conversation_url(loan)
        for loan in borrowing_loans:
            loan.conversation_url = get_conversation_url(loan)
        for loan in approved_loans:
            loan.conversation_url = get_conversation_url(loan)
        for loan in lending_loans:
            loan.conversation_url = get_conversation_url(loan)
        for loan in rejected_loans:
            loan.conversation_url = get_conversation_url(loan)
        for loan in completed_loans:
            loan.conversation_url = get_conversation_url(loan)

        # Calculate statistics
        borrowing_count = len(borrowing_loans)
        lending_count = len(lending_loans)
        your_requests_count = len(pending_requests)
        needs_approval_count = len(needs_approval)
        waiting_pickup_count = len(waiting_pickup)
        approved_count = len(approved_loans)
        awaiting_return_confirmation_count = len(awaiting_return_confirmation)
        rejected_count = len(rejected_loans)

        return {
            'borrowing_count': borrowing_count,
            'lending_count': lending_count,
            'your_requests_count': your_requests_count,
            'needs_approval_count': needs_approval_count,
            'waiting_pickup_count': waiting_pickup_count,
            'approved_count': approved_count,
            'awaiting_return_confirmation_count': awaiting_return_confirmation_count,
            'rejected_count': rejected_count,
            'borrowing_loans': borrowing_loans,
            'lending_loans': lending_loans,
            'completed_loans': completed_loans,
            'pending_requests': pending_requests,
            'needs_approval': needs_approval,
            'waiting_pickup': waiting_pickup,
            'approved_loans': approved_loans,
            'awaiting_return_confirmation': awaiting_return_confirmation,
            'rejected_loans': rejected_loans,
        }
    
    # Cache loan context for 10 minutes
    cached_context = get_ultimate_cache().get(cache_key, loader_func=loader, ttl=600, segment='warm')
    
    return render(request, "loans/my_loans.html", cached_context)


class LoanDetailView(LoanParticipantMixin, DetailView):
    """
    Detail view for a specific loan with privacy controls.
    """
    model = Loan
    template_name = 'loans/loan_detail.html'
    context_object_name = 'loan'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        loan = self.get_object()
        
        # Add form context based on loan status and user role
        user = self.request.user
        
        if loan.status == 'requested' and loan.lender == user:
            context['action_form'] = LoanActionForm(user, loan, initial={'action': 'approve'})
        
        # Borrower actions - differentiate between approved and active
        if loan.status == 'approved' and loan.borrower == user:
            context['action_form'] = LoanActionForm(user, loan, initial={'action': 'mark_active'})
        elif loan.status == 'active' and loan.borrower == user:
            context['action_form'] = LoanActionForm(user, loan, initial={'action': 'return'})
        
        # Lender can cancel approved or active loans
        if loan.status in ['approved', 'active'] and loan.lender == user:
            context['lender_action_form'] = LoanActionForm(user, loan, initial={'action': 'cancel'})
        
        if loan.status == 'returned':
            # Check if user can review
            if not LoanReview.objects.filter(loan=loan, reviewer=user).exists():
                context['review_form'] = LoanReviewForm(user, loan)
        
        # Add extension form if applicable
        if loan.status in ['approved', 'active'] and loan.borrower == user:
            if not loan.extension_requested:
                context['extension_form'] = ExtensionRequestForm(user, loan)

        # Check for existing conversation about this loan
        if user.is_authenticated:
            # Determine who the user should message (lender if user is borrower, borrower if user is lender)
            other_user = loan.lender if user == loan.borrower else loan.borrower
            if user != other_user:
                existing_conversation = Conversation.objects.filter(
                    participants__in=[user, other_user],
                    related_loan=loan
                ).annotate(
                    num_participants=models.Count('participants')
                ).filter(num_participants=2).first()

                context['existing_loan_conversation'] = existing_conversation

        return context


@login_required
def request_loan(request, identifier):
    """Request to borrow an item."""
    item = get_object_or_404(Item, identifier=identifier)
    
    # Check if user can borrow this item
    if not item.can_borrow(request.user):
        messages.error(request, _("You cannot borrow this item."))
        return redirect('item_detail', identifier=identifier)
    
    if request.method == 'POST':
        form = LoanRequestForm(request.user, item, request.POST)
        if form.is_valid():
            # Create loan with user's settings
            loan = form.save(commit=False)
            loan.item = item
            loan.borrower = request.user
            
            # Apply user's loan settings
            user_settings = request.user.loan_settings
            group_settings = None
            
            if loan.group:
                group_settings = GroupLoanSettings.objects.filter(
                    user=request.user,
                    group=loan.group
                ).first()
            
            # Set privacy and other settings
            if group_settings:
                loan.privacy = group_settings.get_effective_privacy()
            else:
                loan.privacy = user_settings.default_loan_privacy
            
            loan.save()

            # Invalidate my_loans cache for both users
            get_ultimate_cache().invalidate_pattern(f'my_loans_context:{loan.borrower.id}:*')
            get_ultimate_cache().invalidate_pattern(f'my_loans_context:{loan.lender.id}:*')

            messages.success(request, _("Loan request sent successfully!"))
            return redirect('loans:loan_detail', pk=loan.pk)
    else:
        form = LoanRequestForm(request.user, item)
    
    return render(request, 'loans/loan_request_form.html', {
        'form': form,
        'item': item,
    })


@login_required
def approve_loan(request, loan_id):
    """Approve a loan request."""
    loan = get_object_or_404(Loan, pk=loan_id)

    if loan.lender != request.user:
        raise PermissionDenied("Only lender can approve loans.")

    if loan.status != 'requested':
        messages.error(request, _("This loan cannot be approved."))
        return redirect('loans:loan_detail', pk=loan.pk)

    if request.method == 'POST':
        form = LoanActionForm(request.user, loan, request.POST)
        if form.is_valid() and form.cleaned_data['action'] == 'approve':
            loan = form.save()

            # Invalidate item detail caches after loan approval
            get_ultimate_cache().invalidate_pattern(f'item_detail:*:{loan.item.id}:*')
            get_ultimate_cache().invalidate_pattern(f'item_detail_v2:{loan.item.id}:*')
            get_ultimate_cache().invalidate_pattern(f'item_detail_v3:{loan.item.id}:*')

            # Invalidate my_loans cache for both users
            get_ultimate_cache().invalidate_pattern(f'my_loans_context:{loan.borrower.id}:*')
            get_ultimate_cache().invalidate_pattern(f'my_loans_context:{loan.lender.id}:*')

            # Note: Email notification is handled by signals in apps/loans/signals.py

            # Mark loan request notifications as read
            try:
                from apps.notifications.models import Notification
                Notification.objects.filter(
                    user=request.user,
                    notification_type='loan_request',
                    related_loan=loan,
                    is_read=False
                ).update(is_read=True)
            except Exception:
                pass  # Notifications app might not be available

            messages.success(request, _("Loan approved successfully!"))

            # Create conversation for loan communication
            from apps.loans.services import LoanService
            LoanService.create_loan_conversation(loan)
        else:
            # Show form errors if validation fails
            if not form.is_valid():
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Loan approval form validation failed for loan {loan_id}: {form.errors}")
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, error)
            elif form.cleaned_data.get('action') != 'approve':
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Invalid action submitted for loan {loan_id}: {form.cleaned_data.get('action')}")
                messages.error(request, _("Invalid action submitted."))

    return redirect('loans:loan_detail', pk=loan.pk)


@login_required
def reject_loan(request, loan_id):
    """Reject a loan request."""
    loan = get_object_or_404(Loan, pk=loan_id)
    
    if loan.lender != request.user:
        raise PermissionDenied("Only lender can reject loans.")
    
    if loan.status != 'requested':
        messages.error(request, _("This loan cannot be rejected."))
        return redirect('loans:loan_detail', pk=loan.pk)
    
    if request.method == 'POST':
        form = LoanActionForm(request.user, loan, request.POST)
        if form.is_valid() and form.cleaned_data['action'] == 'reject':
            loan = form.save()

            # Invalidate my_loans cache for both users
            get_ultimate_cache().invalidate_pattern(f'my_loans_context:{loan.borrower.id}:*')
            get_ultimate_cache().invalidate_pattern(f'my_loans_context:{loan.lender.id}:*')

            # Note: Email notification is handled by signals in apps/loans/signals.py

            # Mark loan request notifications as read
            try:
                from apps.notifications.models import Notification
                Notification.objects.filter(
                    user=request.user,
                    notification_type='loan_request',
                    related_loan=loan,
                    is_read=False
                ).update(is_read=True)
            except Exception:
                pass  # Notifications app might not be available

            messages.success(request, _("Loan rejected."))
        else:
            # Show form errors if validation fails
            if not form.is_valid():
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Loan rejection form validation failed for loan {loan_id}: {form.errors}")
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, error)
            elif form.cleaned_data.get('action') != 'reject':
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Invalid action submitted for loan {loan_id}: {form.cleaned_data.get('action')}")
                messages.error(request, _("Invalid action submitted."))
    
    return redirect('loans:loan_detail', pk=loan.pk)


@login_required
def return_item(request, loan_id):
    """Mark an item as returned."""
    loan = get_object_or_404(Loan, pk=loan_id)

    if loan.borrower != request.user:
        raise PermissionDenied("Only borrower can return items.")

    if loan.status not in ['approved', 'active']:
        messages.error(request, _("This loan cannot be marked as returned."))
        return redirect('loans:loan_detail', pk=loan.pk)

    if request.method == 'POST':
        form = LoanActionForm(request.user, loan, request.POST)
        if form.is_valid() and form.cleaned_data['action'] in ['return', 'mark_active']:
            loan = form.save()

            # Invalidate item detail caches after loan status change
            get_ultimate_cache().invalidate_pattern(f'item_detail:*:{loan.item.id}:*')
            get_ultimate_cache().invalidate_pattern(f'item_detail_v2:{loan.item.id}:*')
            get_ultimate_cache().invalidate_pattern(f'item_detail_v3:{loan.item.id}:*')

            # Invalidate my_loans cache for both users
            get_ultimate_cache().invalidate_pattern(f'my_loans_context:{loan.borrower.id}:*')
            get_ultimate_cache().invalidate_pattern(f'my_loans_context:{loan.lender.id}:*')

            # Note: Email notification is handled by signals in apps/loans/signals.py

            if form.cleaned_data['action'] == 'return':
                messages.success(request, _("Item marked as returned. Lender will confirm."))
            elif form.cleaned_data['action'] == 'mark_active':
                # Mark approval notifications as read
                try:
                    from apps.notifications.models import Notification
                    Notification.objects.filter(
                        user=request.user,
                        notification_type='loan_approved',
                        related_loan=loan,
                        is_read=False
                    ).update(is_read=True)
                except Exception:
                    pass  # Notifications app might not be available
                messages.success(request, _("Item marked as picked up. Enjoy!"))
        else:
            # Show form errors if validation fails
            if not form.is_valid():
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Loan return form validation failed for loan {loan_id}: {form.errors}")
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, error)
            elif form.cleaned_data.get('action') != 'return':
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Invalid action submitted for loan {loan_id}: {form.cleaned_data.get('action')}")
                messages.error(request, _("Invalid action submitted."))

    return redirect('loans:loan_detail', pk=loan.pk)


@login_required
def confirm_return(request, loan_id):
    """Confirm return by lender."""
    loan = get_object_or_404(Loan, pk=loan_id)

    if loan.lender != request.user:
        raise PermissionDenied("Only lender can confirm returns.")

    if loan.status != 'borrower_returned':
        messages.error(request, _("This loan is not awaiting return confirmation."))
        return redirect('loans:loan_detail', pk=loan.pk)

    if request.method == 'POST':
        form = LoanActionForm(request.user, loan, request.POST)
        if form.is_valid() and form.cleaned_data['action'] == 'confirm_return':
            loan.confirm_return()

            # Invalidate item detail caches
            get_ultimate_cache().invalidate_pattern(f'item_detail:*:{loan.item.id}:*')
            get_ultimate_cache().invalidate_pattern(f'item_detail_v2:{loan.item.id}:*')
            get_ultimate_cache().invalidate_pattern(f'item_detail_v3:{loan.item.id}:*')

            # Invalidate my_loans cache for both users
            get_ultimate_cache().invalidate_pattern(f'my_loans_context:{loan.borrower.id}:*')
            get_ultimate_cache().invalidate_pattern(f'my_loans_context:{loan.lender.id}:*')

            # Mark return confirmation notifications as read
            try:
                from apps.notifications.models import Notification
                Notification.objects.filter(
                    user=request.user,
                    notification_type='loan_return_initiated',
                    related_loan=loan,
                    is_read=False
                ).update(is_read=True)
            except Exception:
                pass  # Notifications app might not be available

            messages.success(request, _("Return confirmed. Item is now available."))
        else:
            messages.error(request, _("Invalid action submitted."))

    return redirect('loans:loan_detail', pk=loan.pk)


@login_required
def cancel_loan(request, loan_id):
    """Cancel a loan request."""
    loan = get_object_or_404(Loan, pk=loan_id)
    
    # Check who can cancel and when
    if loan.status == 'requested':
        # Only borrower can cancel their own request
        if loan.borrower != request.user:
            raise PermissionDenied("Only borrower can cancel their own loan request.")
    elif loan.status in ['approved', 'active']:
        # Only lender can cancel approved loans that haven't been picked up yet
        if loan.lender != request.user:
            raise PermissionDenied("Only lender can cancel approved loans.")
    else:
        messages.error(request, _("This loan cannot be cancelled."))
        return redirect('loans:loan_detail', pk=loan.pk)
    
    if request.method == 'POST':
        form = LoanActionForm(request.user, loan, request.POST)
        if form.is_valid() and form.cleaned_data['action'] == 'cancel':
            loan = form.save()

            # Invalidate my_loans cache for both users
            get_ultimate_cache().invalidate_pattern(f'my_loans_context:{loan.borrower.id}:*')
            get_ultimate_cache().invalidate_pattern(f'my_loans_context:{loan.lender.id}:*')

            messages.success(request, _("Loan cancelled."))

    return redirect('loans:my_loans')


@login_required
def submit_review(request, loan_id):
    """Submit a review for a completed loan."""
    from django.db import transaction
    import logging
    logger = logging.getLogger(__name__)
    
    loan = get_object_or_404(Loan, pk=loan_id)
    
    # Check if user is a participant in this loan
    if request.user not in [loan.borrower, loan.lender]:
        raise PermissionDenied("You can only review loans you participated in.")
    
    # Check if loan is returned (completed)
    if loan.status != 'returned':
        messages.error(request, _("You can only review completed loans."))
        return redirect('loans:loan_detail', pk=loan.pk)
    
    if request.method == 'POST':
        form = LoanReviewForm(request.user, loan, request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Double-check if user has already reviewed this loan within transaction
                    if LoanReview.objects.filter(loan=loan, reviewer=request.user).exists():
                        messages.error(request, _("You have already reviewed this loan."))
                        return redirect('loans:loan_detail', pk=loan.pk)
                    
                    review = form.save(commit=False)
                    review.loan = loan
                    review.reviewer = request.user
                    
                    # Set reviewer role and reviewee
                    if loan.borrower == request.user:
                        review.reviewer_role = 'borrower'
                        review.reviewee = loan.lender
                    else:
                        review.reviewer_role = 'lender'
                        review.reviewee = loan.borrower
                    
                    review.save()
                    logger.info(f"Review created: {review.id} for loan {loan.id} by {request.user.username}")
                    
                    # Update reputation - get or create if it doesn't exist
                    from apps.loans.models import UserReputation
                    reputation, created = UserReputation.objects.get_or_create(user=review.reviewee)
                    reputation.calculate_ratings()

                    # Mark any loan-related notifications as read since user has now engaged
                    try:
                        from apps.notifications.models import Notification
                        Notification.objects.filter(
                            user=request.user,
                            related_loan=loan,
                            is_read=False
                        ).update(is_read=True)
                        logger.info(f"Marked notifications as read for user {request.user.username}, loan {loan.id}")
                    except Exception as e:
                        logger.warning(f"Failed to mark notifications as read: {e}")
                        pass  # Notifications app might not be available

                    # Comprehensive cache invalidation to ensure fresh data
                    try:
                        cache = get_ultimate_cache()
                        cache_patterns = [
                            f'item_detail_context:{loan.item.id}:*',
                            f'loan_detail_context:{loan.id}:*',
                            f'my_loans_context:{loan.borrower.id}:*',
                            f'my_loans_context:{loan.lender.id}:*'
                        ]
                        
                        for pattern in cache_patterns:
                            cache.invalidate_pattern(pattern)
                            logger.info(f"Invalidated cache pattern: {pattern}")
                    except Exception as e:
                        logger.warning(f"Cache invalidation failed: {e}")
                        pass  # Cache might not be available

                    messages.success(request, _("Review submitted successfully!"))
                    
            except Exception as e:
                logger.error(f"Failed to submit review for loan {loan.id} by {request.user.username}: {e}")
                messages.error(request, _("Failed to submit review. Please try again."))
                return redirect('loans:loan_detail', pk=loan.pk)
    
    return redirect('loans:loan_detail', pk=loan.pk)


@login_required
def request_extension(request, loan_id):
    """Request an extension for a loan."""
    loan = get_object_or_404(Loan, pk=loan_id)

    if request.method == 'POST':
        form = ExtensionRequestForm(request.user, loan, request.POST)
        if form.is_valid():
            loan = form.save()

            # Invalidate my_loans cache for both users
            get_ultimate_cache().invalidate_pattern(f'my_loans_context:{loan.borrower.id}:*')
            get_ultimate_cache().invalidate_pattern(f'my_loans_context:{loan.lender.id}:*')

            # Trigger notification
            # Note: Email notification is handled by signals in apps/loans/signals.py

            messages.success(request, _("Extension request sent!"))

    return redirect('loans:loan_detail', pk=loan.pk)


@login_required
def approve_extension(request, loan_id):
    """Approve an extension request."""
    loan = get_object_or_404(Loan, pk=loan_id)

    if loan.lender != request.user:
        raise PermissionDenied("Only the lender can approve extensions.")

    if not loan.extension_requested:
        messages.error(request, _("No extension request found."))
        return redirect('loans:loan_detail', pk=loan.pk)

    if request.method == 'POST':
        # Approve the extension
        loan.due_date = loan.due_date + timedelta(days=loan.extension_days)
        loan.extension_approved = True
        loan.save()

        # Invalidate my_loans cache for both users
        get_ultimate_cache().invalidate_pattern(f'my_loans_context:{loan.borrower.id}:*')
        get_ultimate_cache().invalidate_pattern(f'my_loans_context:{loan.lender.id}:*')

        # Note: Extension decision notification is handled by signals in apps/loans/signals.py

        # Mark extension request notifications as read
        try:
            from apps.notifications.models import Notification
            Notification.objects.filter(
                user=request.user,
                notification_type='loan_extension_request',  # Assuming this type exists
                related_loan=loan,
                is_read=False
            ).update(is_read=True)
        except Exception:
            pass  # Notifications app might not be available

        messages.success(request, _("Extension approved!"))

    return redirect('loans:loan_detail', pk=loan.pk)


@login_required
def reject_extension(request, loan_id):
    """Reject an extension request."""
    loan = get_object_or_404(Loan, pk=loan_id)

    if loan.lender != request.user:
        raise PermissionDenied("Only the lender can reject extensions.")

    if not loan.extension_requested:
        messages.error(request, _("No extension request found."))
        return redirect('loans:loan_detail', pk=loan.pk)

    if request.method == 'POST':
        # Reject the extension
        loan.extension_requested = False
        loan.extension_days = 0
        loan.extension_reason = ""
        loan.save()

        # Invalidate my_loans cache for both users
        get_ultimate_cache().invalidate_pattern(f'my_loans_context:{loan.borrower.id}:*')
        get_ultimate_cache().invalidate_pattern(f'my_loans_context:{loan.lender.id}:*')

        # Note: Extension decision notification is handled by signals in apps/loans/signals.py

        messages.success(request, _("Extension rejected."))

    return redirect('loans:loan_detail', pk=loan.pk)
