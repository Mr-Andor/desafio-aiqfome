import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from user.application.use_cases import CreateCustomer
from user.infrastructure.repositories import DjangoCustomerRepository


class CustomerAPITests(TestCase):
    def setUp(self):
        self.repository = DjangoCustomerRepository()
        self.factory_create = CreateCustomer(self.repository)

        self.staff_user = get_user_model().objects.create_user(
            name="Volo Geddarm",
            email="volo@waterdeep.example",
            password="volobook123",
            is_staff=True,
        )

    def _auth_headers(self, user):
        access_token = RefreshToken.for_user(user).access_token
        return {"HTTP_AUTHORIZATION": f"Bearer {access_token}"}

    def test_create_customer_returns_201(self):
        payload = {
            "name": "Keyleth",
            "email": "keyleth@airashari.example",
            "password": "verdant123",
        }

        response = self.client.post(
            reverse("user-list"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["name"], "Keyleth")
        self.assertEqual(body["email"], "keyleth@airashari.example")
        self.assertNotIn("password", body)

    def test_list_customers_requires_auth(self):
        response = self.client.get(reverse("user-list"))
        self.assertEqual(response.status_code, 401)
        self.assertIn("Authentication credentials", response.json()["error"])

    def test_list_customers_returns_all_users(self):
        self.factory_create.execute(
            name="Scanlan Shorthalt",
            email="scanlan@voxmachina.example",
            password="song123",
        )
        self.factory_create.execute(
            name="Percival de Rolo",
            email="percy@voxmachina.example",
            password="gun123",
        )

        response = self.client.get(
            reverse("user-list"),
            **self._auth_headers(self.staff_user),
        )

        self.assertEqual(response.status_code, 200)
        emails = {item["email"] for item in response.json()}
        self.assertTrue(
            {"scanlan@voxmachina.example", "percy@voxmachina.example"}.issubset(emails)
        )

    def test_retrieve_customer_requires_matching_credentials(self):
        customer_password = "heal123"
        customer = self.factory_create.execute(
            name="Pike Trickfoot",
            email="pike@voxmachina.example",
            password=customer_password,
        )

        response = self.client.get(reverse("user-detail", args=[customer.id]))

        self.assertEqual(response.status_code, 401)

    def test_retrieve_customer_returns_single_user(self):
        customer_password = "heal123"
        customer = self.factory_create.execute(
            name="Pike Trickfoot",
            email="pike@voxmachina.example",
            password=customer_password,
        )
        customer_model = get_user_model().objects.get(pk=customer.id)

        response = self.client.get(
            reverse("user-detail", args=[customer.id]),
            **self._auth_headers(customer_model),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], customer.id)

    def test_update_customer_requires_owner(self):
        customer_password = "rage123"
        customer = self.factory_create.execute(
            name="Grog Strongjaw",
            email="grog@voxmachina.example",
            password=customer_password,
        )

        payload = {"name": "Grog Strongjaw", "email": "grog@herdstone.example"}

        response = self.client.put(
            reverse("user-detail", args=[customer.id]),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)

    def test_update_customer_replaces_fields(self):
        customer_password = "rage123"
        customer = self.factory_create.execute(
            name="Grog Strongjaw",
            email="grog@voxmachina.example",
            password=customer_password,
        )
        customer_model = get_user_model().objects.get(pk=customer.id)

        payload = {"name": "Grog Strongjaw", "email": "grog@herdstone.example"}

        response = self.client.put(
            reverse("user-detail", args=[customer.id]),
            data=json.dumps(payload),
            content_type="application/json",
            **self._auth_headers(customer_model),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], "grog@herdstone.example")

    def test_delete_customer_requires_auth(self):
        customer_password = "arrow123"
        customer = self.factory_create.execute(
            name="Vexahlia Vessar",
            email="vex@voxmachina.example",
            password=customer_password,
        )

        response = self.client.delete(reverse("user-detail", args=[customer.id]))

        self.assertEqual(response.status_code, 401)

    def test_delete_customer_returns_204(self):
        customer_password = "arrow123"
        customer = self.factory_create.execute(
            name="Vexahlia Vessar",
            email="vex@voxmachina.example",
            password=customer_password,
        )
        customer_model = get_user_model().objects.get(pk=customer.id)

        response = self.client.delete(
            reverse("user-detail", args=[customer.id]),
            **self._auth_headers(customer_model),
        )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
