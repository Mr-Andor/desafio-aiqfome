from __future__ import annotations

from typing import Protocol, runtime_checkable, Sequence

from .entities import CustomerDTO


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
