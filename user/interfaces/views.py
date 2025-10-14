from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, Dict

from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from user.application import (
    AddFavorite,
    CreateCustomer,
    DeleteCustomer,
    GetCustomer,
    ListCustomers,
    ListFavorites,
    RemoveFavorite,
    UpdateCustomer,
)

from user.domain import (
    CustomerNotFoundError,
    FavoriteAlreadyExistsError,
    FavoriteNotFoundError,
    ProductNotFoundError,
)
from user.infrastructure import (
    DjangoCustomerRepository,
    DjangoFavoriteRepository,
    FakeStoreProductGateway,
)


class _JSONViewMixin:
    def _load_payload(self, request) -> Dict[str, Any]:
        if not request.body:
            return {}

        try:
            return json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid JSON payload") from exc

    def _error_response(self, *, message: str, status: int, details: Dict[str, Any] | None = None):
        response_data = {"error": message}
        if details:
            response_data["details"] = details
        return JsonResponse(response_data, status=status)


class _CustomerBaseView(_JSONViewMixin, View):
    repository_class = DjangoCustomerRepository

    def dispatch(self, request, *args, **kwargs):
        self.repository = self.repository_class()
        return super().dispatch(request, *args, **kwargs)

    def _validate_payload(self, payload: Dict[str, Any]) -> Dict[str, str]:
        errors: Dict[str, str] = {}
        if not payload.get("name"):
            errors["name"] = "This field is required."
        if not payload.get("email"):
            errors["email"] = "This field is required."
        return errors


@method_decorator(csrf_exempt, name="dispatch")
class CustomerListCreateView(_CustomerBaseView):
    """Entrypoint for listing and creating customers."""

    def get(self, request):
        customers = ListCustomers(self.repository).execute()
        data = [asdict(customer) for customer in customers]
        return JsonResponse(data, status=200, safe=False)

    def post(self, request):
        try:
            payload = self._load_payload(request)
        except ValueError:
            return self._error_response(message="Invalid JSON payload.", status=400)

        errors = self._validate_payload(payload)
        if errors:
            return self._error_response(message="Invalid payload.", status=400, details=errors)

        try:
            customer = CreateCustomer(self.repository).execute(
                name=payload["name"],
                email=payload["email"],
            )
        except IntegrityError:
            return self._error_response(
                message="A customer with this email already exists.",
                status=400,
                details={"email": "Must be unique."},
            )

        return JsonResponse(asdict(customer), status=201)


@method_decorator(csrf_exempt, name="dispatch")
class CustomerDetailView(_CustomerBaseView):
    """Entrypoint for retrieving, updating, and deleting customers."""

    def get(self, request, customer_id: int):
        try:
            customer = GetCustomer(self.repository).execute(customer_id)
        except CustomerNotFoundError:
            return self._error_response(message="Customer not found.", status=404)

        return JsonResponse(asdict(customer), status=200)

    def put(self, request, customer_id: int):
        try:
            payload = self._load_payload(request)
        except ValueError:
            return self._error_response(message="Invalid JSON payload.", status=400)

        errors = self._validate_payload(payload)
        if errors:
            return self._error_response(message="Invalid payload.", status=400, details=errors)

        try:
            customer = UpdateCustomer(self.repository).execute(
                customer_id=customer_id,
                name=payload["name"],
                email=payload["email"],
            )
        except CustomerNotFoundError:
            return self._error_response(message="Customer not found.", status=404)
        except IntegrityError:
            return self._error_response(
                message="A customer with this email already exists.",
                status=400,
                details={"email": "Must be unique."},
            )

        return JsonResponse(asdict(customer), status=200)

    def delete(self, request, customer_id: int):
        try:
            DeleteCustomer(self.repository).execute(customer_id=customer_id)
        except CustomerNotFoundError:
            return self._error_response(message="Customer not found.", status=404)

        return HttpResponse(status=204)


class _FavoriteBaseView(_JSONViewMixin, View):
    repository_class = DjangoFavoriteRepository
    product_gateway_class = FakeStoreProductGateway

    def dispatch(self, request, *args, **kwargs):
        self.repository = self.repository_class()
        self.product_gateway = self.product_gateway_class()
        return super().dispatch(request, *args, **kwargs)

    def _validate_payload(self, payload: Dict[str, Any]) -> Dict[str, str]:
        errors: Dict[str, str] = {}
        if "product_id" not in payload:
            errors["product_id"] = "This field is required."
            return errors

        try:
            product_id = int(payload["product_id"])
        except (TypeError, ValueError):
            errors["product_id"] = "Must be an integer."
            return errors

        if product_id <= 0:
            errors["product_id"] = "Must be a positive integer."

        payload["product_id"] = product_id
        return errors


@method_decorator(csrf_exempt, name="dispatch")
class FavoriteListCreateView(_FavoriteBaseView):
    """List and add favorites for a specific customer."""

    def get(self, request, customer_id: int):
        try:
            favorites = ListFavorites(self.repository, self.product_gateway).execute(
                customer_id=customer_id
            )
        except CustomerNotFoundError:
            return self._error_response(message="Customer not found.", status=404)
        except RuntimeError:
            return self._error_response(
                message="Unable to fetch product details from external service.",
                status=503,
            )

        data = [asdict(favorite) for favorite in favorites]
        return JsonResponse(data, status=200, safe=False)

    def post(self, request, customer_id: int):
        try:
            payload = self._load_payload(request)
        except ValueError:
            return self._error_response(message="Invalid JSON payload.", status=400)

        errors = self._validate_payload(payload)
        if errors:
            return self._error_response(message="Invalid payload.", status=400, details=errors)

        product_id = payload["product_id"]

        try:
            favorite = AddFavorite(self.repository, self.product_gateway).execute(
                customer_id=customer_id,
                product_id=product_id,
            )
        except CustomerNotFoundError:
            return self._error_response(message="Customer not found.", status=404)
        except ProductNotFoundError:
            return self._error_response(message="Product not found.", status=404)
        except FavoriteAlreadyExistsError:
            return self._error_response(
                message="Product already marked as favorite.",
                status=400,
            )
        except RuntimeError:
            return self._error_response(
                message="Unable to validate product with external service.",
                status=503,
            )

        return JsonResponse(asdict(favorite), status=201)


@method_decorator(csrf_exempt, name="dispatch")
class FavoriteDetailView(_FavoriteBaseView):
    """Remove a favorite product from a customer."""

    def delete(self, request, customer_id: int, product_id: int):
        try:
            RemoveFavorite(self.repository).execute(
                customer_id=customer_id,
                product_id=product_id,
            )
        except (CustomerNotFoundError, FavoriteNotFoundError):
            return self._error_response(message="Favorite not found.", status=404)

        return HttpResponse(status=204)
