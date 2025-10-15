from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class UserDTO:
    """Immutable transfer object for exposing common user data."""

    id: int
    name: str
    email: str


@dataclass(frozen=True)
class CustomerDTO(UserDTO):
    """Immutable transfer object for exposing customer data."""


@dataclass(frozen=True)
class FavoriteDTO:
    """Transfer object for customer favorite entries."""

    id: int
    customer_id: int
    product_id: int
    title: Optional[str] = None
    image: Optional[str] = None
    price: Optional[float] = None
    review: Optional[Dict[str, Any]] = None
