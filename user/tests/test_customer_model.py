from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase


class CustomerModelTests(TestCase):
    def test_customer_str_returns_name(self):
        customer = get_user_model().objects.create_user(
            name="Viconia DeVir",
            email="viconia@baldursgate.example",
            password="shadow123",
        )

        self.assertEqual(str(customer), "Viconia DeVir")

    def test_customer_email_must_be_unique(self):
        user_model = get_user_model()
        user_model.objects.create_user(
            name="Minsc",
            email="minsc@rashemen.example",
            password="hamster123",
        )

        with self.assertRaises(IntegrityError):
            user_model.objects.create_user(
                name="Another Minsc",
                email="minsc@rashemen.example",
                password="hamster456",
            )
