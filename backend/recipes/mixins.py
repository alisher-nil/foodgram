from django.db import models
from django.utils import timezone


class CreatedAtMixin(models.Model):
    created_at = models.DateTimeField(
        "date of creation",
        default=timezone.now,
    )

    class Meta:
        abstract = True
