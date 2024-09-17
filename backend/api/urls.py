from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from api.views import (
    DownloadShoppingCartAPIView,
    FavoritesAPIView,
    FoodgramUserViewSet,
    IngredientsViewSet,
    RecipeViewSet,
    ShoppingCartAPIView,
    SubscribeAPIView,
    SubscriptionListViewSet,
    TagViewSet,
)

app_name = "api"

auth_urlpatterns = [
    path("", include("djoser.urls.authtoken")),
]

router_v1 = DefaultRouter()
router_v1.register("tags", TagViewSet, basename="tags")
router_v1.register("ingredients", IngredientsViewSet, basename="ingredients")

users_router_v1 = DefaultRouter()
users_router_v1.register("", FoodgramUserViewSet, basename="users")
users_urlpatterns = [
    re_path(
        r"(?P<author_id>\d+)/subscribe/",
        SubscribeAPIView.as_view(),
        name="subscribe",
    ),
    path(
        "subscriptions/",
        SubscriptionListViewSet.as_view(),
        name="subscriptions",
    ),
    path("", include(users_router_v1.urls)),
]

recipes_router_v1 = DefaultRouter()
recipes_router_v1.register("", RecipeViewSet, basename="recipes")
recipes_urlpatterns = [
    re_path(
        r"(?P<recipe_id>\d+)/shopping_cart/",
        ShoppingCartAPIView.as_view(),
        name="shopping_cart",
    ),
    re_path(
        r"(?P<recipe_id>\d+)/favorite/",
        FavoritesAPIView.as_view(),
        name="favorites",
    ),
    path(
        "download_shopping_cart/",
        DownloadShoppingCartAPIView.as_view(),
        name="download_shopping_cart",
    ),
    path("", include(recipes_router_v1.urls)),
]


urlpatterns = [
    path("", include(router_v1.urls)),
    path("recipes/", include(recipes_urlpatterns)),
    path("users/", include(users_urlpatterns)),
    path("auth/", include(auth_urlpatterns)),
]
