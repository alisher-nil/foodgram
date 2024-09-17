import pytest
from django.urls import reverse
from pytest_lazyfixture import lazy_fixture
from rest_framework import status

from api.tests.helpers.utils import validate_response_schema
from recipes.models import Recipe


@pytest.mark.parametrize(
    "param_client",
    (
        lazy_fixture("client"),
        lazy_fixture("authorized_client"),
    ),
    ids=("anonymous user", "authorized user"),
)
class RecipeProperties:
    list_url_path = None
    detail_url_path = None
    model = None
    list_schema = None
    detail_schema = None

    def test_items_list_retrieval(self, param_client):
        response = param_client.get(reverse(self.list_url_path))
        assert response.status_code == status.HTTP_200_OK
        validate_response_schema(response, self.list_schema)

    def test_item_detail_retrieval(self, param_client):
        item = self.model.objects.first()
        response = param_client.get(
            reverse(self.detail_url_path, args=[item.id])
        )
        assert response.status_code == status.HTTP_200_OK
        validate_response_schema(response, self.detail_schema)

    def test_non_existent_item_detail_retrieval(self, param_client):
        max_id = max(self.model.objects.values_list("id", flat=True))
        response = param_client.get(
            reverse(
                self.detail_url_path,
                args=[max_id + 1],
            )
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize(
        "method, url_path",
        (
            ("put", "api:tags-detail"),
            ("patch", "api:tags-detail"),
            ("delete", "api:tags-detail"),
            ("post", "api:tags-list"),
        ),
        ids=("put", "patch", "delete", "post"),
    )
    def test_bad_methods(self, param_client, method, url_path):
        item = self.model.objects.last()
        url = reverse(url_path, args=[item.id] if "detail" in url_path else [])
        response = getattr(param_client, method)(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


class UserCollections:
    url = None
    detail_schema = None
    model = None

    @pytest.mark.parametrize(
        "param_client, expected_result",
        (
            (lazy_fixture("authorized_client"), status.HTTP_201_CREATED),
            (lazy_fixture("client"), status.HTTP_401_UNAUTHORIZED),
        ),
        ids=("anonymous user", "authorized user"),
    )
    def test_add(self, param_client, user_recipe, test_user, expected_result):
        response = param_client.post(reverse(self.url, args=[user_recipe.id]))
        assert response.status_code == expected_result
        if expected_result == status.HTTP_201_CREATED:
            assert self.model.objects.filter(
                user=test_user, recipe=user_recipe
            ).exists()
            validate_response_schema(response, self.detail_schema)

    def test_double_add(self, authorized_client, user_recipe):
        url = reverse(self.url, args=[user_recipe.id])
        response = authorized_client.post(url)
        assert response.status_code == status.HTTP_201_CREATED
        response = authorized_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.usefixtures("user_recipe")
    def test_nonexistent_recipe(self, authorized_client):
        bad_id = max(Recipe.objects.values_list("id", flat=True)) + 1
        response = authorized_client.post(reverse(self.url, args=[bad_id]))
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_delete(self, authorized_client, user_recipe, test_user):
        response = authorized_client.delete(
            reverse(self.url, args=[user_recipe.id])
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not self.model.objects.filter(
            recipe=user_recipe,
            user=test_user,
        ).exists()
