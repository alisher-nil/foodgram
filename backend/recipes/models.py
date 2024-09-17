from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from foodgram_backend.constants import (
    DEFAULT_CHAR_FIELD_LENGTH,
    HEX_COLOR_LENGTH,
    MIN_INGREDIENT_AMOUNT,
)
from recipes.mixins import CreatedAtMixin

User = get_user_model()

media_root = settings.MEDIA_ROOT


class Tag(models.Model):
    name = models.CharField(
        max_length=DEFAULT_CHAR_FIELD_LENGTH,
        unique=True,
        verbose_name="tag name",
    )
    color = models.CharField(
        max_length=HEX_COLOR_LENGTH,
        verbose_name="color in HEX",
    )
    slug = models.CharField(
        max_length=DEFAULT_CHAR_FIELD_LENGTH,
        unique=True,
        verbose_name="slug",
    )

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} - {self.slug}"


class Ingredient(models.Model):
    name = models.CharField(
        max_length=DEFAULT_CHAR_FIELD_LENGTH,
        verbose_name="name",
    )
    measurement_unit = models.CharField(
        max_length=DEFAULT_CHAR_FIELD_LENGTH, verbose_name="measurement unit"
    )

    class Meta:
        verbose_name = "Ingredient"
        verbose_name_plural = "Ingredients"
        ordering = ["name", "measurement_unit"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"],
                name="unique_name_and_unit",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"


class Recipe(CreatedAtMixin, models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="author",
    )
    name = models.CharField(
        max_length=DEFAULT_CHAR_FIELD_LENGTH,
        verbose_name="recipe name",
    )
    text = models.TextField(verbose_name="description")
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="time in minutes",
        validators=[MinValueValidator(MIN_INGREDIENT_AMOUNT)],
    )
    image = models.ImageField(
        upload_to="recipes/",
        verbose_name="image",
    )
    tags = models.ManyToManyField(
        Tag,
        related_name="recipes",
        verbose_name="tags",
    )

    class Meta:
        verbose_name = "Recipe"
        verbose_name_plural = "Recipes"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class RecipeIngredientAmount(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="ingredients",
        verbose_name="recipe",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="ingredient",
    )
    amount = models.PositiveSmallIntegerField(verbose_name="amount")

    class Meta:
        verbose_name = "Recipe ingredient"
        verbose_name_plural = "Recipe ingredients"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="unique_recipe_ingredient",
            )
        ]
        ordering = ["id"]

    def __str__(self):
        return f"{self.recipe} - {self.ingredient}"


class UserCollection(CreatedAtMixin, models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="user",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="recipe",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="%(class)s unique item",
            )
        ]
        ordering = ["-created_at"]
        default_related_name = "%(class)s"
        abstract = True

    def __str__(self):
        return f"{self.user} - {self.recipe}"


class ShoppingCart(UserCollection):
    class Meta:
        verbose_name = "Shopping carts"
        verbose_name_plural = "Shopping cart items"
        default_related_name = "shopping_cart"


class Favorite(UserCollection):
    class Meta:
        verbose_name = "Favorites"
        verbose_name_plural = "Favorite items"
        default_related_name = "favorites"
