from django.contrib.auth import get_user_model
from django.db.models import (
    BooleanField,
    Count,
    Exists,
    F,
    OuterRef,
    Prefetch,
    Sum,
    Value,
)
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import SetPasswordSerializer
from rest_framework import (
    decorators,
    generics,
    mixins,
    permissions,
    response,
    status,
    views,
    viewsets,
)

from api.filters import IngredientFilter, RecipeFilter
from api.mixins import UserCollectionsMixin
from api.permissions import IsAuthorAdminOrReadOnly
from api.serializers import (
    FavoriteSerializer,
    IngredientSerializer,
    RecipeSerializer,
    RecipeWriteSerializer,
    ShoppingCartSerializer,
    SignupSerializer,
    SubscribeSerializer,
    TagSerializer,
    UserDetailSerializer,
    UserSerializer,
)
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from users.models import Subscription

User = get_user_model()


class FoodgramUserViewSet(
    mixins.CreateModelMixin,
    viewsets.ReadOnlyModelViewSet,
):
    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return UserSerializer
        elif self.action == "set_password":
            return SetPasswordSerializer
        return SignupSerializer

    def get_queryset(self):
        queryset = User.objects.all()
        if self.request.user.is_authenticated:
            subscriptions = self.request.user.subscriptions
            queryset = queryset.annotate(
                is_subscribed=Exists(
                    subscriptions.filter(author=OuterRef("pk"))
                )
            )
        return queryset

    def get_permissions(self):
        if self.action in ("me", "set_password"):
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_instance(self):
        return self.request.user

    @decorators.action(detail=False)
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)

    @decorators.action(["post"], detail=False)
    def set_password(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.request.user.set_password(serializer.data["new_password"])
        self.request.user.save()
        return response.Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionListViewSet(generics.ListAPIView):
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        subscriptions = self.request.user.subscriptions
        return (
            User.objects.filter(subscribers__user=self.request.user)
            .annotate(recipes_count=Count("recipes"))
            .annotate(
                is_subscribed=Exists(
                    subscriptions.filter(author=OuterRef("pk"))
                )
            )
            .prefetch_related("recipes")
            .order_by("username")
        )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthorAdminOrReadOnly]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return RecipeSerializer
        return RecipeWriteSerializer

    def get_queryset(self):
        if self.action == "destroy":
            return Recipe.objects.all()
        if self.request.user.is_anonymous:
            is_favorited = Value(False, output_field=BooleanField())
            is_in_shopping_cart = Value(False, output_field=BooleanField())
            is_subscribed = Value(False, output_field=BooleanField())
        else:
            is_favorited = Exists(
                self.request.user.favorites.filter(recipe=OuterRef("pk"))
            )
            is_in_shopping_cart = Exists(
                self.request.user.shopping_cart.filter(recipe=OuterRef("pk"))
            )
            is_subscribed = Exists(
                self.request.user.subscriptions.filter(author=OuterRef("pk"))
            )
        return Recipe.objects.prefetch_related(
            "tags",
            "ingredients__ingredient",
            Prefetch(
                "author",
                queryset=User.objects.annotate(is_subscribed=is_subscribed),
            ),
        ).annotate(
            is_favorited=is_favorited,
            is_in_shopping_cart=is_in_shopping_cart,
        )


class DownloadShoppingCartAPIView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    item_template = "{name} ({unit}) - {amount}"

    def get(self, request, *args, **kwargs):
        Favorite.objects.all().values()
        shopping_list = request.user.shopping_cart.values(
            "recipe__ingredients__ingredient"
        ).annotate(
            name=F("recipe__ingredients__ingredient__name"),
            unit=F("recipe__ingredients__ingredient__measurement_unit"),
            amount=Sum("recipe__ingredients__amount"),
        )
        shopping_list_text = "\n".join(
            [self.item_template.format(**item) for item in shopping_list]
        )
        response = FileResponse(
            shopping_list_text,
            content_type="text/plain",
            headers={
                "Content-Disposition": "attachment; filename=shopping_list.txt"
            },
        )
        return response


class FavoritesAPIView(UserCollectionsMixin, views.APIView):
    model = Favorite
    serializer_class = FavoriteSerializer


class ShoppingCartAPIView(UserCollectionsMixin, views.APIView):
    model = ShoppingCart
    serializer_class = ShoppingCartSerializer


class SubscribeAPIView(UserCollectionsMixin, views.APIView):
    model = Subscription
    serializer_class = SubscribeSerializer
    author = None
    recipes_limit = None

    def initial(self, request, *args, **kwargs):
        self.author = get_object_or_404(User, pk=kwargs.get("author_id"))
        return super().initial(request, *args, **kwargs)

    def get_request_data(self, request, *args, **kwargs):
        return {
            "author": self.author.pk,
        }

    def get_collection_filter(self, request, *args, **kwargs):
        return {
            "user": request.user,
            "author": self.author,
        }
