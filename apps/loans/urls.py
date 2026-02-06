"""
URL patterns for Loans app.
"""

from django.urls import path

from . import views

app_name = "loans"

urlpatterns = [
    # List views
    path("", views.my_loans, name="my_loans"),
    path("my-loans/", views.my_loans, name="index"),
    # Loan detail
    path("<int:pk>/", views.LoanDetailView.as_view(), name="loan_detail"),
    # Loan request
    path("request/<str:identifier>/", views.request_loan, name="request"),
    # Loan actions
    path("<int:loan_id>/approve/", views.approve_loan, name="approve"),
    path("<int:loan_id>/reject/", views.reject_loan, name="reject"),
    path("<int:loan_id>/return/", views.return_item, name="return"),
    path("<int:loan_id>/confirm_return/", views.confirm_return, name="confirm_return"),
    path("<int:loan_id>/cancel/", views.cancel_loan, name="cancel"),
    path("<int:loan_id>/review/", views.submit_review, name="submit_review"),
    path("<int:loan_id>/extend/", views.request_extension, name="request_extension"),
    path("<int:loan_id>/approve_extension/", views.approve_extension, name="approve_extension"),
    path("<int:loan_id>/reject_extension/", views.reject_extension, name="reject_extension"),
]
