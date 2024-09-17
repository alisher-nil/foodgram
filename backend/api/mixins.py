from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
)

from recipes.models import Recipe


class UserCollectionsMixin:
    permission_classes = [IsAuthenticated]

    def get_collection_filter(self, request, *args, **kwargs):
        return {
            "user": request.user,
            "recipe": get_object_or_404(Recipe, pk=kwargs.get("recipe_id")),
        }

    def get_request_data(self, request, *args, **kwargs):
        return {
            "recipe": kwargs.get("recipe_id"),
        }

    def get_serializer_context(self):
        return {
            "request": self.request,
            "format": self.format_kwarg,
            "view": self,
        }

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=self.get_request_data(request, *args, **kwargs),
            context=self.get_serializer_context(),
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data, status=HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        collection_filter = self.get_collection_filter(
            request, *args, **kwargs
        )
        try:
            instance = self.model.objects.get(**collection_filter)
        except self.model.DoesNotExist as e:
            return Response(
                {"details": str(e)},
                status=HTTP_400_BAD_REQUEST,
            )
        instance.delete()
        return Response(status=HTTP_204_NO_CONTENT)
