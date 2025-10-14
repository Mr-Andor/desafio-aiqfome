from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class CustomerManager(BaseUserManager):
    """Custom manager that uses email as the unique identifier."""

    use_in_migrations = True

    def _create_user(self, email, name, password, **extra_fields):
        if not email:
            raise ValueError("An email address must be provided")
        if not name:
            raise ValueError("A name must be provided")

        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, name, password, **extra_fields)

    def create_superuser(self, email, name, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, name, password, **extra_fields)


class Customer(AbstractUser):
    """Customer model extending Django's user with email as username."""

    username = None
    first_name = None
    last_name = None

    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    objects = CustomerManager()

    def __str__(self) -> str:
        return self.name


class Favorite(models.Model):
    """Favorite product marked by a customer."""

    customer = models.ForeignKey(
        "Customer",
        related_name="favorites",
        on_delete=models.CASCADE,
    )
    product_id = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["customer", "product_id"],
                name="unique_customer_favorite",
            )
        ]
        ordering = ("id",)

    def __str__(self) -> str:
        return f"{self.customer_id}:{self.product_id}"
