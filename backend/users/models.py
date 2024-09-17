from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import F, Q

from foodgram_backend.constants import (
    USER_EMAIL_MAX_LENGTH,
    USER_FIRST_NAME_MAX_LENGTH,
    USER_LAST_NAME_MAX_LENGTH,
)


class FoodgramUser(AbstractUser):
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = [
        "username",
        "first_name",
        "last_name",
    ]
    first_name = models.CharField(
        verbose_name="first name",
        max_length=USER_FIRST_NAME_MAX_LENGTH,
    )
    last_name = models.CharField(
        verbose_name="last name",
        max_length=USER_LAST_NAME_MAX_LENGTH,
    )
    email = models.EmailField(
        verbose_name="email",
        max_length=USER_EMAIL_MAX_LENGTH,
        unique=True,
    )

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"
        ordering = ["username"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"


class Subscription(models.Model):
    user = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name="subscriber",
    )
    author = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name="subscribers",
        verbose_name="author",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "author"],
                name="unique_user_author",
            ),
            models.CheckConstraint(
                check=~Q(user=F("author")),
                name="cannot_subscribe_to_self",
            ),
        ]
