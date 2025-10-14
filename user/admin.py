from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Customer, Favorite


@admin.register(Customer)
class CustomerAdmin(UserAdmin):
    """Admin configuration for the customer model."""

    model = Customer
    list_display = ("email", "name", "is_active", "is_staff")
    ordering = ("email",)
    search_fields = ("email", "name")

    fieldsets = (
        (None, {"fields": ("email", "password", "name")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "name", "password1", "password2", "is_staff", "is_superuser"),
            },
        ),
    )
    readonly_fields = ("date_joined", "last_login")


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Admin configuration for customer favorites."""

    list_display = ("customer", "product_id", "created_at")
    search_fields = ("customer__email", "customer__name")
    list_filter = ("product_id",)
