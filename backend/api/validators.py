from django.core.exceptions import ValidationError


def username_not_me_validator(value):
    if value == 'me':
        raise ValidationError(
            f'Username "{value}" is not valid'
        )


def cooking_time_validator(value):
    try:
        if int(value) < 1:
            raise ValidationError(
                'Cooking time should be not less than 1 min'
            )
    except ValueError:
        raise ValidationError(
            'Value must be an integer'
        )


def ingredient_amount_validator(value):
    try:
        if int(value) <= 0:
            raise ValidationError(
                'Number of ingridients should be above zero'
            )
    except ValueError:
        raise ValidationError(
            'Value must be an integer'
        )