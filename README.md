# Mafia companion API

<!-- region nice badges -->
[![wakatime](https://wakatime.com/badge/github/evgfilim1/mafia-companion-api.svg)](https://wakatime.com/badge/github/evgfilim1/mafia-companion-api)
<!-- endregion -->

API для приложения [Mafia companion][app].

Позволяет более гибко сохранять список игроков, турниров и партий в игре "Мафия".

## Установка

### Локально

1. Установите, настройте и запустите PostgreSQL и Redis;
2. Установите Python 3.12;
3. `pip install -r requirements.txt -r dev-requirements.txt uvicorn`;
4. `cp .env.dist .env`;
5. `vim .env`;
6. `alembic upgrade head`;
7. `uvicorn --port 8000 server.app:app`;
8. `xdg-open http://localhost:8000/`.

### Docker

1. Установите, настройте и запустите Docker с плагином docker-compose;
2. `cp .env.dist .env`;
3. `vim .env`;
4. `docker compose -f compose.yaml -f compose.dev.yaml up -d --build`;
5. `xdg-open http://localhost:8000/`.

## Помощь в разработке

Если вы нашли ошибку в приложении, пожалуйста, напишите мне в [Telegram][tg] или создайте [issue].

Приложение написано на Python 3.12 с использованием FastAPI и SQLAlchemy 2.0. Для управления
миграциями используется Alembic.

[app]: https://github.com/evgfilim1/mafia-companion
[tg]: https://t.me/evgfilim1
[issue]: https://github.com/evgfilim1/mafia-companion-api/issues/new

