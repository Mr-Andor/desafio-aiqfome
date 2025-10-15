from __future__ import annotations

from user.domain import FavoriteDTO, FavoriteRepository, ProductGateway, ProductNotFoundError


class AddFavorite:
    """Use case for marking a product as favorite for a customer."""

    def __init__(self, repository: FavoriteRepository, product_gateway: ProductGateway):
        self._repository = repository
        self._product_gateway = product_gateway

    def execute(self, *, customer_id: int, product_id: int) -> FavoriteDTO:
        if not self._product_gateway.exists(product_id):
            raise ProductNotFoundError(product_id)

        return self._repository.add(customer_id=customer_id, product_id=product_id)


class ListFavorites:
    """Use case for listing all favorites of a customer with product details."""

    def __init__(self, repository: FavoriteRepository, product_gateway: ProductGateway):
        self._repository = repository
        self._product_gateway = product_gateway

    def execute(self, *, customer_id: int):
        favorites = self._repository.list(customer_id=customer_id)
        detailed = []
        for favorite in favorites:
            details = self._product_gateway.get_details(favorite.product_id)
            detailed.append(
                FavoriteDTO(
                    id=favorite.id,
                    customer_id=favorite.customer_id,
                    product_id=favorite.product_id,
                    title=(details or {}).get("title"),
                    image=(details or {}).get("image"),
                    price=(details or {}).get("price"),
                    review=(details or {}).get("review"),
                )
            )
        return detailed


class RemoveFavorite:
    """Use case for removing an existing favorite."""

    def __init__(self, repository: FavoriteRepository):
        self._repository = repository

    def execute(self, *, customer_id: int, product_id: int) -> None:
        self._repository.remove(customer_id=customer_id, product_id=product_id)
