from __future__ import annotations

from typing import Any, Dict, Optional, Protocol, Sequence, runtime_checkable

from .entities import CustomerDTO, FavoriteDTO


@runtime_checkable
class CustomerRepository(Protocol):
    """Repository abstraction for Customer persistence."""

    def create(self, *, name: str, email: str) -> CustomerDTO:
        ...

    def list(self) -> Sequence[CustomerDTO]:
        ...

    def get(self, customer_id: int) -> CustomerDTO:
        ...

    def update(self, *, customer_id: int, name: str, email: str) -> CustomerDTO:
        ...

    def delete(self, customer_id: int) -> None:
        ...


@runtime_checkable
class FavoriteRepository(Protocol):
    """Repository abstraction for managing customer favorites."""

    def add(self, *, customer_id: int, product_id: int) -> FavoriteDTO:
        ...

    def list(self, *, customer_id: int) -> Sequence[FavoriteDTO]:
        ...

    def remove(self, *, customer_id: int, product_id: int) -> None:
        ...


@runtime_checkable
class ProductGateway(Protocol):
    """Integration contract for external product catalogue validation."""

    def exists(self, product_id: int) -> bool:
        ...

    def get_details(self, product_id: int) -> Optional[Dict[str, Any]]:
        ...
