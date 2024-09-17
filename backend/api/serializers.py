from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db.models import BooleanField, Count, Value
from django.db.transaction import atomic
from drf_extra_fields.fields import Base64ImageField
from rest_framework import exceptions, serializers, validators

from api.utils import extract_and_assign_tags_ingredients
from api.validators import NotEmptyValueValidator
from foodgram_backend.constants import MIN_INGREDIENT_AMOUNT
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredientAmount,
    ShoppingCart,
    Tag,
)
from users.models import Subscription

User = get_user_model()


class RecipeListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        recipes_limit = self.get_recipes_limit_from_context()
        if recipes_limit:
            data = data.all()[:recipes_limit]
        return super().to_representation(data)

    def get_recipes_limit_from_context(self):
        query_params = getattr(
            self.context.get("request", None), "query_params", {}
        )
        recipes_limit = query_params.get("recipes_limit", None)
        if recipes_limit and self.validate_recipe_limit(recipes_limit):
            return int(recipes_limit)

    def validate_recipe_limit(self, value):
        try:
            int(value)
            return value
        except ValueError:
            raise serializers.ValidationError(
                "Recipes limit should be an integer"
            )


class RecipeBasicSerializer(serializers.ModelSerializer):
    class Meta:
        list_serializer_class = RecipeListSerializer
        model = Recipe
        fields = (
            "id",
            "name",
            "cooking_time",
            "image",
        )


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "color", "slug")


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class UserBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
        )


class SignupSerializer(UserBaseSerializer):
    password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
    )

    class Meta:
        model = User
        fields = UserBaseSerializer.Meta.fields + ("password",)

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(UserBaseSerializer):
    is_subscribed = serializers.BooleanField(default=False)

    class Meta:
        model = User
        fields = UserBaseSerializer.Meta.fields + ("is_subscribed",)


class UserDetailSerializer(UserSerializer):
    recipes_count = serializers.IntegerField(required=False)
    recipes = RecipeBasicSerializer(many=True, required=False)

    class Meta:
        model = User
        fields = UserSerializer.Meta.fields + (
            "recipes_count",
            "recipes",
        )


class RecipeIngredientsSerializer(serializers.ModelSerializer):
    """
    Serializer for representaion of recipe ingredients as a nested field
    in RecipeSerializer and RecipeWriteSerializer.

    id and amount are required fields. They are used to create or
    update ManyToMany relations between Recipe and Ingredients.

    name and measurement_unit are for read-only purposes.
    """

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source="ingredient",
    )
    amount = serializers.IntegerField(min_value=MIN_INGREDIENT_AMOUNT)
    name = serializers.CharField(source="ingredient.name", read_only=True)
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit", read_only=True
    )

    class Meta:
        model = RecipeIngredientAmount
        fields = (
            "id",
            "name",
            "measurement_unit",
            "amount",
        )


class RecipeBaseSerializer(serializers.ModelSerializer):
    author = UserSerializer()
    ingredients = RecipeIngredientsSerializer(many=True)
    tags = TagSerializer(many=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "name",
            "text",
            "cooking_time",
            "image",
            "tags",
            "ingredients",
        )


class RecipeSerializer(RecipeBaseSerializer):
    is_favorited = serializers.BooleanField(read_only=True, default=False)
    is_in_shopping_cart = serializers.BooleanField(
        read_only=True, default=False
    )

    class Meta:
        model = Recipe
        fields = RecipeBaseSerializer.Meta.fields + (
            "is_favorited",
            "is_in_shopping_cart",
        )


class RecipeWriteSerializer(RecipeBaseSerializer):
    author = UserSerializer(default=serializers.CurrentUserDefault())
    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )

    class Meta:
        model = Recipe
        fields = RecipeBaseSerializer.Meta.fields
        validators = [
            NotEmptyValueValidator(fields=["image", "tags", "ingredients"])
        ]

    def _verify_unique_values(self, data: list):
        """Verifies that all entries in a list are unique."""
        if len(set(data)) != len(data):
            raise serializers.ValidationError("Values are not unique")

    def validate_tags(self, tags):
        """Validates that all tags are unique.

        Empty values are allowed, because they are checked by
        NotEmptyValueValidator.
        """
        self._verify_unique_values(tags)
        return tags

    def validate_ingredients(self, ingredients):
        """Validates that all ingredients are unique.

        Empty values are allowed, because they are checked by
        NotEmptyValueValidator.
        """
        selected_ingredients = [
            ingredient["ingredient"] for ingredient in ingredients
        ]
        self._verify_unique_values(selected_ingredients)
        return ingredients

    @atomic
    @extract_and_assign_tags_ingredients
    def create(self, validated_data):
        return Recipe.objects.create(**validated_data)

    @atomic
    @extract_and_assign_tags_ingredients
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeSerializer(instance).data


class UserCollectionsSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        fields = ("user", "recipe")

    def to_representation(self, instance):
        return RecipeBasicSerializer(instance.recipe).data


class ShoppingCartSerializer(UserCollectionsSerializer):
    class Meta:
        model = ShoppingCart
        fields = UserCollectionsSerializer.Meta.fields
        validators = [
            validators.UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=("user", "recipe"),
                message="Can not add the same recipe twice.",
            )
        ]


class FavoriteSerializer(UserCollectionsSerializer):
    class Meta:
        model = Favorite
        fields = UserCollectionsSerializer.Meta.fields
        validators = [
            validators.UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=("user", "recipe"),
                message="Can not add the same recipe twice.",
            )
        ]


class AuthorPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        return (
            User.objects.all()
            .annotate(recipes_count=Count("recipes"))
            .annotate(is_subscribed=Value(True, output_field=BooleanField()))
            .prefetch_related("recipes")
        )


class SubscribeSerializer(UserCollectionsSerializer):
    author = AuthorPrimaryKeyRelatedField()

    class Meta:
        model = Subscription
        fields = ["user", "author"]
        validators = [
            validators.UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=("user", "author"),
                message="You already subscribed to this author.",
            )
        ]

    def validate_author(self, data):
        if data == self.context["request"].user:
            raise exceptions.ValidationError(
                "Users cannot subscribe to themselves"
            )
        return data

    def to_representation(self, instance):
        return UserDetailSerializer(
            instance.author,
            context=self.context,
        ).data
