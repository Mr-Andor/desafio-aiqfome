from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.application import SearchProducts
from catalog.domain import ProductSearchResultDTO
from catalog.infrastructure import ElasticsearchProductSearchService
from catalog.interfaces.serializers import ProductSearchResultSerializer


def get_product_search_service():
    return ElasticsearchProductSearchService()


def _parse_optional_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError("Invalid numeric filter") from exc


class ProductSearchView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Search products",
        description="Query products stored in Elasticsearch with optional price and rating filters.",
        parameters=[
            OpenApiParameter(
                name="keyword",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Term to match against product title or description.",
            ),
            OpenApiParameter(
                name="min_price",
                type=float,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Minimum product price to include in the result.",
            ),
            OpenApiParameter(
                name="max_price",
                type=float,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Maximum product price to include in the result.",
            ),
            OpenApiParameter(
                name="min_rating",
                type=float,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Minimum product rating to include in the result.",
            ),
        ],
        responses={
            200: ProductSearchResultSerializer(many=True),
            400: OpenApiResponse(description="Invalid numeric filter."),
        },
        auth=[],
    )
    def get(self, request: Request):
        keyword = request.query_params.get("keyword")
        try:
            min_price = _parse_optional_float(request.query_params.get("min_price"))
            max_price = _parse_optional_float(request.query_params.get("max_price"))
            min_rating = _parse_optional_float(request.query_params.get("min_rating"))
        except ValueError as exc:
            return Response({"error": str(exc)}, status=400)

        service = get_product_search_service()
        results = SearchProducts(service).execute(
            query=keyword,
            min_price=min_price,
            max_price=max_price,
            min_rating=min_rating,
        )

        payload = [
            asdict(result) if isinstance(result, ProductSearchResultDTO) else result
            for result in results
        ]
        serialized = ProductSearchResultSerializer(payload, many=True)
        return Response(serialized.data, status=200)
