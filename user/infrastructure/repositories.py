from __future__ import annotations

from typing import Sequence

from django.contrib.auth import get_user_model
from django.db import IntegrityError

from user.domain import (
    CustomerDTO,
    CustomerNotFoundError,
    CustomerRepository,
    FavoriteAlreadyExistsError,
    FavoriteDTO,
    FavoriteNotFoundError,
    FavoriteRepository,
)
from user.models import Favorite


class DjangoCustomerRepository(CustomerRepository):
    """Repository implementation backed by the Django ORM."""

    def __init__(self, model=None):
        self._model = model or get_user_model()

    def _to_dto(self, instance) -> CustomerDTO:
        return CustomerDTO(id=instance.id, name=instance.name, email=instance.email)

    def create(self, *, name: str, email: str, password: str) -> CustomerDTO:
        instance = self._model.objects.create_user(
            name=name,
            email=email,
            password=password,
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


class DjangoFavoriteRepository(FavoriteRepository):
    """Favorite repository backed by Django ORM models."""

    def __init__(self, favorite_model=None, customer_model=None):
        self._favorite_model = favorite_model or Favorite
        self._customer_model = customer_model or get_user_model()

    def _get_customer(self, customer_id: int):
        try:
            return self._customer_model.objects.get(pk=customer_id)
        except self._customer_model.DoesNotExist as exc:
            raise CustomerNotFoundError(customer_id) from exc

    def _to_dto(self, instance) -> FavoriteDTO:
        return FavoriteDTO(
            id=instance.id,
            customer_id=instance.customer_id,
            product_id=instance.product_id,
        )

    def add(self, *, customer_id: int, product_id: int) -> FavoriteDTO:
        customer = self._get_customer(customer_id)
        try:
            instance = self._favorite_model.objects.create(
                customer=customer,
                product_id=product_id,
            )
        except IntegrityError as exc:
            raise FavoriteAlreadyExistsError(customer_id, product_id) from exc

        return self._to_dto(instance)

    def list(self, *, customer_id: int) -> Sequence[FavoriteDTO]:
        self._get_customer(customer_id)
        instances = self._favorite_model.objects.filter(customer_id=customer_id).order_by("id")
        return [self._to_dto(instance) for instance in instances]

    def remove(self, *, customer_id: int, product_id: int) -> None:
        self._get_customer(customer_id)
        deleted, _ = self._favorite_model.objects.filter(
            customer_id=customer_id,
            product_id=product_id,
        ).delete()
        if deleted == 0:
            raise FavoriteNotFoundError(customer_id, product_id)
