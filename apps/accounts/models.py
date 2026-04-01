from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.accounts.managers import UserManager
from apps.common.models import BaseModel


class User(BaseModel, AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email