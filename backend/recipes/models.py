from django.db import models
from django.utils.text import slugify
from django.contrib.auth import get_user_model

from api.validators import cooking_time_validator, ingredient_amount_validator
from api.constants import (MAX_LENGTH_TAG,
                           MAX_LENGTH_SLUG,
                           MAX_LENGTH_INGREDIENT,
                           MAX_LENGTH_MEASURMENT,
                           MAX_LENGTH_RECIPE,
                           MAX_LENGTH_RECIPE_SHORT)


User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        'Tag', unique=True,
        max_length=MAX_LENGTH_TAG
    )
    slug = models.SlugField(
        'Slug', unique=True,
        max_length=MAX_LENGTH_SLUG
    )

    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        'Ingredient', unique=True,
        max_length=MAX_LENGTH_INGREDIENT
    )
    measurement_unit = models.CharField(
        'Measurement unit',
        max_length=MAX_LENGTH_MEASURMENT
    )

    class Meta:
        verbose_name = 'Ingredient'
        verbose_name_plural = 'Ingredients'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='recipe', verbose_name='Author'
    )
    name = models.CharField(
        'Recipe', unique=True,
        max_length=MAX_LENGTH_RECIPE
    )
    text = models.TextField('Description')
    cooking_time = models.IntegerField(
        'Cooking time',
        validators=[
            cooking_time_validator,
        ],
    )
    image = models.ImageField()
    ingredients = models.ManyToManyField(
        Ingredient, through='IngredientAmount',
        related_name='recipes'
    )
    tags = models.ManyToManyField(Tag)
    short_link = models.SlugField(
        unique=True, blank=True,
    )
    pub_date = models.DateTimeField('Publication date', auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.short_link:
            self.short_link = slugify(
                self.name, allow_unicode=True
            )[:MAX_LENGTH_RECIPE_SHORT]
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Recipe'
        verbose_name_plural = 'Recipes'
        ordering = ('pub_date',)

    def __str__(self):
        return self.name


class IngredientAmount(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        verbose_name='Recipe'
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE,
        verbose_name='Ingredient'
    )
    amount = models.PositiveIntegerField(
        'Amount', unique=True,
        validators=[
            ingredient_amount_validator
        ]
    )

    class Meta:
        verbose_name = 'Ingredient amount'
        verbose_name_plural = 'Ingredients amount'
        ordering = ('recipe',)

    def __str__(self):
        return self.name


class Subscription(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='respondent', verbose_name='Respondent'
    )
    subscriber = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='subscribers', verbose_name='Subscriber'
    )

    class Meta:
        verbose_name = 'Subscriber'
        verbose_name_plural = 'Subscribers'
        ordering = ('user',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'subscriber'],
                name="unique_subscribers"
            ),
            models.CheckConstraint(
                name='prevent_self_subscribe',
                check=~models.Q(user=models.F('subscriber')),
            ),
        ]


class ShoppingList(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='shoppinglist_users', verbose_name='User'
    )
    recipes = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name='shoppinglist_recipes', verbose_name='Recipe'
    )

    class Meta:
        verbose_name = 'Shopping list'
        verbose_name_plural = 'Shopping lists'


class Favorite(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='favotite_users', verbose_name='User'
    )
    recipes = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name='favorite_recipes', verbose_name='Recipe'
    )

    class Meta:
        verbose_name = 'Favorite'
        verbose_name_plural = 'Favorites'
