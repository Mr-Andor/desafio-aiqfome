from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict

from django.http import JsonResponse
from django.views import View

from catalog.application import SearchProducts
from catalog.domain import ProductSearchResultDTO
from catalog.infrastructure import ElasticsearchProductSearchService


def get_product_search_service():
    return ElasticsearchProductSearchService()


def _parse_optional_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError("Invalid numeric filter") from exc


class ProductSearchView(View):
    def get(self, request):
        keyword = request.GET.get("keyword")
        try:
            min_price = _parse_optional_float(request.GET.get("min_price"))
            max_price = _parse_optional_float(request.GET.get("max_price"))
            min_rating = _parse_optional_float(request.GET.get("min_rating"))
        except ValueError as exc:
            return JsonResponse({"error": str(exc)}, status=400)

        service = get_product_search_service()
        results = SearchProducts(service).execute(
            query=keyword,
            min_price=min_price,
            max_price=max_price,
            min_rating=min_rating,
        )

        payload = [asdict(result) if isinstance(result, ProductSearchResultDTO) else result for result in results]
        return JsonResponse(payload, safe=False, status=200)
