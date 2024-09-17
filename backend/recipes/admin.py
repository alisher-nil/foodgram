from django.contrib import admin

from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag


class RecipeInline(admin.TabularInline):
    model = Recipe
    extra = 0


class FavoriteInline(admin.TabularInline):
    model = Favorite
    extra = 0


class ShoppingCartInline(admin.TabularInline):
    model = ShoppingCart
    extra = 0


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "color", "slug", "id")
    search_fields = ("name",)
    list_filter = ("name",)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "measurement_unit", "id")
    search_fields = ("name",)
    list_filter = ("name",)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("name", "author", "created_at", "id")
    search_fields = ("name", "author__username")
    list_filter = ("created_at",)
    inlines = [FavoriteInline, ShoppingCartInline]


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")
    search_fields = ("user__username", "recipe__name")
    list_filter = ("created_at",)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")
    search_fields = ("user__username", "recipe__name")
    list_filter = ("created_at",)
