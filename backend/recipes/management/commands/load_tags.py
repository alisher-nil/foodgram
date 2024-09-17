import json

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandParser

from recipes.models import Tag


class Command(BaseCommand):
    help = "Load ingredients from tags.json"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "tags_file",
            type=str,
            help="Path to tags.json",
        )

    def handle(self, *args, **options):
        try:
            with open(options["tags_file"], "r") as file:
                ingredients = json.load(file)
                db_tags = self.get_valid_tags(ingredients)
                Tag.objects.bulk_create(db_tags)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to load tags. Error: {e}")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Successfully loaded {len(db_tags)} tags")
            )

    def get_valid_tags(self, tags):
        db_tags = []
        for tag in tags:
            db_tag = Tag(**tag)
            if self.validate_tags(db_tag):
                db_tags.append(db_tag)
        return db_tags

    def validate_tags(self, tag):
        try:
            tag.validate_constraints()
            tag.validate_unique()
        except ValidationError:
            pass
        else:
            return tag
