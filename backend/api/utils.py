from recipes.models import RecipeIngredientAmount


def extract_and_assign_tags_ingredients(func):
    """
    Decorator that extracts tags and ingredients from a validated data
    and assignes them to an instance after it had been created or updated.
    """

    def wrapper(*args, **kwargs):
        *_, validated_data = args
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")

        instance = func(*args, **kwargs)

        instance.tags.set(tags)
        # all() is required because `instance.ingredients` returns
        # a related manager, that does not have delete() method
        instance.ingredients.all().delete()
        new_ingredients = [
            RecipeIngredientAmount(recipe=instance, **ingredient)
            for ingredient in ingredients
        ]
        RecipeIngredientAmount.objects.bulk_create(new_ingredients)
        return instance

    return wrapper
