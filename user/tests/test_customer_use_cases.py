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
            name="Elminster Aumar",
            email="elminster@candlekeep.example",
            password="mystra123",
        )

        self.assertIsNotNone(customer.id)
        self.assertEqual(customer.name, "Elminster Aumar")
        self.assertEqual(customer.email, "elminster@candlekeep.example")

    def test_list_customers_returns_all_customers(self):
        self.create_use_case.execute(
            name="Laeral Silverhand",
            email="laeral@waterdeep.example",
            password="harpers123",
        )
        self.create_use_case.execute(
            name="Bruenor Battlehammer",
            email="bruenor@mithral.example",
            password="forge123",
        )

        customers = ListCustomers(self.repository).execute()

        self.assertEqual(len(customers), 2)
        self.assertEqual(
            sorted(customer.email for customer in customers),
            ["bruenor@mithral.example", "laeral@waterdeep.example"],
        )

    def test_get_customer_returns_matching_customer(self):
        created = self.create_use_case.execute(
            name="Drizzt DoUrden",
            email="drizzt@faerun.example",
            password="panther123",
        )

        found = GetCustomer(self.repository).execute(created.id)

        self.assertEqual(found.id, created.id)
        self.assertEqual(found.name, "Drizzt DoUrden")
        self.assertEqual(found.email, "drizzt@faerun.example")

    def test_get_customer_raises_when_not_found(self):
        with self.assertRaises(CustomerNotFoundError):
            GetCustomer(self.repository).execute(customer_id=999)

    def test_update_customer_changes_persisted_fields(self):
        created = self.create_use_case.execute(
            name="Jarlaxle Baenre",
            email="jarlaxle@bregandarthe.example",
            password="hat123",
        )

        updated = UpdateCustomer(self.repository).execute(
            customer_id=created.id,
            name="Captain Jarlaxle",
            email="jarlaxle@luskan.example",
        )

        self.assertEqual(updated.name, "Captain Jarlaxle")
        self.assertEqual(updated.email, "jarlaxle@luskan.example")

    def test_delete_customer_removes_record(self):
        created = self.create_use_case.execute(
            name="Catti-brie",
            email="catti@silverymoon.example",
            password="bow123",
        )

        DeleteCustomer(self.repository).execute(customer_id=created.id)

        with self.assertRaises(CustomerNotFoundError):
            GetCustomer(self.repository).execute(customer_id=created.id)
