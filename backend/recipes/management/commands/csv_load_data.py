import csv

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.apps import apps
from django.db import transaction, models


def load_data_from_csv(model_name, csv_file_path):
    if model_name == 'User':
        model_class = get_user_model()
    else:
        model_class = apps.get_model(
            app_label='recipes', model_name=model_name
        )
    if model_class is None:
        raise CommandError('Модель не найдена в модуле.')

    with transaction.atomic():
        with open(csv_file_path, 'r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                obj = model_class(**row)
                for field_name, value in row.items():
                    if hasattr(obj, field_name) and isinstance(
                        getattr(obj, field_name), models.ForeignKey
                    ):
                        related_model = apps.get_model(
                            app_label='reviews',
                            model_name=obj._meta.get_field(
                                field_name
                            ).related_model
                        )
                        related_object = related_model.objects.get(pk=value)
                        setattr(obj, field_name, related_object)
                obj.full_clean()
                obj.save()


class Command(BaseCommand):
    help = 'Загружает данные из CSV-файла в базу данных.'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Путь CSV-файлу')
        parser.add_argument('model_name', type=str, help='Имя модели')

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        model_name = options['model_name']
        self.stdout.write(
            self.style.NOTICE(f'Загрузка данных из файла {csv_file}')
        )
        try:
            load_data_from_csv(model_name, csv_file)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'При загрузке произошла ошибка:\n{e}\nИзменения отменены.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Данные успешно загружены')
            )
