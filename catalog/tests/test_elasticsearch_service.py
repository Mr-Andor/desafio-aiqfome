from unittest.mock import MagicMock

from django.test import TestCase

from catalog.infrastructure.elasticsearch_service import ElasticsearchProductSearchService
from catalog.domain.entities import ProductSearchResultDTO


class ElasticsearchProductSearchServiceTests(TestCase):
    def test_builds_query_with_filters(self):
        client = MagicMock()
        client.search.return_value = {
            "hits": {
                "hits": [
                    {
                        "_id": "42",
                        "_source": {
                            "title": "Sending Stone",
                            "description": "Arcane stones for long-distance whispers.",
                            "price": 79.99,
                            "rating": {"rate": 4.2},
                            "image": "sending_stone.png",
                        },
                    }
                ]
            }
        }

        service = ElasticsearchProductSearchService(client=client, index="products")

        results = service.search(
            query="sending stone",
            min_price=50,
            max_price=100,
            min_rating=4,
        )

        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], ProductSearchResultDTO)
        self.assertEqual(results[0].title, "Sending Stone")

        called_kwargs = client.search.call_args.kwargs
        self.assertEqual(called_kwargs["index"], "products")
        bool_query = called_kwargs["query"]["bool"]
        must_clause = bool_query["must"][0]
        self.assertEqual(must_clause["multi_match"]["query"], "sending stone")
        price_range = bool_query["filter"][0]["range"]["price"]
        self.assertEqual(price_range["gte"], 50)
        self.assertEqual(price_range["lte"], 100)
        rating_range = bool_query["filter"][1]["range"]["rating.rate"]
        self.assertEqual(rating_range["gte"], 4)
