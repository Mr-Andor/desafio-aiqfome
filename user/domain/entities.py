from dataclasses import dataclass


@dataclass(frozen=True)
class CustomerDTO:
    """Immutable transfer object for exposing customer data."""

    id: int
    name: str
    email: str
