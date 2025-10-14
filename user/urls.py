from django.urls import path

from user.interfaces.views import CustomerDetailView, CustomerListCreateView

urlpatterns = [
    path("users/", CustomerListCreateView.as_view(), name="user-list"),
    path("users/<int:customer_id>/", CustomerDetailView.as_view(), name="user-detail"),
]
