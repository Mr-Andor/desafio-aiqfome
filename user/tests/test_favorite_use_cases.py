from django.test import TestCase

from user.application import CreateCustomer
from user.application.favorite_use_cases import AddFavorite, ListFavorites, RemoveFavorite
from user.domain.exceptions import FavoriteAlreadyExistsError, FavoriteNotFoundError, ProductNotFoundError
from user.infrastructure.repositories import DjangoCustomerRepository, DjangoFavoriteRepository


class StubProductGateway:
    def __init__(self, existing_ids=None, details=None):
        self.existing_ids = set(existing_ids or [])
        self.details = details or {}

    def exists(self, product_id: int) -> bool:
        return product_id in self.existing_ids

    def get_details(self, product_id: int):
        return self.details.get(product_id)


class FavoriteUseCaseTests(TestCase):
    def setUp(self):
        self.customer_repo = DjangoCustomerRepository()
        self.favorite_repo = DjangoFavoriteRepository()
        self.product_gateway = StubProductGateway(
            existing_ids={1, 2, 3},
            details={
                1: {"title": "Vorpal Sword", "image": "vorpal_sword.png", "price": 199.99, "review": {"rate": 5}},
                2: {"title": "Deck of Many Things", "image": "deck.png", "price": 49.5, "review": {"rate": 4.5}},
                3: {"title": "Bag of Holding", "image": "bag.png", "price": 120.0, "review": None},
            },
        )

        self.customer = CreateCustomer(self.customer_repo).execute(
            name="Mordenkainen",
            email="mordenkainen@greyhawk.example",
            password="wizard123",
        )

    def test_add_favorite_persists_product(self):
        favorite = AddFavorite(self.favorite_repo, self.product_gateway).execute(
            customer_id=self.customer.id,
            product_id=1,
        )

        self.assertEqual(favorite.customer_id, self.customer.id)
        self.assertEqual(favorite.product_id, 1)

    def test_add_favorite_requires_valid_product(self):
        use_case = AddFavorite(self.favorite_repo, StubProductGateway(existing_ids={}))

        with self.assertRaises(ProductNotFoundError):
            use_case.execute(customer_id=self.customer.id, product_id=999)

    def test_cannot_duplicate_favorite(self):
        use_case = AddFavorite(self.favorite_repo, self.product_gateway)
        use_case.execute(customer_id=self.customer.id, product_id=2)

        with self.assertRaises(FavoriteAlreadyExistsError):
            use_case.execute(customer_id=self.customer.id, product_id=2)

    def test_list_favorites_returns_all_for_customer(self):
        add = AddFavorite(self.favorite_repo, self.product_gateway)
        add.execute(customer_id=self.customer.id, product_id=1)
        add.execute(customer_id=self.customer.id, product_id=2)

        favorites = ListFavorites(self.favorite_repo, self.product_gateway).execute(
            customer_id=self.customer.id
        )

        self.assertEqual({fav.product_id for fav in favorites}, {1, 2})
        favorite = next(fav for fav in favorites if fav.product_id == 1)
        self.assertEqual(favorite.title, "Vorpal Sword")
        self.assertEqual(favorite.image, "vorpal_sword.png")
        self.assertEqual(favorite.price, 199.99)
        self.assertEqual(favorite.review, {"rate": 5})

    def test_remove_favorite_deletes_entry(self):
        add = AddFavorite(self.favorite_repo, self.product_gateway)
        add.execute(customer_id=self.customer.id, product_id=3)

        RemoveFavorite(self.favorite_repo).execute(customer_id=self.customer.id, product_id=3)

        favorites = ListFavorites(self.favorite_repo, self.product_gateway).execute(
            customer_id=self.customer.id
        )
        self.assertEqual(len(favorites), 0)

    def test_remove_favorite_raises_when_missing(self):
        with self.assertRaises(FavoriteNotFoundError):
            RemoveFavorite(self.favorite_repo).execute(customer_id=self.customer.id, product_id=77)
