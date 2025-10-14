class CustomerNotFoundError(Exception):
    """Raised when a customer could not be found in the repository."""

    def __init__(self, customer_id: int):
        super().__init__(f"Customer with id={customer_id} was not found.")
        self.customer_id = customer_id
