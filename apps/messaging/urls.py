"""
URLs for Messaging app.
"""

from django.urls import path

from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.ConversationListView.as_view(), name='conversation_list'),
    path('conversation/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('conversation/<int:conversation_id>/delete/', views.delete_conversation, name='delete_conversation'),
    path('start/<str:username>/', views.start_conversation, name='start_conversation'),
    path('start/<str:username>/item/<int:item_id>/', views.start_conversation, name='start_conversation_item'),
    path('start/<str:username>/loan/<int:loan_id>/', views.start_conversation, name='start_conversation_loan'),
    path('start/', views.start_conversation_form, name='start_conversation_form'),
    path('send/<int:conversation_id>/', views.send_message, name='send_message'),
]