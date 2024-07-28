from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import User


class CustomUserAdmin(UserAdmin):
    search_fields = ['username', 'email']


CustomUserAdmin.fieldsets += (
    ('Extra Fields', {'fields': ('avatar', 'role')}),
)

admin.site.register(User, CustomUserAdmin)
