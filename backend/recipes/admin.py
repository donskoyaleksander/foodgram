from django.contrib import admin

from recipes.models import (
    Recipe,
    Ingredient,
    Tag,
    IngredientAmount,
    Subscription,
    ShoppingList,
    Favorite
)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = [
        'author',
        'name',
        'text',
        'cooking_time',
        'image',
        'short_link',
    ]
    search_fields = ['name', 'author__username']
    list_filter = ['tags']


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['name', 'measurement_unit']
    search_fields = ['name']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']


@admin.register(IngredientAmount)
class IngredientAmountAdmin(admin.ModelAdmin):
    list_display = ['recipe', 'ingredient', 'amount']
    search_fields = ['recipe__name', 'ingredient__name']
    list_filter = ['recipe']


@admin.register(Subscription)
class SubscriptiontAdmin(admin.ModelAdmin):
    list_display = ['user', 'subscriber']


@admin.register(ShoppingList)
class ShoppingListAdmin(admin.ModelAdmin):
    list_display = ['user', 'recipes']


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'recipes']
