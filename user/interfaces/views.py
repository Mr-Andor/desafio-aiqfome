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
    CreateCustomer,
    DeleteCustomer,
    GetCustomer,
    ListCustomers,
    UpdateCustomer,
)
from user.domain import CustomerNotFoundError
from user.infrastructure import DjangoCustomerRepository


class _CustomerBaseView(View):
    repository_class = DjangoCustomerRepository

    def dispatch(self, request, *args, **kwargs):
        self.repository = self.repository_class()
        return super().dispatch(request, *args, **kwargs)

    def _load_payload(self, request) -> Dict[str, Any]:
        if not request.body:
            return {}

        try:
            return json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid JSON payload") from exc

    def _validate_payload(self, payload: Dict[str, Any]) -> Dict[str, str]:
        errors: Dict[str, str] = {}
        if not payload.get("name"):
            errors["name"] = "This field is required."
        if not payload.get("email"):
            errors["email"] = "This field is required."
        return errors

    def _error_response(self, *, message: str, status: int, details: Dict[str, Any] | None = None):
        response_data = {"error": message}
        if details:
            response_data["details"] = details
        return JsonResponse(response_data, status=status)


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
