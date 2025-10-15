from .product_gateway import FakeStoreProductGateway
from .repositories import DjangoCustomerRepository, DjangoFavoriteRepository

__all__ = [
    "DjangoCustomerRepository",
    "DjangoFavoriteRepository",
    "FakeStoreProductGateway",
]
