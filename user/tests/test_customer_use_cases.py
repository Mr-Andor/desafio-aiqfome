from django.test import TestCase

from user.application.use_cases import (
    CreateCustomer,
    DeleteCustomer,
    GetCustomer,
    ListCustomers,
    UpdateCustomer,
)
from user.domain.exceptions import CustomerNotFoundError
from user.infrastructure.repositories import DjangoCustomerRepository


class CustomerUseCaseTests(TestCase):
    def setUp(self):
        self.repository = DjangoCustomerRepository()
        self.create_use_case = CreateCustomer(self.repository)

    def test_create_customer_returns_dto(self):
        customer = self.create_use_case.execute(
            name="Luke Skywalker",
            email="luke@rebellion.example",
        )

        self.assertIsNotNone(customer.id)
        self.assertEqual(customer.name, "Luke Skywalker")
        self.assertEqual(customer.email, "luke@rebellion.example")

    def test_list_customers_returns_all_customers(self):
        self.create_use_case.execute(
            name="Leia Organa",
            email="leia@rebellion.example",
        )
        self.create_use_case.execute(
            name="Han Solo",
            email="han@falcon.example",
        )

        customers = ListCustomers(self.repository).execute()

        self.assertEqual(len(customers), 2)
        self.assertEqual(
            sorted(customer.email for customer in customers),
            ["han@falcon.example", "leia@rebellion.example"],
        )

    def test_get_customer_returns_matching_customer(self):
        created = self.create_use_case.execute(
            name="Rey Skywalker",
            email="rey@jedi.example",
        )

        found = GetCustomer(self.repository).execute(created.id)

        self.assertEqual(found.id, created.id)
        self.assertEqual(found.name, "Rey Skywalker")
        self.assertEqual(found.email, "rey@jedi.example")

    def test_get_customer_raises_when_not_found(self):
        with self.assertRaises(CustomerNotFoundError):
            GetCustomer(self.repository).execute(customer_id=999)

    def test_update_customer_changes_persisted_fields(self):
        created = self.create_use_case.execute(
            name="Finn",
            email="finn@resistance.example",
        )

        updated = UpdateCustomer(self.repository).execute(
            customer_id=created.id,
            name="FN-2187",
            email="fn2187@resistance.example",
        )

        self.assertEqual(updated.name, "FN-2187")
        self.assertEqual(updated.email, "fn2187@resistance.example")

    def test_delete_customer_removes_record(self):
        created = self.create_use_case.execute(
            name="Poe Dameron",
            email="poe@resistance.example",
        )

        DeleteCustomer(self.repository).execute(customer_id=created.id)

        with self.assertRaises(CustomerNotFoundError):
            GetCustomer(self.repository).execute(customer_id=created.id)
