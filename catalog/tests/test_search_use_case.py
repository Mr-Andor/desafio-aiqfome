from dataclasses import dataclass

from django.test import TestCase

from catalog.application.search_use_cases import SearchProducts


@dataclass(frozen=True)
class StubProduct:
    id: int
    title: str
    description: str
    price: float
    rating: float | None = None
    image: str | None = None


class StubSearchService:
    def __init__(self):
        self.calls = []
        self.results = [
            StubProduct(
                id=1,
                title="Thermal Detonator",
                description="Compact self-detonating explosive device.",
                price=129.99,
                rating=4.8,
                image="detonator.png",
            )
        ]

    def search(self, *, query=None, min_price=None, max_price=None, min_rating=None):
        self.calls.append(
            {
                "query": query,
                "min_price": min_price,
                "max_price": max_price,
                "min_rating": min_rating,
            }
        )
        return self.results


class SearchProductsUseCaseTests(TestCase):
    def test_delegates_to_service_with_filters(self):
        service = StubSearchService()
        use_case = SearchProducts(service)

        results = use_case.execute(
            query="detonator",
            min_price=100,
            max_price=200,
            min_rating=4.5,
        )

        self.assertEqual(results, service.results)
        self.assertEqual(
            service.calls[-1],
            {
                "query": "detonator",
                "min_price": 100,
                "max_price": 200,
                "min_rating": 4.5,
            },
        )
