from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from typing import Any, Dict

from django.db import IntegrityError

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.exceptions import (
    AuthenticationFailed,
    NotAuthenticated,
    ParseError,
    PermissionDenied,
)
from rest_framework.permissions import AllowAny, BasePermission, IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

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
from user.interfaces.serializers import (
    CustomerCreateInputSerializer,
    CustomerInputSerializer,
    CustomerOutputSerializer,
    FavoriteCreateSerializer,
    FavoriteOutputSerializer,
)


class _JSONViewMixin:
    def _load_payload(self, request: Request) -> Dict[str, Any]:
        try:
            data = request.data
        except ParseError as exc:
            raise ValueError("Invalid JSON payload") from exc
        if data is None:
            return {}
        if isinstance(data, Mapping):
            return dict(data)
        return data

    def _error_response(
        self,
        *,
        message: str,
        status: int,
        details: Dict[str, Any] | None = None,
    ) -> Response:
        response_data = {"error": message}
        if details:
            response_data["details"] = details
        return Response(response_data, status=status)

    def _forbidden_response(self) -> Response:
        return self._error_response(
            message="You do not have permission to perform this action.",
            status=403,
        )


class _BaseAPIView(_JSONViewMixin, APIView):
    """Base API view providing consistent error handling for auth failures."""

    www_authenticate_header = "Bearer"

    def handle_exception(self, exc):
        if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
            response = self._error_response(message=str(exc.detail), status=401)
            response["WWW-Authenticate"] = getattr(exc, "auth_header", None) or self.www_authenticate_header
            return response

        if isinstance(exc, PermissionDenied):
            return self._forbidden_response()

        return super().handle_exception(exc)


class IsStaffOrTargetCustomer(BasePermission):
    """Allow access to staff users or to the customer matching the route."""

    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        customer_id = view.kwargs.get("customer_id")
        if customer_id is None:
            return user.is_staff

        return user.is_staff or user.id == customer_id


class _CustomerBaseView(_BaseAPIView):
    repository_class = DjangoCustomerRepository

    def dispatch(self, request, *args, **kwargs):
        self.repository = self.repository_class()
        return super().dispatch(request, *args, **kwargs)


class CustomerListCreateView(_CustomerBaseView):
    """Entrypoint for listing and creating customers."""

    def get_permissions(self):
        if self.request.method.lower() == "post":
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminUser()]

    @extend_schema(
        summary="List customers",
        description="Return all registered customers. Requires staff credentials.",
        responses={200: CustomerOutputSerializer(many=True)},
        auth=[{'BearerAuth': []}],
    )
    def get(self, request: Request):
        customers = ListCustomers(self.repository).execute()
        data = [asdict(customer) for customer in customers]
        return Response(data, status=200)

    @extend_schema(
        summary="Create customer",
        description="Register a new customer. Authentication is optional for this action.",
        request=CustomerCreateInputSerializer,
        responses={
            201: CustomerOutputSerializer,
            400: OpenApiResponse(description="Invalid payload or duplicated email."),
        },
        auth=[],
    )
    def post(self, request: Request):
        try:
            payload = self._load_payload(request)
        except ValueError:
            return self._error_response(message="Invalid JSON payload.", status=400)

        serializer = CustomerCreateInputSerializer(data=payload)
        if not serializer.is_valid():
            return self._error_response(
                message="Invalid payload.",
                status=400,
                details=serializer.errors,
            )

        try:
            customer = CreateCustomer(self.repository).execute(
                name=serializer.validated_data["name"],
                email=serializer.validated_data["email"],
                password=serializer.validated_data["password"],
            )
        except IntegrityError:
            return self._error_response(
                message="A customer with this email already exists.",
                status=400,
                details={"email": "Must be unique."},
            )

        return Response(asdict(customer), status=201)


class CustomerDetailView(_CustomerBaseView):
    """Entrypoint for retrieving, updating, and deleting customers."""

    permission_classes = [IsAuthenticated, IsStaffOrTargetCustomer]

    @extend_schema(
        summary="Retrieve customer",
        responses={
            200: CustomerOutputSerializer,
            404: OpenApiResponse(description="Customer not found."),
        },
        auth=[{'BearerAuth': []}],
    )
    def get(self, request: Request, customer_id: int):
        try:
            customer = GetCustomer(self.repository).execute(customer_id)
        except CustomerNotFoundError:
            return self._error_response(message="Customer not found.", status=404)

        return Response(asdict(customer), status=200)

    @extend_schema(
        summary="Update customer",
        request=CustomerInputSerializer,
        responses={
            200: CustomerOutputSerializer,
            400: OpenApiResponse(description="Invalid payload or duplicated email."),
            404: OpenApiResponse(description="Customer not found."),
        },
        auth=[{'BearerAuth': []}],
    )
    def put(self, request: Request, customer_id: int):
        try:
            payload = self._load_payload(request)
        except ValueError:
            return self._error_response(message="Invalid JSON payload.", status=400)

        serializer = CustomerInputSerializer(data=payload)
        if not serializer.is_valid():
            return self._error_response(
                message="Invalid payload.",
                status=400,
                details=serializer.errors,
            )

        try:
            customer = UpdateCustomer(self.repository).execute(
                customer_id=customer_id,
                name=serializer.validated_data["name"],
                email=serializer.validated_data["email"],
            )
        except CustomerNotFoundError:
            return self._error_response(message="Customer not found.", status=404)
        except IntegrityError:
            return self._error_response(
                message="A customer with this email already exists.",
                status=400,
                details={"email": "Must be unique."},
            )

        return Response(asdict(customer), status=200)

    @extend_schema(
        summary="Delete customer",
        responses={
            204: OpenApiResponse(description="Customer removed."),
            404: OpenApiResponse(description="Customer not found."),
        },
        auth=[{'BearerAuth': []}],
    )
    def delete(self, request: Request, customer_id: int):
        try:
            DeleteCustomer(self.repository).execute(customer_id=customer_id)
        except CustomerNotFoundError:
            return self._error_response(message="Customer not found.", status=404)

        return Response(status=204)


class _FavoriteBaseView(_BaseAPIView):
    repository_class = DjangoFavoriteRepository
    product_gateway_class = FakeStoreProductGateway

    def dispatch(self, request, *args, **kwargs):
        self.repository = self.repository_class()
        self.product_gateway = self.product_gateway_class()
        return super().dispatch(request, *args, **kwargs)

class FavoriteListCreateView(_FavoriteBaseView):
    """List and add favorites for a specific customer."""

    permission_classes = [IsAuthenticated, IsStaffOrTargetCustomer]

    @extend_schema(
        summary="List favorites",
        description="Return the favorite products stored for the given customer.",
        responses={
            200: FavoriteOutputSerializer(many=True),
            404: OpenApiResponse(description="Customer not found."),
            503: OpenApiResponse(description="External product service unavailable."),
        },
        auth=[{'BearerAuth': []}],
    )
    def get(self, request: Request, customer_id: int):
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
        return Response(data, status=200)

    @extend_schema(
        summary="Add favorite",
        request=FavoriteCreateSerializer,
        responses={
            201: FavoriteOutputSerializer,
            400: OpenApiResponse(description="Invalid payload or favorite already registered."),
            404: OpenApiResponse(description="Customer or product not found."),
            503: OpenApiResponse(description="External product service unavailable."),
        },
        auth=[{'BearerAuth': []}],
    )
    def post(self, request: Request, customer_id: int):
        try:
            payload = self._load_payload(request)
        except ValueError:
            return self._error_response(message="Invalid JSON payload.", status=400)

        serializer = FavoriteCreateSerializer(data=payload)
        if not serializer.is_valid():
            return self._error_response(
                message="Invalid payload.",
                status=400,
                details=serializer.errors,
            )

        product_id = serializer.validated_data["product_id"]

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

        return Response(asdict(favorite), status=201)


class FavoriteDetailView(_FavoriteBaseView):
    """Remove a favorite product from a customer."""

    permission_classes = [IsAuthenticated, IsStaffOrTargetCustomer]

    @extend_schema(
        summary="Remove favorite",
        responses={
            204: OpenApiResponse(description="Favorite removed."),
            404: OpenApiResponse(description="Favorite not found."),
        },
        auth=[{'BearerAuth': []}],
    )
    def delete(self, request: Request, customer_id: int, product_id: int):
        try:
            RemoveFavorite(self.repository).execute(
                customer_id=customer_id,
                product_id=product_id,
            )
        except (CustomerNotFoundError, FavoriteNotFoundError):
            return self._error_response(message="Favorite not found.", status=404)

        return Response(status=204)
