class CustomerNotFoundError(Exception):
    """Raised when a customer could not be found in the repository."""

    def __init__(self, customer_id: int):
        super().__init__(f"Customer with id={customer_id} was not found.")
        self.customer_id = customer_id


class ProductNotFoundError(Exception):
    """Raised when a product could not be validated against the external API."""

    def __init__(self, product_id: int):
        super().__init__(f"Product with id={product_id} was not found in the catalog.")
        self.product_id = product_id


class FavoriteAlreadyExistsError(Exception):
    """Raised when attempting to re-add an existing favorite for a customer."""

    def __init__(self, customer_id: int, product_id: int):
        super().__init__(
            f"Customer with id={customer_id} already marked product id={product_id} as favorite."
        )
        self.customer_id = customer_id
        self.product_id = product_id


class FavoriteNotFoundError(Exception):
    """Raised when attempting to remove a favorite that does not exist."""

    def __init__(self, customer_id: int, product_id: int):
        super().__init__(
            f"Customer with id={customer_id} does not have product id={product_id} as favorite."
        )
        self.customer_id = customer_id
        self.product_id = product_id
