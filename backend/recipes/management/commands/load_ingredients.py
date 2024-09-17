import json

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandParser

from recipes.models import Ingredient


class Command(BaseCommand):
    help = "Load ingredients from ingredients.json"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "ingredients_file",
            type=str,
            help="Path to ingredients.json",
        )

    def handle(self, *args, **options):
        try:
            with open(options["ingredients_file"], "r") as file:
                ingredients = json.load(file)
                db_ingredients = self.get_valid_ingrediends(ingredients)
                Ingredient.objects.bulk_create(db_ingredients)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to load ingredients. Error: {e}")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully loaded {len(db_ingredients)} ingredients"
                )
            )

    def get_valid_ingrediends(self, ingredients):
        db_ingredients = []
        for ingredient in ingredients:
            db_ingredient = Ingredient(**ingredient)
            if self.validate_ingredient(db_ingredient):
                db_ingredients.append(db_ingredient)
        return db_ingredients

    def validate_ingredient(self, ingredient):
        try:
            ingredient.validate_constraints()
            ingredient.validate_unique()
        except ValidationError:
            pass
        else:
            return ingredient
