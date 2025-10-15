from typing import Protocol, Sequence

from .entities import ProductSearchResultDTO


class ProductSearchService(Protocol):
    def search(
        self,
        *,
        query: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        min_rating: float | None = None,
    ) -> Sequence[ProductSearchResultDTO]:
        ...
