from catalog.domain import ProductSearchService


class SearchProducts:
    def __init__(self, service: ProductSearchService):
        self._service = service

    def execute(
        self,
        *,
        query: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        min_rating: float | None = None,
    ):
        return self._service.search(
            query=query,
            min_price=min_price,
            max_price=max_price,
            min_rating=min_rating,
        )
