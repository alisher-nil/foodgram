USER_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "number"},
        "username": {"type": "string"},
        "first_name": {"type": "string"},
        "last_name": {"type": "string"},
        "email": {"type": "string"},
        "is_subscribed": {"type": "boolean"},
    },
    "required": [
        "id",
        "username",
        "first_name",
        "last_name",
        "email",
        "is_subscribed",
    ],
    "additionalProperties": False,
}

INGREDIENT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "number"},
        "name": {"type": "string"},
        "measurement_unit": {"type": "string"},
    },
    "required": ["id", "name", "measurement_unit"],
    "additionalProperties": False,
}
RECIPE_INGREDIENT_SCHEMA = {
    **INGREDIENT_SCHEMA,
    "properties": {
        **INGREDIENT_SCHEMA["properties"],
        "amount": {"type": "number"},
    },
    "required": INGREDIENT_SCHEMA["required"] + ["amount"],
}

TAG_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "number"},
        "name": {"type": "string"},
        "color": {"type": "string"},
        "slug": {"type": "string"},
    },
    "required": ["id", "name", "color", "slug"],
    "additionalProperties": False,
}

RECIPE_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "number"},
        "tags": {
            "type": "array",
            "items": TAG_SCHEMA,
        },
        "author": USER_SCHEMA,
        "ingredients": {
            "type": "array",
            "items": RECIPE_INGREDIENT_SCHEMA,
        },
        "is_favorited": {"type": "boolean"},
        "is_in_shopping_cart": {"type": "boolean"},
        "name": {"type": "string"},
        "image": {"type": "string"},
        "text": {"type": "string"},
        "cooking_time": {"type": "number"},
    },
    "required": [
        "id",
        "tags",
        "author",
        "ingredients",
        "is_favorited",
        "is_in_shopping_cart",
        "name",
        "image",
        "text",
        "cooking_time",
    ],
    "additionalProperties": False,
}

SIMPLE_RECIPE_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "number"},
        "name": {"type": "string"},
        "image": {"type": "string"},
        "cooking_time": {"type": "number"},
    },
    "required": ["id", "name", "image", "cooking_time"],
    "additionalProperties": False,
}

SUBSCRIPTION_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "number"},
        "username": {"type": "string"},
        "first_name": {"type": "string"},
        "last_name": {"type": "string"},
        "email": {"type": "string"},
        "is_subscribed": {"type": "boolean"},
        "recipes_count": {"type": "number"},
        "recipes": {
            "type": "array",
            "items": SIMPLE_RECIPE_SCHEMA,
        },
    },
    "required": [
        "id",
        "username",
        "first_name",
        "last_name",
        "email",
        "is_subscribed",
        "recipes",
        "recipes_count",
    ],
    "additionalProperties": False,
}


def get_paginated_response_schema(item_schema: dict) -> dict:
    return {
        "type": "object",
        "properties": {
            "count": {"type": "number"},
            "next": {
                "anyOf": [{"type": "string"}, {"type": "null"}],
            },
            "previous": {
                "anyOf": [{"type": "string"}, {"type": "null"}],
            },
            "results": {
                "type": "array",
                "items": item_schema,
            },
        },
        "required": ["count", "next", "previous", "results"],
    }


def get_list_response_schema(item_schema: dict) -> dict:
    return {
        "type": "array",
        "items": item_schema,
    }


def get_subs_schema_limited_recipes(recipes_limit):
    limited_schema = SUBSCRIPTION_SCHEMA.copy()
    limited_schema["properties"]["recipes"]["maxItems"] = recipes_limit
    return limited_schema
