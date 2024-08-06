import io
import csv
from django.db.models import Sum

from recipes.models import ShoppingList, IngredientAmount


def get_shopping_list(user):
    ingredient_counts = {}
    shopping_card = io.StringIO()
    writer = csv.writer(shopping_card)
    writer.writerow(['Ингредиент', 'Количество'])
    ingredients_and_totals = IngredientAmount.objects.filter(
        ingredient__in=ShoppingList.objects.filter(user=user).values_list(
            'recipes__ingredients__id', flat=True
        )
    ).values('ingredient__name').annotate(total_amount=Sum('amount'))
    for item in ingredients_and_totals:
        ingredient_counts[item['ingredient__name']] = item['total_amount']
    for key, value in ingredient_counts.items():
        writer.writerow([key, value])
    shopping_card.seek(0)
    return shopping_card


def get_ingredients_data(data, instance):
    data = [
        {
            'ingredient': data['ingredient'],
            'amount': data['amount']
        } for data in data
    ]

    return IngredientAmount.objects.bulk_create(
        [
            IngredientAmount(
                recipe=instance, **ingredient_data
            ) for ingredient_data in data
        ],
    )
