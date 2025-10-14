import json

from django.test import TestCase
from django.urls import reverse

from user.application.use_cases import CreateCustomer
from user.infrastructure.repositories import DjangoCustomerRepository


class CustomerAPITests(TestCase):
    def setUp(self):
        self.repository = DjangoCustomerRepository()
        self.factory_create = CreateCustomer(self.repository)

    def test_create_customer_returns_201(self):
        payload = {"name": "Cara Dune", "email": "cara@marshal.example"}

        response = self.client.post(
            reverse("user-list"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["name"], "Cara Dune")
        self.assertEqual(response.json()["email"], "cara@marshal.example")

    def test_list_customers_returns_all_users(self):
        self.factory_create.execute(name="Bo-Katan Kryze", email="bo@mandalore.example")
        self.factory_create.execute(name="Din Djarin", email="din@mandalore.example")

        response = self.client.get(reverse("user-list"))

        self.assertEqual(response.status_code, 200)
        emails = {item["email"] for item in response.json()}
        self.assertEqual(
            emails,
            {"bo@mandalore.example", "din@mandalore.example"},
        )

    def test_retrieve_customer_returns_single_user(self):
        customer = self.factory_create.execute(
            name="Grogu",
            email="grogu@jedifoundling.example",
        )

        response = self.client.get(reverse("user-detail", args=[customer.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], customer.id)

    def test_update_customer_replaces_fields(self):
        customer = self.factory_create.execute(
            name="Moff Gideon",
            email="gideon@empire.example",
        )

        payload = {"name": "Moff Gideon", "email": "gideon@darktrooper.example"}

        response = self.client.put(
            reverse("user-detail", args=[customer.id]),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], "gideon@darktrooper.example")

    def test_delete_customer_returns_204(self):
        customer = self.factory_create.execute(
            name="IG-11",
            email="ig11@droid.example",
        )

        response = self.client.delete(reverse("user-detail", args=[customer.id]))

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
