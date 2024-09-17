from django.contrib import admin

from recipes.models import Favorite, Recipe, ShoppingCart
from users.models import FoodgramUser, Subscription


class RecipeInline(admin.TabularInline):
    model = Recipe
    extra = 0


class FavoriteInline(admin.TabularInline):
    model = Favorite
    extra = 0


class ShoppingCartInline(admin.TabularInline):
    model = ShoppingCart
    extra = 0


@admin.register(FoodgramUser)
class FoodgramUserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
    )
    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
    )
    list_filter = ("is_staff",)
    list_display_links = ("name",)
    inlines = [RecipeInline, FavoriteInline, ShoppingCartInline]

    def name(self, obj):
        return f"{obj.first_name} {obj.last_name} ({obj.username})".strip()


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "author")
