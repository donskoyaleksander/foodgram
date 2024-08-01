import io
import csv

from recipes.models import ShoppingList


def get_shopping_list(user):
    shopping_list = ShoppingList.objects.filter(user=user)
    ingredient_counts = {}
    response = io.StringIO()
    writer = csv.writer(response)
    writer.writerow(['Ingredient', 'Amount'])
    for recipe in shopping_list:
        ingredients = recipe.recipes.ingredients.all()
        for ingredient in ingredients:
            ingredient_amount = ingredient.ingredientamount_set.first()
            if ingredient_amount.ingredient.name in ingredient_counts:
                ingredient_counts[
                    ingredient_amount.ingredient.name
                ] += ingredient_amount.amount
            else:
                ingredient_counts[
                    ingredient_amount.ingredient.name
                ] = ingredient_amount.amount
    for key, value in ingredient_counts.items():
        writer.writerow([key, value])
    response.seek(0)
    return response
