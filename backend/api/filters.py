import django_filters

from recipes.models import Ingredient, Recipe


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.Filter(method="filter_name")

    class Meta:
        model = Ingredient
        fields = ["name"]

    def filter_name(self, queryset, name, value):
        return queryset.filter(name__startswith=value) | queryset.filter(
            name__icontains=value
        )


class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.AllValuesMultipleFilter(field_name="tags__slug")
    is_in_shopping_cart = django_filters.NumberFilter(
        method="filter_is_in_shopping_cart"
    )
    is_favorited = django_filters.NumberFilter(method="filter_is_favorited")

    class Meta:
        model = Recipe
        fields = ["tags", "author", "is_in_shopping_cart", "is_favorited"]

    def filter_is_favorited(self, queryset, name, value):
        if value:
            return queryset.filter(is_favorited=True)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(is_in_shopping_cart=True)
        return queryset
