import base64
import json
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from user.application import CreateCustomer
from user.infrastructure.repositories import DjangoCustomerRepository


class FavoriteAPITests(TestCase):
    def setUp(self):
        self.password = "eldritch123"
        self.customer = CreateCustomer(DjangoCustomerRepository()).execute(
            name="Fjord Stone",
            email="fjord@conclave.example",
            password=self.password,
        )

    def _auth_headers(self):
        token = base64.b64encode(f"{self.customer.email}:{self.password}".encode("utf-8")).decode("utf-8")
        return {"HTTP_AUTHORIZATION": f"Basic {token}"}

    @patch("user.interfaces.views.FakeStoreProductGateway.exists", return_value=True)
    def test_add_favorite_returns_201(self, exists_mock):
        response = self.client.post(
            reverse("favorite-list", args=[self.customer.id]),
            data=json.dumps({"product_id": 5}),
            content_type="application/json",
            **self._auth_headers(),
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["product_id"], 5)
        exists_mock.assert_called_once_with(5)

    def test_list_favorites_requires_auth(self):
        response = self.client.get(reverse("favorite-list", args=[self.customer.id]))
        self.assertEqual(response.status_code, 401)
        self.assertIn("Authentication credentials", response.json()["error"])

    @patch("user.interfaces.views.FakeStoreProductGateway.get_details")
    @patch("user.interfaces.views.FakeStoreProductGateway.exists", return_value=True)
    def test_list_favorites_returns_marked_products(self, _exists_mock, get_details_mock):
        self.client.post(
            reverse("favorite-list", args=[self.customer.id]),
            data=json.dumps({"product_id": 7}),
            content_type="application/json",
            **self._auth_headers(),
        )
        self.client.post(
            reverse("favorite-list", args=[self.customer.id]),
            data=json.dumps({"product_id": 9}),
            content_type="application/json",
            **self._auth_headers(),
        )

        get_details_mock.side_effect = [
            {"title": "Sunblade", "image": "sunblade.png", "price": 999.0, "review": {"rate": 4.9}},
            {"title": "Mithral Armor", "image": "mithral_armor.png", "price": 499.0, "review": None},
        ]

        response = self.client.get(reverse("favorite-list", args=[self.customer.id]), **self._auth_headers())

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual({item["product_id"] for item in payload}, {7, 9})
        armor = next(item for item in payload if item["product_id"] == 9)
        self.assertEqual(armor["title"], "Mithral Armor")
        self.assertEqual(armor["image"], "mithral_armor.png")
        self.assertEqual(armor["price"], 499.0)
        self.assertIsNone(armor["review"])

    @patch("user.interfaces.views.FakeStoreProductGateway.exists", return_value=True)
    def test_add_duplicate_favorite_returns_400(self, _exists_mock):
        payload = {"product_id": 8}
        self.client.post(
            reverse("favorite-list", args=[self.customer.id]),
            data=json.dumps(payload),
            content_type="application/json",
            **self._auth_headers(),
        )

        response = self.client.post(
            reverse("favorite-list", args=[self.customer.id]),
            data=json.dumps(payload),
            content_type="application/json",
            **self._auth_headers(),
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("already marked", response.json()["error"])

    @patch("user.interfaces.views.FakeStoreProductGateway.exists", return_value=False)
    def test_add_favorite_validates_external_product(self, exists_mock):
        response = self.client.post(
            reverse("favorite-list", args=[self.customer.id]),
            data=json.dumps({"product_id": 404}),
            content_type="application/json",
            **self._auth_headers(),
        )

        self.assertEqual(response.status_code, 404)
        self.assertIn("Product not found", response.json()["error"])
        exists_mock.assert_called_once_with(404)

    @patch("user.interfaces.views.FakeStoreProductGateway.exists", return_value=True)
    def test_remove_favorite_returns_204(self, _exists_mock):
        self.client.post(
            reverse("favorite-list", args=[self.customer.id]),
            data=json.dumps({"product_id": 11}),
            content_type="application/json",
            **self._auth_headers(),
        )

        response = self.client.delete(
            reverse("favorite-detail", args=[self.customer.id, 11]),
            content_type="application/json",
            **self._auth_headers(),
        )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")

    def test_remove_missing_favorite_returns_404(self):
        response = self.client.delete(
            reverse("favorite-detail", args=[self.customer.id, 999]),
            content_type="application/json",
            **self._auth_headers(),
        )

        self.assertEqual(response.status_code, 404)
        self.assertIn("Favorite not found", response.json()["error"])
