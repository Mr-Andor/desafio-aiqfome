from __future__ import annotations

from typing import Sequence

from user.domain import CustomerDTO, CustomerRepository


class CreateCustomer:
    """Use case orchestrating creation of a customer."""

    def __init__(self, repository: CustomerRepository):
        self._repository = repository

    def execute(self, *, name: str, email: str) -> CustomerDTO:
        return self._repository.create(name=name, email=email)


class ListCustomers:
    """Use case returning all customers."""

    def __init__(self, repository: CustomerRepository):
        self._repository = repository

    def execute(self) -> Sequence[CustomerDTO]:
        return self._repository.list()


class GetCustomer:
    """Use case retrieving a single customer."""

    def __init__(self, repository: CustomerRepository):
        self._repository = repository

    def execute(self, customer_id: int) -> CustomerDTO:
        return self._repository.get(customer_id)


class UpdateCustomer:
    """Use case updating an existing customer."""

    def __init__(self, repository: CustomerRepository):
        self._repository = repository

    def execute(self, *, customer_id: int, name: str, email: str) -> CustomerDTO:
        return self._repository.update(
            customer_id=customer_id,
            name=name,
            email=email,
        )


class DeleteCustomer:
    """Use case deleting a customer."""

    def __init__(self, repository: CustomerRepository):
        self._repository = repository

    def execute(self, *, customer_id: int) -> None:
        self._repository.delete(customer_id)
