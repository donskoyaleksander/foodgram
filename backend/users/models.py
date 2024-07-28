from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import hashers
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils.translation import gettext_lazy

from api.validators import username_not_me_validator
from api.constants import (MAX_LENGTH_NAME,
                           MAX_LENGTH_EMAIL,
                           MAX_LENGTH_ROLE)


class User(AbstractUser):

    class Roles(models.TextChoices):
        ADMIN = 'admin', gettext_lazy('Admin')
        USER = 'user', gettext_lazy('User')

    username = models.CharField(
        'Username',
        max_length=MAX_LENGTH_NAME,
        unique=True,
        validators=[
            UnicodeUsernameValidator(),
            username_not_me_validator
        ],
    )
    email = models.EmailField(
        'Email',
        unique=True,
        max_length=MAX_LENGTH_EMAIL
    )
    first_name = models.CharField(
        'First name',
        max_length=MAX_LENGTH_NAME
    )
    last_name = models.CharField(
        'Last name',
        max_length=MAX_LENGTH_NAME
    )
    avatar = models.ImageField(
        upload_to='users/',
        null=True,
        blank=True
    )
    role = models.CharField(
        'Role',
        max_length=MAX_LENGTH_ROLE,
        choices=Roles.choices,
        default=Roles.USER,
    )

    def update_password(self, old_password, new_password):
        if not self.check_password(old_password):
            raise ValueError("Your current password is not valid")
        self.set_password(new_password)
        self.save()

    def check_password(self, raw_password):
        return hashers.check_password(raw_password, self.password)

    def set_password(self, raw_password):
        self.password = hashers.make_password(raw_password)

    @property
    def is_admin(self):
        return self.role == self.Roles.ADMIN or self.is_superuser

    def __str__(self):
        return self.username
