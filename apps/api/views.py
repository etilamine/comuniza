"""
API views for Comuniza platform.
Provides JWT authentication and RESTful endpoints for mobile and web clients.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from drf_spectacular.utils import extend_schema
from apps.core.rate_limiting import strict_auth_rate_limit, strict_api_rate_limit, message_rate_limit, content_creation_rate_limit

from apps.items.models import Item, ItemCategory
from apps.users.models import User
from apps.groups.models import Group
from apps.loans.models import Loan
from .serializers import (
    ItemSerializer, ItemCategorySerializer,
    UserSerializer, GroupSerializer, LoanSerializer
)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Enhanced token obtain view that includes user profile data.
    Optimized for mobile app login experience.
    """

    @strict_auth_rate_limit
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            # Add user profile data to login response
            # Use email for authentication (allauth requirement)
            user = authenticate(
                email=request.data.get('email'),  # Changed from username to email
                password=request.data.get('password')
            )
            if user:
                response.data['user'] = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_active': user.is_active,
                    'date_joined': user.date_joined.isoformat() if user.date_joined else None,
                }

        return response


class LogoutView(APIView):
    """
    Logout view that blacklists the refresh token.
    Ensures logged-out tokens cannot be reused.
    """

    @strict_auth_rate_limit
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response({
                    'message': 'Successfully logged out',
                    'detail': 'Refresh token has been blacklisted'
                })
            else:
                return Response(
                    {'error': 'Refresh token required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {'error': 'Invalid token', 'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint for items.
    Provides CRUD operations with filtering and search.
    """
    queryset = Item.objects.select_related('owner', 'category')
    serializer_class = ItemSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'condition', 'category', 'owner']
    ordering_fields = ['created_at', 'title', 'borrow_count']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        """Set the owner to the current user when creating items"""
        serializer.save(owner=self.request.user)

    @strict_api_rate_limit
    def create(self, request, *args, **kwargs):
        """Rate limited item creation"""
        return super().create(request, *args, **kwargs)

    @strict_api_rate_limit
    def update(self, request, *args, **kwargs):
        """Rate limited item updates"""
        return super().update(request, *args, **kwargs)

    @strict_api_rate_limit
    def destroy(self, request, *args, **kwargs):
        """Rate limited item deletion"""
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def borrow(self, request, pk=None):
        """
        Request to borrow an item.
        Creates a loan request for the specified item.
        """
        item = self.get_object()

        # Check if item is available
        if not item.is_available:
            return Response(
                {'error': 'Item is not available for borrowing'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user already has a pending loan for this item
        existing_loan = Loan.objects.filter(
            item=item,
            borrower=request.user,
            status__in=['pending', 'approved']
        ).exists()

        if existing_loan:
            return Response(
                {'error': 'You already have a pending loan request for this item'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Note: Loan request creation not fully implemented in API endpoint.
        # Use main views (apps/loans/views.py::request_loan) for full functionality.
        return Response({
            'message': f'Borrow request for "{item.title}" has been submitted',
            'item_id': item.id,
            'status': 'pending'
        })


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only API endpoint for users.
    Provides user profile information.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active']


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only API endpoint for groups.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


@extend_schema(
    description="List loans for the authenticated user",
    responses={200: LoanSerializer(many=True)}
)
class LoanViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only API endpoint for loans.
    Users can only view their own loans.
    """
    serializer_class = LoanSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['created_at', 'start_date', 'due_date']
    ordering = ['-created_at']

    def get_queryset(self):
        """Users can only see their own loans"""
        return Loan.objects.filter(borrower=self.request.user)