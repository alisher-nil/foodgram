import pytest
from djoser.conf import settings

from foodgram_backend.constants import DEFAULT_CHAR_FIELD_LENGTH
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredientAmount,
    ShoppingCart,
    Tag,
)
from users.models import Subscription


@pytest.fixture
def test_user_email():
    return "sandwitch@royal.com"


@pytest.fixture
def test_user_password():
    return "6dpCnL53MJ8ZvD5p"


@pytest.fixture
def user_login_credentials(test_user_email, test_user_password):
    return {
        "email": test_user_email,
        "password": test_user_password,
    }


@pytest.fixture
def test_user_data(user_login_credentials):
    return {
        **user_login_credentials,
        "username": "TheRaw",
        "first_name": "Gordon",
        "last_name": "Ramsey",
    }


@pytest.fixture
def another_user_data():
    return {
        "email": "remy.is.a.rat@gusteau.fr",
        "username": "Auguste999",
        "first_name": "Auguste",
        "last_name": "Gusteau",
        "password": "jMaecXN4hM84T9fw",
    }


@pytest.fixture
def test_user(django_user_model, test_user_data):
    return django_user_model.objects.create_user(**test_user_data)


@pytest.fixture
def prominent_author(django_user_model, another_user_data, recipe_data):
    author = django_user_model.objects.create_user(**another_user_data)
    author_recipe_data = recipe_data.copy()
    author_recipe_data["image"] = "path_to_image.png"
    tags = author_recipe_data.pop("tags")
    ingredients_data = author_recipe_data.pop("ingredients")
    recipes = [Recipe(**author_recipe_data, author=author) for _ in range(10)]
    for recipe in recipes:
        recipe.save()
        recipe.tags.set(tags)
        ingredients = [
            RecipeIngredientAmount(
                recipe=recipe,
                ingredient=Ingredient.objects.get(pk=ingredient["id"]),
                amount=ingredient["amount"],
            )
            for ingredient in ingredients_data
        ]
        RecipeIngredientAmount.objects.bulk_create(ingredients)
    return author


@pytest.fixture
def users_bulk_create(django_user_model):
    users = [
        django_user_model(
            username=f"user{i}",
            password=f"uLi393QqSuuB4RBm{i}",
            email=f"user{i}@mail.com",
            first_name=f"User{i}",
            last_name=f"User{i}ov",
        )
        for i in range(10)
    ]
    django_user_model.objects.bulk_create(users)


@pytest.fixture
def another_user(django_user_model, users_bulk_create, test_user):
    return django_user_model.objects.exclude(pk=test_user.pk).first()


@pytest.fixture
def authentication_token(test_user):
    token, _ = settings.TOKEN_MODEL.objects.get_or_create(user=test_user)
    return token


@pytest.fixture
def authorized_client(client, authentication_token):
    client.defaults["HTTP_AUTHORIZATION"] = f"Token {authentication_token}"
    return client


@pytest.fixture
def tags_bulk_create(db):
    tags = [
        Tag(
            name=f"tag{i}",
            color=f"AAAA{i:02d}",
            slug=f"slug{i}",
        )
        for i in range(10)
    ]
    Tag.objects.bulk_create(tags)


@pytest.fixture
def ingredients_bulk_create(db):
    ingredients = [
        Ingredient(
            name=f"ingredient{i}",
            measurement_unit=f"unit{i}",
        )
        for i in range(10)
    ]
    Ingredient.objects.bulk_create(ingredients)


@pytest.fixture
def base64_image():
    return (
        "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABiey"
        "waAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACk"
        "lEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg=="
    )


@pytest.fixture
def recipe_data(base64_image, tags_bulk_create, ingredients_bulk_create):
    first_ingredient_id = Ingredient.objects.first().id
    second_ingredient_id = Ingredient.objects.last().id
    first_tag_id = Tag.objects.first().id
    second_tag_id = Tag.objects.last().id
    return {
        "ingredients": [
            {
                "id": first_ingredient_id,
                "amount": 20,
            },
            {
                "id": second_ingredient_id,
                "amount": 10,
            },
        ],
        "tags": [first_tag_id, second_tag_id],
        "image": base64_image,
        "name": "Нечто съедобное (это не точно)",
        "text": "Приготовьте как нибудь эти ингредиеты",
        "cooking_time": 5,
    }


@pytest.fixture
def new_recipe_data(base64_image):
    first_ingredient_id = Ingredient.objects.first().id
    first_tag_id = Tag.objects.first().id
    return {
        "ingredients": [
            {
                "id": first_ingredient_id,
                "amount": 20,
            },
        ],
        "tags": [first_tag_id],
        "image": base64_image,
        "name": "Les poissons",
        "text": (
            """Les poissons, les poissons
            How I love les poissons
            Love to chop and to serve little fish
            First I cut of their heads
            Zen I pull out their bones
            Ah mais oui, ça see'est toujours delish"""
        ),
        "cooking_time": 40,
    }


@pytest.fixture
def user_recipe(test_user, recipe_data):
    recipe_data_copy = recipe_data.copy()
    tags = recipe_data_copy.pop("tags")
    ingredients_data = recipe_data_copy.pop("ingredients")
    recipe_data_copy["image"] = "path_to_image.png"
    recipe = Recipe.objects.create(author=test_user, **recipe_data_copy)
    recipe.tags.set(tags)
    ingredients = [
        RecipeIngredientAmount(
            recipe=recipe,
            ingredient=Ingredient.objects.get(pk=ingredient["id"]),
            amount=ingredient["amount"],
        )
        for ingredient in ingredients_data
    ]
    RecipeIngredientAmount.objects.bulk_create(ingredients)
    return recipe


@pytest.fixture
def user_recipe_id(user_recipe):
    return [user_recipe.id]


@pytest.fixture
def recipes_bulk_create(
    users_bulk_create,
    tags_bulk_create,
    ingredients_bulk_create,
    django_user_model,
    test_user,
):
    tags = Tag.objects.all()
    ingredients = Ingredient.objects.all()
    users = django_user_model.objects.exclude(pk=test_user.pk)
    recipes = [
        Recipe(
            author=users[i % len(users)],
            name=f"recipe{i}",
            text="Some text here",
            cooking_time=10,
            image=f"recipes/{i:02d}17107c-0b8a-4aeb-bee2-1ce0abd868f0.png",
        )
        for i in range(11)
    ]
    Recipe.objects.bulk_create(recipes)
    for i, recipe in enumerate(recipes):
        tag = tags[i % len(tags)]
        recipe.tags.set([tag])

        ingredient = RecipeIngredientAmount(
            recipe=recipe,
            ingredient=ingredients[i % len(ingredients)],
            amount=20,
        )
        ingredient.save()


@pytest.fixture
def non_user_recipe(test_user, recipes_bulk_create):
    return Recipe.objects.exclude(author=test_user).first()


@pytest.fixture
def bad_tag_id_recipe_data(recipe_data):
    bad_tags = [max(Tag.objects.values_list("id", flat=True)) + 1]
    return {**recipe_data, "tags": bad_tags}


@pytest.fixture
def double_tag_recipe_data(recipe_data):
    tag_id = Tag.objects.first().id
    double_tags = [tag_id, tag_id]
    return {**recipe_data, "tags": double_tags}


@pytest.fixture
def bad_ingredient_id_recipe_data(recipe_data):
    bad_ingredients = [
        {
            "id": max(Ingredient.objects.values_list("id", flat=True)) + 1,
            "amount": 20,
        }
    ]
    return {**recipe_data, "ingredients": bad_ingredients}


@pytest.fixture
def low_ingredient_amount_recipe_data(recipe_data):
    low_ingredients = [
        {
            "id": Ingredient.objects.first().id,
            "amount": 0,
        }
    ]
    return {**recipe_data, "ingredients": low_ingredients}


@pytest.fixture
def double_ingrediend_recipe_data(recipe_data):
    ingredient_id = Ingredient.objects.first().id
    double_ingredients = [
        {"id": ingredient_id, "amount": 20},
        {"id": ingredient_id, "amount": 10},
    ]
    return {**recipe_data, "ingredients": double_ingredients}


@pytest.fixture
def too_long_name_recipe_data(recipe_data):
    bad_name = "a" * (DEFAULT_CHAR_FIELD_LENGTH + 1)
    return {**recipe_data, "name": bad_name}


@pytest.fixture
def user_subscription(test_user, prominent_author):
    return Subscription.objects.create(user=test_user, author=prominent_author)


@pytest.fixture
def user_subscriptions_in_bulk(
    test_user, django_user_model, users_bulk_create
):
    users = django_user_model.objects.exclude(pk=test_user.pk)
    subscriptions = [
        Subscription(user=test_user, author=user) for user in users
    ]
    Subscription.objects.bulk_create(subscriptions)


@pytest.fixture
def shopping_cart_in_bulk(test_user, recipes_bulk_create):
    shopping_cart_items = [
        ShoppingCart(user=test_user, recipe=recipe)
        for recipe in Recipe.objects.all()
    ]
    ShoppingCart.objects.bulk_create(shopping_cart_items)


@pytest.fixture
def shopping_cart(test_user, user_recipe):
    return ShoppingCart.objects.create(user=test_user, recipe=user_recipe)


@pytest.fixture
def test_favorites(test_user, user_recipe):
    return Favorite.objects.create(user=test_user, recipe=user_recipe)
