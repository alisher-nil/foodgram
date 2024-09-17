import json

import pytest
from django.urls import reverse
from pytest_lazyfixture import lazy_fixture
from rest_framework import status

from api.tests.helpers.mixins import RecipeProperties
from api.tests.helpers.schemas import (
    INGREDIENT_SCHEMA,
    RECIPE_SCHEMA,
    TAG_SCHEMA,
    get_list_response_schema,
    get_paginated_response_schema,
)
from api.tests.helpers.utils import validate_response_schema
from recipes.models import Ingredient, Recipe, Tag


@pytest.mark.usefixtures("tags_bulk_create")
class TestTags(RecipeProperties):
    list_url_path = "api:tags-list"
    detail_url_path = "api:tags-detail"
    model = Tag
    list_schema = get_list_response_schema(TAG_SCHEMA)
    detail_schema = TAG_SCHEMA


@pytest.mark.usefixtures("ingredients_bulk_create")
class TestIngredients(RecipeProperties):
    list_url_path = "api:ingredients-list"
    detail_url_path = "api:ingredients-detail"
    model = Ingredient
    list_schema = get_list_response_schema(INGREDIENT_SCHEMA)
    detail_schema = INGREDIENT_SCHEMA

    def test_filtered_ingredients_list(self, param_client):
        ingredients_count = Ingredient.objects.filter(
            name__contains="1"
        ).count()
        response = param_client.get(
            reverse("api:ingredients-list"), {"name": "1"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == ingredients_count
        validate_response_schema(response, self.list_schema)


@pytest.mark.usefixtures(
    "recipes_bulk_create",
)
class TestRecipesRetrieval:
    list_url_path = "api:recipes-list"
    detail_url_path = "api:recipes-detail"
    list_schema = get_paginated_response_schema(RECIPE_SCHEMA)
    detail_schema = RECIPE_SCHEMA
    model = Recipe

    @pytest.mark.parametrize(
        "param_client",
        (
            lazy_fixture("client"),
            lazy_fixture("authorized_client"),
        ),
        ids=("anonymous user", "authorized user"),
    )
    def test_recipe_list_retrieval(self, param_client):
        response = param_client.get(reverse(self.list_url_path))
        assert response.status_code == status.HTTP_200_OK
        validate_response_schema(response, self.list_schema)

    @pytest.mark.parametrize(
        "param_client",
        (
            lazy_fixture("client"),
            lazy_fixture("authorized_client"),
        ),
        ids=("anonymous user", "authorized user"),
    )
    def test_recipe_detail_retrieval(self, param_client, user_recipe):
        response = param_client.get(
            reverse(
                self.detail_url_path,
                args=[user_recipe.id],
            )
        )
        assert response.status_code == status.HTTP_200_OK
        validate_response_schema(response, self.detail_schema)

    @pytest.mark.parametrize("limit", (1, 2, 3))
    def test_recipe_list_retrieval_with_limits(self, client, limit):
        response = client.get(
            reverse(self.list_url_path),
            {"limit": f"{limit}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["results"]) == limit
        validate_response_schema(response, self.list_schema)

    def test_recipe_list_retrieval_with_tags(self, client):
        first_tag = Tag.objects.first()
        second_tag = Tag.objects.last()
        recipe_count = Recipe.objects.filter(
            tags__in=[
                first_tag,
                second_tag,
            ]
        ).count()
        response = client.get(
            reverse(self.list_url_path),
            {"tags": [first_tag.slug, second_tag.slug]},
        )
        assert response.status_code == status.HTTP_200_OK
        validate_response_schema(response, self.list_schema)
        assert len(response.data["results"]) == recipe_count

    def test_recipe_list_retrieval_with_author(
        self, client, django_user_model
    ):
        author = django_user_model.objects.first()
        response = client.get(
            reverse(self.list_url_path), {"author": author.id}
        )
        assert response.status_code == status.HTTP_200_OK
        assert (
            len(response.data["results"])
            == Recipe.objects.filter(author=author).count()
        )
        validate_response_schema(response, self.list_schema)

    def test_recipe_list_pagination(self, client):
        recipe_count = Recipe.objects.count()
        limit = recipe_count - 1
        response = client.get(
            reverse(self.list_url_path),
            {"limit": limit, "page": 2},
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        validate_response_schema(response, self.list_schema)


class TestRecipeCreateUpdate:
    list_url_path = "api:recipes-list"
    detail_url_path = "api:recipes-detail"
    detail_schema = RECIPE_SCHEMA

    @pytest.mark.parametrize(
        "param_client, expected_status",
        (
            (lazy_fixture("client"), status.HTTP_401_UNAUTHORIZED),
            (lazy_fixture("authorized_client"), status.HTTP_201_CREATED),
        ),
        ids=("anonymous user", "authorized user"),
    )
    def test_recipe_creation(self, param_client, recipe_data, expected_status):
        recipe_count = Recipe.objects.count()
        expected_count = (
            recipe_count + 1
            if expected_status == status.HTTP_201_CREATED
            else recipe_count
        )
        # default content type `multipart/form-data` does not support complex
        # nested data, so use `application/json` is required
        response = param_client.post(
            reverse(self.list_url_path),
            data=json.dumps(recipe_data),
            content_type="application/json",
        )
        assert (
            response.status_code == expected_status
        ), "Unexpected response status"
        assert (
            Recipe.objects.count() == expected_count
        ), "Unexpected recipe count"
        if expected_status == status.HTTP_201_CREATED:
            validate_response_schema(response, self.detail_schema)

    @pytest.mark.parametrize(
        "param_client, expected_status, recipe",
        (
            (
                lazy_fixture("client"),
                status.HTTP_401_UNAUTHORIZED,
                lazy_fixture("user_recipe"),
            ),
            (
                lazy_fixture("authorized_client"),
                status.HTTP_403_FORBIDDEN,
                lazy_fixture("non_user_recipe"),
            ),
            (
                lazy_fixture("authorized_client"),
                status.HTTP_200_OK,
                lazy_fixture("user_recipe"),
            ),
        ),
        ids=("anonymous user", "non-author user", "author user"),
    )
    def test_recipe_update(
        self, param_client, recipe, expected_status, new_recipe_data
    ):
        response = param_client.patch(
            reverse(self.detail_url_path, args=[recipe.id]),
            data=json.dumps(new_recipe_data),
            content_type="application/json",
        )
        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        "missing_field",
        (
            "name",
            "text",
            "cooking_time",
            "image",
            "ingredients",
            "tags",
        ),
    )
    def test_recipe_create_missing_data(
        self, authorized_client, recipe_data, missing_field
    ):
        recipe_data.pop(missing_field)
        response = authorized_client.post(
            reverse(self.list_url_path),
            data=json.dumps(recipe_data),
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.parametrize(
        "empty_field, empty_value",
        (
            ("name", ""),
            ("text", ""),
            ("cooking_time", ""),
            ("image", ""),
            ("ingredients", []),
            ("tags", []),
        ),
        ids=(
            "name",
            "text",
            "cooking_time",
            "image",
            "ingredients",
            "tags",
        ),
    )
    @pytest.mark.parametrize(
        "method, url_path, args",
        (
            ("post", "api:recipes-list", []),
            ("patch", "api:recipes-detail", lazy_fixture("user_recipe_id")),
        ),
        ids=("create", "update"),
    )
    def test_recipe_create_update_empty_data(
        self,
        authorized_client,
        empty_field,
        empty_value,
        recipe_data,
        method,
        url_path,
        args,
    ):
        recipe_data[empty_field] = empty_value
        response = getattr(authorized_client, method)(
            reverse(url_path, args=args),
            data=json.dumps(recipe_data),
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.parametrize(
        "bad_recipe_data",
        (
            lazy_fixture("bad_tag_id_recipe_data"),
            lazy_fixture("bad_ingredient_id_recipe_data"),
            lazy_fixture("double_tag_recipe_data"),
            lazy_fixture("low_ingredient_amount_recipe_data"),
            lazy_fixture("double_ingrediend_recipe_data"),
            lazy_fixture("too_long_name_recipe_data"),
        ),
    )
    def test_bad_data(self, authorized_client, bad_recipe_data):
        response = authorized_client.post(
            reverse("api:recipes-list"),
            data=json.dumps(bad_recipe_data),
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
