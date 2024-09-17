import pytest
from django.urls import reverse
from djoser.conf import settings as djoser_settings
from pytest_lazyfixture import lazy_fixture
from rest_framework import status

from api.tests.helpers.schemas import (
    USER_SCHEMA,
    get_paginated_response_schema,
)
from api.tests.helpers.utils import (
    bad_user_creation_count_assertion,
    validate_response_schema,
)
from foodgram_backend.constants import (
    USER_EMAIL_MAX_LENGTH,
    USER_FIRST_NAME_MAX_LENGTH,
    USER_LAST_NAME_MAX_LENGTH,
    USER_USERNAME_MAX_LENGTH,
)


@pytest.mark.usefixtures("db")
class TestSignUpEndpoints:
    users_url = reverse("api:users-list")

    def test_user_creation(self, client, test_user_data, django_user_model):
        initial_user_count = django_user_model.objects.count()
        response = client.post(self.users_url, data=test_user_data)

        assert response.status_code == status.HTTP_201_CREATED
        assert django_user_model.objects.count() == initial_user_count + 1
        test_user_data.pop("password")
        assert django_user_model.objects.filter(**test_user_data).exists()

    @pytest.mark.parametrize(
        "missing_field",
        (
            "email",
            "username",
            "first_name",
            "last_name",
            "password",
        ),
    )
    @bad_user_creation_count_assertion
    def test_user_creation_with_missing_data(
        self, client, test_user_data, missing_field
    ):
        test_user_data.pop(missing_field)
        response = client.post(self.users_url, data=test_user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.parametrize(
        "field_name, limit",
        (
            ("email", USER_EMAIL_MAX_LENGTH),
            ("username", USER_USERNAME_MAX_LENGTH),
            ("first_name", USER_FIRST_NAME_MAX_LENGTH),
            ("last_name", USER_LAST_NAME_MAX_LENGTH),
        ),
    )
    @bad_user_creation_count_assertion
    def test_user_creation_with_too_long_fields(
        self, client, test_user_data, field_name, limit
    ):
        mail_postfix = "@mail.com"
        test_user_data[field_name] = (
            "a" * (limit + 1)
            if field_name != "email"
            else f"{'a' * (limit + 1 - len(mail_postfix))}{mail_postfix}"
        )
        response = client.post(self.users_url, data=test_user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.parametrize(
        "invalid_character",
        (
            "!",
            "#",
            "$",
            "%",
            "^",
            "&",
            "*",
            "(",
            ")",
            "=",
            "[",
            "]",
            "{",
            "}",
            ";",
            ":",
            ",",
            "<",
            ">",
            "?",
            "/",
            "\\",
            "|",
            "~",
            "`",
        ),
    )
    @bad_user_creation_count_assertion
    def test_invalid_username(self, client, test_user_data, invalid_character):
        test_user_data["username"] = (
            test_user_data["username"] + invalid_character
        )
        response = client.post(self.users_url, data=test_user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST, (
            "Response status code with username "
            f"{test_user_data['username']} is not 400"
        )

    @pytest.mark.usefixtures("test_user")
    @pytest.mark.parametrize("fail_field", ("email", "username"))
    @bad_user_creation_count_assertion
    def test_taken_credentials(
        self, client, another_user_data, test_user_data, fail_field
    ):
        another_user_data[fail_field] = test_user_data[fail_field]
        response = client.post(self.users_url, data=another_user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert fail_field in response.data
        assert response.data[fail_field].pop().code == "unique"


@pytest.mark.usefixtures("test_user")
class TestLoginLogoutEndpoints:
    login_url = reverse("api:login")
    logout_url = reverse("api:logout")

    @pytest.mark.parametrize(
        "credentials, expected_status",
        (
            (
                {
                    "email": lazy_fixture("test_user_email"),
                    "password": "not_a_password",
                },
                status.HTTP_400_BAD_REQUEST,
            ),
            (
                {
                    "email": "not@email.com",
                    "password": lazy_fixture("test_user_password"),
                },
                status.HTTP_400_BAD_REQUEST,
            ),
            (
                {"email": lazy_fixture("test_user_email")},
                status.HTTP_400_BAD_REQUEST,
            ),
            (
                {"password": lazy_fixture("test_user_password")},
                status.HTTP_400_BAD_REQUEST,
            ),
            (
                lazy_fixture("user_login_credentials"),
                status.HTTP_200_OK,
            ),
        ),
        ids=(
            "wrong password",
            "wrong email",
            "no password",
            "no email",
            "valid credentials",
        ),
    )
    def test_token_acquisition(
        self, test_user, client, credentials, expected_status
    ):
        response = client.post(self.login_url, data=credentials)

        assert response.status_code == expected_status
        if expected_status == status.HTTP_200_OK:
            assert "auth_token" in response.data
            assert djoser_settings.TOKEN_MODEL.objects.filter(
                user=test_user,
                key=response.data["auth_token"],
            ).exists()
            assert test_user.is_authenticated

    def test_logout(self, test_user, authorized_client):
        response = authorized_client.post(self.logout_url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not djoser_settings.TOKEN_MODEL.objects.filter(
            user=test_user
        ).exists()

    @pytest.mark.parametrize(
        "param_client, valid_client",
        (
            (lazy_fixture("client"), False),
            (lazy_fixture("authorized_client"), True),
        ),
        ids=("anonymous user", "authorized user"),
    )
    @pytest.mark.parametrize(
        "password, valid_pass",
        (
            (lazy_fixture("test_user_password"), True),
            ("not_a_password", False),
        ),
        ids=("valid password", "invalid password"),
    )
    def test_password_reset(
        self, param_client, valid_client, password, valid_pass
    ):
        expected_status = status.HTTP_204_NO_CONTENT
        if not valid_client:
            expected_status = status.HTTP_401_UNAUTHORIZED
        elif not valid_pass:
            expected_status = status.HTTP_400_BAD_REQUEST

        response = param_client.post(
            reverse("api:users-set-password"),
            data={
                "new_password": "new_password",
                "current_password": password,
            },
        )
        assert (
            response.status_code == expected_status
        ), f"Response status code is not {expected_status}"


@pytest.mark.usefixtures("users_bulk_create")
class TestUserRetrievalEndpoints:
    users_url = reverse("api:users-list")
    list_schema = get_paginated_response_schema(USER_SCHEMA)
    detail_schema = USER_SCHEMA

    @pytest.mark.parametrize(
        "param_client",
        (
            lazy_fixture("client"),
            lazy_fixture("authorized_client"),
        ),
        ids=("anonymous user", "authorized user"),
    )
    def test_user_list(self, param_client):
        response = param_client.get(self.users_url)
        assert (
            response.status_code == status.HTTP_200_OK
        ), "Response status code is not 200"
        validate_response_schema(response, self.list_schema)

    @pytest.mark.parametrize("limit", (1, 2, 3))
    def test_user_list_with_limits(self, client, limit):
        path_param = f"?limit={limit}"
        response = client.get(self.users_url + path_param)
        assert (
            response.status_code == status.HTTP_200_OK
        ), "Response status code is not 200"
        assert (
            len(response.data["results"]) == limit
        ), "Results count is not equal to the limit"

    @pytest.mark.parametrize(
        "param_client",
        (
            lazy_fixture("client"),
            lazy_fixture("authorized_client"),
        ),
        ids=("anonymous user", "authorized user"),
    )
    def test_profile_retrieval(self, test_user, param_client):
        response = param_client.get(f"{self.users_url}{test_user.id}/")
        assert (
            response.status_code == status.HTTP_200_OK
        ), "Response status code is not 200"
        validate_response_schema(response, self.detail_schema)

    def test_non_existent_profile_retrieval(self, client, django_user_model):
        last_id = django_user_model.objects.last().id
        response = client.get(f"{self.users_url}{last_id+1}/")
        assert (
            response.status_code == status.HTTP_404_NOT_FOUND
        ), "Response status code is not 404"

    @pytest.mark.parametrize(
        "param_client, expected_status",
        (
            (lazy_fixture("client"), status.HTTP_401_UNAUTHORIZED),
            (lazy_fixture("authorized_client"), status.HTTP_200_OK),
        ),
        ids=("anonymous user", "authorized user"),
    )
    def test_me_retrieval(self, test_user, param_client, expected_status):
        response = param_client.get(reverse("api:users-me"))
        assert (
            response.status_code == expected_status
        ), f"Response status code is not {expected_status}"

        if expected_status == status.HTTP_200_OK:
            validate_response_schema(response, self.detail_schema)
            assert (
                response.data["id"] == test_user.id
            ), "User id is not correct"
