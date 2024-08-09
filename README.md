# Foodrgam
Продуктовый помощник - дипломный проект курса Backend-разработки Яндекс.Практикум. Проект представляет собой онлайн-сервис и API для него. На этом сервисе пользователи могут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Favorite», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.
Проект реализован на Django и DjangoRestFramework. Доступ к данным реализован через API-интерфейс. Документация к API написана с использованием Redoc.

### Особенности

Проект завернут в Docker-контейнеры;
Образы foodgram_frontend и foodgram_backend запушены на DockerHub;
Реализован workflow c автодеплоем на удаленный сервер и отправкой сообщения в Telegram;

Адрес: https://foodgram-new.ddns.net/

### Инфраструктура проекта

- Главная - https://foodgram-new.ddns.net/recipes/
- API - https://foodgram-new.ddns.net/api/
- Админка -https://foodgram-new.ddns.net/admin/

### Развертывание на сервере

1. Скопируйте из репозитория файл docker-compose.production.yml

2. В дирректорию с сохраненным docker-compose.production.yml создайте файл .env со следующим содержимым:

    - SECRET_KEY=... # секретный ключ для backend'а на Django
    - DEBUG=... # Параметр включения/отключения режима отладки для backend'а на Django
    - ALLOWED_HOSTS=... # IP/домен хоста, БД (указывается через запятую без пробелов)
    - DB_ENGINE=django.db.backends.postgresql # работаем с БД postgresql
    - DB_NAME=db.postgres # имя БД
    - POSTGRES_USER=... # имя пользователя БД
    - POSTGRES_PASSWORD=... # пароль от БД
    - DB_HOST=db
    - DB_PORT=5432

3. В этой же дирректории в терминале (bash) выполните команду:

```bash
# в случае Windows не нужно использовать sudo
sudo docker compose -f docker-compose.production.yml up -d
```

4. Для создания суперпользователя, выполните команду:
```bash
sudo docker compose -f docker-compose.production.yml exec backend python manage.py createsuperuser
```


**Автор:** Донской Александр (donskoyaleksander@gmail.com)