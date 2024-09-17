import pytest
from django.urls import reverse
from pytest_lazyfixture import lazy_fixture
from rest_framework import status

from api.tests.helpers.mixins import UserCollections
from api.tests.helpers.schemas import (
    SIMPLE_RECIPE_SCHEMA,
    SUBSCRIPTION_SCHEMA,
    get_paginated_response_schema,
    get_subs_schema_limited_recipes,
)
from api.tests.helpers.utils import validate_response_schema
from recipes.models import Favorite, ShoppingCart
from users.models import Subscription


class TestSubs:
    subscribe_url_path = "api:subscribe"
    subscriptions_url_path = "api:subscriptions"
    detail_schema = SUBSCRIPTION_SCHEMA
    list_schema = get_paginated_response_schema(SUBSCRIPTION_SCHEMA)

    @pytest.mark.parametrize(
        "param_client, expected_result",
        (
            (lazy_fixture("authorized_client"), status.HTTP_201_CREATED),
            (lazy_fixture("client"), status.HTTP_401_UNAUTHORIZED),
        ),
        ids=("anonymous user", "authorized user"),
    )
    def test_subscribe(
        self, param_client, test_user, another_user, expected_result
    ):
        response = param_client.post(
            reverse(self.subscribe_url_path, args=[another_user.id])
        )
        assert response.status_code == expected_result
        if expected_result == status.HTTP_201_CREATED:
            assert Subscription.objects.filter(
                user=test_user, author_id=another_user.id
            ).exists()

    @pytest.mark.parametrize("recipes_limit", (1, 2, 3))
    def test_subscribe_with_limits(
        self, authorized_client, prominent_author, recipes_limit
    ):
        # post method does not support query parameters
        # so the manual way is the way
        url = (
            reverse(self.subscribe_url_path, args=[prominent_author.id])
            + f"?recipes_limit={recipes_limit}"
        )
        response = authorized_client.post(url)
        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data["recipes"]) == recipes_limit
        schema = get_subs_schema_limited_recipes(recipes_limit)
        validate_response_schema(response, schema)

    def test_double_subscription(self, authorized_client, prominent_author):
        url = reverse(self.subscribe_url_path, args=[prominent_author.id])
        response = authorized_client.post(url)
        assert response.status_code == status.HTTP_201_CREATED
        response = authorized_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_self_subscription(self, authorized_client, test_user):
        url = reverse(self.subscribe_url_path, args=[test_user.id])
        response = authorized_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_nonexistent_user_subscription(
        self, authorized_client, django_user_model
    ):
        bad_id = (
            max(django_user_model.objects.values_list("id", flat=True)) + 1
        )
        url = reverse(self.subscribe_url_path, args=[bad_id])
        response = authorized_client.post(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.usefixtures("user_subscription")
    def test_unsubscribe(self, authorized_client, test_user, prominent_author):
        response = authorized_client.delete(
            reverse(self.subscribe_url_path, args=[prominent_author.id])
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Subscription.objects.filter(
            user=test_user, author=prominent_author
        ).exists()

    @pytest.mark.usefixtures("user_subscriptions_in_bulk")
    def test_retrieve_subscriptions(self, authorized_client):
        response = authorized_client.get(reverse(self.subscriptions_url_path))
        assert response.status_code == status.HTTP_200_OK
        validate_response_schema(response, self.list_schema)

    @pytest.mark.usefixtures("user_subscriptions_in_bulk")
    @pytest.mark.parametrize("limit", (1, 2, 3))
    def test_retrieve_subscriptions_limits(self, authorized_client, limit):
        response = authorized_client.get(
            reverse(self.subscriptions_url_path),
            {"limit": limit},
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == limit
        validate_response_schema(response, self.list_schema)

    @pytest.mark.usefixtures("user_subscription")
    @pytest.mark.parametrize("recipes_limit", (1, 2, 3))
    def test_retrieve_subscriptions_recipe_limits(
        self, authorized_client, recipes_limit
    ):
        response = authorized_client.get(
            reverse(self.subscriptions_url_path),
            {"recipes_limit": recipes_limit},
        )
        assert response.status_code == status.HTTP_200_OK
        schema = get_subs_schema_limited_recipes(recipes_limit)
        validate_response_schema(
            response,
            get_paginated_response_schema(schema),
        )


class TestShoppingCart(UserCollections):
    url = "api:shopping_cart"
    download_url = "api:download_shopping_cart"
    detail_schema = SIMPLE_RECIPE_SCHEMA
    model = ShoppingCart

    @pytest.mark.usefixtures("shopping_cart")
    def test_delete(self, authorized_client, user_recipe, test_user):
        super().test_delete(authorized_client, user_recipe, test_user)

    @pytest.mark.usefixtures("shopping_cart_in_bulk")
    def test_download_shopping_cart(self, authorized_client):
        response = authorized_client.get(reverse(self.download_url))
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "text/plain"
        assert (
            response["Content-Disposition"]
            == "attachment; filename=shopping_list.txt"
        )


class TestFavorites(UserCollections):
    url = "api:favorites"
    detail_schema = SIMPLE_RECIPE_SCHEMA
    model = Favorite

    @pytest.mark.usefixtures("test_favorites")
    def test_delete(self, authorized_client, user_recipe, test_user):
        super().test_delete(authorized_client, user_recipe, test_user)
