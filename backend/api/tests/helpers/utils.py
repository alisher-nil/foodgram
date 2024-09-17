import functools

import pytest
from django.contrib.auth import get_user_model
from jsonschema import validate
from jsonschema.exceptions import ValidationError

User = get_user_model()


def bad_user_creation_count_assertion(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        initial_user_count = User.objects.count()
        func(*args, **kwargs)
        assert (
            User.objects.count() == initial_user_count
        ), "User is created with invalid data"

    return wrapper


def validate_response_schema(response, schema):
    try:
        validate(response.json(), schema)
    except ValidationError as e:
        pytest.fail(f"Response schema validation failed: {e.message}")
