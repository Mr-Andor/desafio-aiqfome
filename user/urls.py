from django.urls import path

from user.interfaces.views import (
    CustomerDetailView,
    CustomerListCreateView,
    FavoriteDetailView,
    FavoriteListCreateView,
)

urlpatterns = [
    path("users/", CustomerListCreateView.as_view(), name="user-list"),
    path("users/<int:customer_id>/", CustomerDetailView.as_view(), name="user-detail"),
    path(
        "users/<int:customer_id>/favorites/",
        FavoriteListCreateView.as_view(),
        name="favorite-list",
    ),
    path(
        "users/<int:customer_id>/favorites/<int:product_id>/",
        FavoriteDetailView.as_view(),
        name="favorite-detail",
    ),
]
