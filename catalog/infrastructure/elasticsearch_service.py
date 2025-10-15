from __future__ import annotations

from typing import Any, Dict, Sequence

from elasticsearch import Elasticsearch
from django.conf import settings

from catalog.domain import ProductSearchResultDTO, ProductSearchService


def _get_es_config(overrides: Dict[str, Any] | None = None) -> Dict[str, Any]:
    base_config = getattr(settings, "ELASTICSEARCH", {}).copy()
    if overrides:
        base_config.update({k: v for k, v in overrides.items() if v is not None})
    return base_config


def get_elasticsearch_client(config: Dict[str, Any] | None = None) -> Elasticsearch:
    """Create an Elasticsearch client based on Django settings configuration."""
    cfg = _get_es_config(config)

    client_kwargs: Dict[str, Any] = {}

    cloud_id = cfg.get("cloud_id")
    hosts = cfg.get("hosts")

    if cloud_id:
        client_kwargs["cloud_id"] = cloud_id
    else:
        if isinstance(hosts, str):
            hosts = [host.strip() for host in hosts.split(",") if host.strip()]
        client_kwargs["hosts"] = hosts

    api_key = cfg.get("api_key")
    username = cfg.get("username")
    password = cfg.get("password")

    if api_key:
        client_kwargs["api_key"] = api_key
    elif username and password:
        client_kwargs["basic_auth"] = (username, password)

    return Elasticsearch(**client_kwargs)


class ElasticsearchProductSearchService(ProductSearchService):
    """Product search service backed by Elasticsearch."""

    def __init__(self, client: Elasticsearch | None = None, index: str | None = None):
        cfg = _get_es_config()
        self._client = client or get_elasticsearch_client(cfg)
        self._index = index or cfg.get("index", "products")
        self._size = int(cfg.get("search_size", 50))

    def search(
        self,
        *,
        query: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        min_rating: float | None = None,
    ) -> Sequence[ProductSearchResultDTO]:
        must: list[Dict[str, Any]] = []
        filters: list[Dict[str, Any]] = []

        if query:
            must.append(
                {
                    "multi_match": {
                        "query": query,
                        "fields": ["title^2", "description"],
                        "type": "best_fields",
                    }
                }
            )

        price_range: Dict[str, float] = {}
        if min_price is not None:
            price_range["gte"] = min_price
        if max_price is not None:
            price_range["lte"] = max_price
        if price_range:
            filters.append({"range": {"price": price_range}})

        if min_rating is not None:
            filters.append({"range": {"rating.rate": {"gte": min_rating}}})

        if not must and not filters:
            es_query: Dict[str, Any] = {"match_all": {}}
        else:
            es_query = {"bool": {}}
            if must:
                es_query["bool"]["must"] = must
            if filters:
                es_query["bool"]["filter"] = filters

        response = self._client.search(index=self._index, query=es_query, size=self._size)

        hits = response.get("hits", {}).get("hits", [])
        results: list[ProductSearchResultDTO] = []
        for hit in hits:
            source = hit.get("_source", {})
            rating_data = source.get("rating")
            if isinstance(rating_data, dict):
                rating_value = rating_data.get("rate")
            else:
                rating_value = rating_data

            results.append(
                ProductSearchResultDTO(
                    id=int(hit.get("_id", source.get("id", 0))),
                    title=source.get("title", ""),
                    description=source.get("description", ""),
                    price=float(source.get("price", 0.0)),
                    rating=(
                        float(rating_value)
                        if rating_value is not None and rating_value != ""
                        else None
                    ),
                    image=source.get("image"),
                )
            )

        return results
