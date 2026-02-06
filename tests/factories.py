"""
Test factories for Comuniza using factory-boy.
"""

import factory
from django.contrib.auth import get_user_model
from apps.items.models import Item, ItemCategory
from apps.groups.models import Group, GroupMembership
from apps.loans.models import Loan

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for User model."""
    
    class Meta:
        model = User
        django_get_or_create = ('email',)
    
    email = factory.Faker('email')
    username = factory.Faker('user_name')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    
    @factory.post_generation
    def set_password(obj, create, extracted, **kwargs):
        if not create:
            return
        
        obj.set_password('testpass123')
        obj.save()


class GroupFactory(factory.django.DjangoModelFactory):
    """Factory for Group model."""
    
    class Meta:
        model = Group
    
    name = factory.Faker('company')
    description = factory.Faker('text', max_nb_chars=200)
    city = factory.Faker('city')
    country = 'Germany'
    owner = factory.SubFactory(UserFactory)


class ItemCategoryFactory(factory.django.DjangoModelFactory):
    """Factory for ItemCategory model."""
    
    class Meta:
        model = ItemCategory
        django_get_or_create = ('name',)
    
    name = factory.Faker('word')
    description = factory.Faker('text', max_nb_chars=100)


class ItemFactory(factory.django.DjangoModelFactory):
    """Factory for Item model."""
    
    class Meta:
        model = Item
    
    title = factory.Faker('catch_phrase')
    description = factory.Faker('text', max_nb_chars=500)
    author = factory.Faker('name')
    publisher = factory.Faker('company')
    condition = 'good'
    status = 'available'
    visibility = 'public'
    max_loan_days = 14
    owner = factory.SubFactory(UserFactory)
    category = factory.SubFactory(ItemCategoryFactory)


class LoanFactory(factory.django.DjangoModelFactory):
    """Factory for Loan model."""
    
    class Meta:
        model = Loan
    
    item = factory.SubFactory(ItemFactory)
    borrower = factory.SubFactory(UserFactory)
    status = 'requested'
    start_date = factory.Faker('date_between', start_date='-30d', end_date='today')
    end_date = factory.Faker('date_between', start_date='today', end_date='+30d')


class GroupMembershipFactory(factory.django.DjangoModelFactory):
    """Factory for GroupMembership model."""
    
    class Meta:
        model = GroupMembership
        django_get_or_create = ('group', 'user')
    
    group = factory.SubFactory(GroupFactory)
    user = factory.SubFactory(UserFactory)
    role = 'member'
    status = 'active'