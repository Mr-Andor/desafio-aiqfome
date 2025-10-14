from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase


class CustomerModelTests(TestCase):
    def test_customer_str_returns_name(self):
        customer = get_user_model().objects.create_user(
            name="Leia Organa",
            email="leia@rebellion.example",
            password="secret123",
        )

        self.assertEqual(str(customer), "Leia Organa")

    def test_customer_email_must_be_unique(self):
        user_model = get_user_model()
        user_model.objects.create_user(
            name="Han Solo",
            email="han@falcon.example",
            password="secret123",
        )

        with self.assertRaises(IntegrityError):
            user_model.objects.create_user(
                name="Another Han",
                email="han@falcon.example",
                password="secret456",
            )
