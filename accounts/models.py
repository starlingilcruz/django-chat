"""
User model for authentication
"""

from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxLengthValidator, MinLengthValidator
from django.db import models


class User(AbstractUser):
    """
    Custom user model with first_name and last_name validation
    """

    first_name = models.CharField(
        max_length=50,
        validators=[MinLengthValidator(1), MaxLengthValidator(50)],
        blank=False,
    )
    last_name = models.CharField(
        max_length=50,
        validators=[MinLengthValidator(1), MaxLengthValidator(50)],
        blank=False,
    )
    email = models.EmailField(unique=True, blank=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.email} ({self.get_full_name()})"
