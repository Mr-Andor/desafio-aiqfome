from __future__ import annotations

from typing import Sequence

from django.contrib.auth import get_user_model
from user.domain import CustomerDTO, CustomerNotFoundError, CustomerRepository


class DjangoCustomerRepository(CustomerRepository):
    """Repository implementation backed by the Django ORM."""

    def __init__(self, model=None):
        self._model = model or get_user_model()

    def _to_dto(self, instance) -> CustomerDTO:
        return CustomerDTO(id=instance.id, name=instance.name, email=instance.email)

    def create(self, *, name: str, email: str) -> CustomerDTO:
        instance = self._model.objects.create_user(
            name=name,
            email=email,
            password=None,
        )
        return self._to_dto(instance)

    def list(self) -> Sequence[CustomerDTO]:
        instances = self._model.objects.order_by("id").all()
        return [self._to_dto(instance) for instance in instances]

    def get(self, customer_id: int) -> CustomerDTO:
        try:
            instance = self._model.objects.get(pk=customer_id)
        except self._model.DoesNotExist as exc:
            raise CustomerNotFoundError(customer_id) from exc
        return self._to_dto(instance)

    def update(self, *, customer_id: int, name: str, email: str) -> CustomerDTO:
        try:
            instance = self._model.objects.get(pk=customer_id)
        except self._model.DoesNotExist as exc:
            raise CustomerNotFoundError(customer_id) from exc

        instance.name = name
        instance.email = email
        instance.save(update_fields=["name", "email"])
        return self._to_dto(instance)

    def delete(self, customer_id: int) -> None:
        try:
            instance = self._model.objects.get(pk=customer_id)
        except self._model.DoesNotExist as exc:
            raise CustomerNotFoundError(customer_id) from exc

        instance.delete()
