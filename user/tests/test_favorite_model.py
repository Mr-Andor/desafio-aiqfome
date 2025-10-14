from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from user.models import Favorite


class FavoriteModelTests(TestCase):
    def setUp(self):
        self.customer = get_user_model().objects.create_user(
            name="Mon Mothma",
            email="mon@rebellion.example",
            password="secret123",
        )

    def test_can_create_favorite_for_customer(self):
        favorite = Favorite.objects.create(
            customer=self.customer,
            product_id=42,
        )

        self.assertEqual(favorite.customer, self.customer)
        self.assertEqual(favorite.product_id, 42)

    def test_favorite_must_be_unique_per_customer(self):
        Favorite.objects.create(customer=self.customer, product_id=99)

        with self.assertRaises(IntegrityError):
            Favorite.objects.create(customer=self.customer, product_id=99)
