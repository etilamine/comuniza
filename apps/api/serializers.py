"""
API serializers for Comuniza platform.
Provides JSON serialization for mobile and web API responses.
"""

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from apps.items.models import Item, ItemCategory, ItemImage
from apps.users.models import User
from apps.groups.models import Group
from apps.loans.models import Loan


class ItemImageSerializer(serializers.ModelSerializer):
    """Serializer for item images"""
    
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ItemImage
        fields = ['id', 'image_url', 'caption', 'is_primary', 'order']
        read_only_fields = ['id', 'image_url', 'caption', 'is_primary', 'order']
    
    def get_image_url(self, obj):
        """Get image URL from ThumbnailerImageField"""
        if obj.image:
            if hasattr(obj.image, 'url'):
                return obj.image.url
            return str(obj.image)
        return None


class ItemCategorySerializer(serializers.ModelSerializer):
    """Serializer for item categories"""

    class Meta:
        model = ItemCategory
        fields = [
            'id', 'name', 'slug', 'description',
            'created_at', 'is_active'
        ]


class ItemSerializer(serializers.ModelSerializer):
    """Serializer for items with owner and category details"""

    owner = serializers.StringRelatedField(read_only=True)
    owner_id = serializers.IntegerField(read_only=True)
    category = ItemCategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True, required=False)
    images = ItemImageSerializer(many=True, read_only=True)

    # Additional computed fields
    is_available = serializers.BooleanField(read_only=True)
    can_borrow = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = [
            'id', 'title', 'description', 'category', 'category_id',
            'status', 'condition', 'owner', 'owner_id',
            'created_at', 'updated_at', 'borrow_count',
            'is_available', 'can_borrow', 'images'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'borrow_count',
            'is_available', 'can_borrow', 'images'
        ]

    @extend_schema_field(serializers.BooleanField())
    def get_can_borrow(self, obj):
        """Check if current user can borrow this item"""
        request = self.context.get('request')
        if request and request.user:
            return obj.can_borrow(request.user)
        return False

    def create(self, validated_data):
        """Handle category assignment during creation"""
        category_id = validated_data.pop('category_id', None)
        if category_id:
            try:
                category = ItemCategory.objects.get(id=category_id)
                validated_data['category'] = category
            except ItemCategory.DoesNotExist:
                pass  # Leave category as None
        return super().create(validated_data)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profiles"""

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_active', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']


class GroupSerializer(serializers.ModelSerializer):
    """Serializer for groups"""

    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            'id', 'name', 'slug', 'description',
            'is_active', 'created_at', 'member_count'
        ]

    @extend_schema_field(serializers.IntegerField())
    def get_member_count(self, obj):
        return obj.members.count()


class LoanSerializer(serializers.ModelSerializer):
    """Serializer for loans"""

    item_title = serializers.CharField(source='item.title', read_only=True)
    item_owner = serializers.CharField(source='item.owner.username', read_only=True)
    borrower_name = serializers.CharField(source='borrower.username', read_only=True)

    class Meta:
        model = Loan
        fields = [
            'id', 'item', 'item_title', 'item_owner',
            'borrower', 'borrower_name', 'status',
            'start_date', 'due_date', 'created_at',
            'approved_at', 'returned_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'approved_at', 'returned_at'
        ]