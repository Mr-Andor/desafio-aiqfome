import json
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from catalog.domain.entities import ProductSearchResultDTO

class ProductSearchAPITests(TestCase):
    @patch("catalog.interfaces.views.get_product_search_service")
    def test_returns_search_results_with_filters(self, get_service_mock):
        service_instance = get_service_mock.return_value
        service_instance.search.return_value = [
            ProductSearchResultDTO(
                id=101,
                title="Jedi Robe",
                description="Traditional cloak worn by the Jedi Order.",
                price=499.0,
                rating=4.9,
                image="robe.png",
            )
        ]

        response = self.client.get(
            reverse("product-search"),
            {"keyword": "robe", "min_price": "100", "max_price": "600", "min_rating": "4"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload[0]["title"], "Jedi Robe")
        service_instance.search.assert_called_once_with(
            query="robe",
            min_price=100.0,
            max_price=600.0,
            min_rating=4.0,
        )

    @patch("catalog.interfaces.views.get_product_search_service")
    def test_validates_numeric_filters(self, get_service_mock):
        response = self.client.get(
            reverse("product-search"),
            {"min_price": "not-a-number"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid numeric filter", response.json()["error"])
        get_service_mock.assert_not_called()
