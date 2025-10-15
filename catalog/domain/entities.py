from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ProductSearchResultDTO:
    id: int
    title: str
    description: str
    price: float
    rating: Optional[float] = None
    image: Optional[str] = None
