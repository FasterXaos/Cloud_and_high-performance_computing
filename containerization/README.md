# XArcanoid: таблица рекордов в двух контейнерах

Тот же сеттинг, что у [XArcanoid](https://github.com/FasterXaos/XArcanoid): арканоид, забеги, сложности. Здесь нет самой игры и регистрации. Точка входа хранит законченные забеги и отдаёт таблицу.

`entrypoint` принимает HTTP. PostgreSQL (`db`) живёт в той же сети Docker, хост `db:5432`. Каталог данных — именованный том `score-data`, поэтому строки остаются при `restart` и при пересоздании контейнеров (`down` без `-v`, затем `up`).

PostgreSQL вместо SQLite из игры: у SQLite нет сетевого протокола, второй контейнер не может запросить его по сети.

Демо-учётные данные базы, они же в `docker-compose.yml`: пользователь `xarcanoid`, пароль `xarcanoid`, база `xarcanoid`. Порт PostgreSQL наружу не опубликован.

Один забег — одна строка с именем игрока. Учётных записей и паролей здесь нет. Practice в таблицу не пишется, как и в игре.

## Запуск

Из этой папки:

```bash
docker compose up -d --build
```

Дождаться, пока оба сервиса станут healthy / running:

```bash
docker compose ps
```

Точка входа: http://localhost:8080/

Если том остался от предыдущей схемы, сотри его и подними заново: `docker compose down -v`, затем команда запуска выше.

## Проверка запросов

Сид в `database/init.sql` кладёт пять забегов при первом создании тома.

```bash
curl http://localhost:8080/health
curl http://localhost:8080/leaderboard
curl "http://localhost:8080/leaderboard?mode=campaign"
curl http://localhost:8080/scores/1
```

Новый забег через точку входа:

```bash
curl -X POST http://localhost:8080/scores \
  -H "Content-Type: application/json" \
  -d "{\"player\":\"PaddleGhost\",\"score\":50120,\"level\":6,\"max_combo\":11,\"difficulty\":\"overdrive\",\"mode\":\"survival\"}"
```

В PowerShell `curl` — это алиас `Invoke-WebRequest`, а кавычки в JSON он съедает у `curl.exe`. Рабочие варианты:

```powershell
curl.exe http://localhost:8080/health
curl.exe http://localhost:8080/leaderboard
curl.exe --% -X POST http://localhost:8080/scores -H "Content-Type: application/json" --data-raw "{\"player\":\"PaddleGhost\",\"score\":50120,\"level\":6,\"max_combo\":11,\"difficulty\":\"overdrive\",\"mode\":\"survival\"}"
```

```powershell
Invoke-RestMethod http://localhost:8080/leaderboard
Invoke-RestMethod -Method Post -Uri http://localhost:8080/scores -ContentType "application/json" -Body '{"player":"PaddleGhost","score":50120,"level":6,"max_combo":11,"difficulty":"overdrive","mode":"survival"}'
```

Ответ `POST` — созданный забег с `id`. Его должен вернуть следующий `GET /scores`. В `GET /leaderboard` игрок попадает, только если этот счёт лучший для него в выбранном режиме.

## Данные переживают перезапуск

Перезапуск процессов, тома не трогает:

```bash
docker compose restart
curl http://localhost:8080/scores
```

Удаление контейнеров и подъём заново. Том `score-data` остаётся, сид повторно не выполняется, добавленный забег на месте:

```bash
docker compose down
docker compose up -d
curl http://localhost:8080/scores
```

Стереть данные можно только вместе с томом:

```bash
docker compose down -v
```

## Что внутри

| Путь | Роль |
| --- | --- |
| `database/Dockerfile` | Образ базы: `postgres:16-alpine` и скрипт инициализации |
| `database/init.sql` | Таблица `scores` и пять стартовых забегов |
| `entrypoint/Dockerfile` | Образ точки входа |
| `entrypoint/app.py` | HTTP API таблицы |
| `docker-compose.yml` | Сеть `xarcanoid-net`, том `score-data`, оба сервиса |

Эндпоинты точки входа:

| Метод | Путь | Действие |
| --- | --- | --- |
| GET | `/health` | Проверка, что база отвечает |
| GET | `/leaderboard?mode=` | Лучший забег каждого игрока. Режим `survival` (по умолчанию) или `campaign` |
| GET | `/scores` | Все забеги |
| GET | `/scores/<id>` | Один забег |
| POST | `/scores` | Тело `{player, score, level, max_combo, difficulty, mode}` |

`difficulty`: `standard` или `overdrive`. `mode`: `campaign` или `survival`.

## Docker Hub

Публикация образов в задании необязательна. Локальные теги после сборки: `xarcanoid-db:local` и `xarcanoid-entrypoint:local`.

```bash
docker tag xarcanoid-db:local <dockerhub-user>/xarcanoid-db:1.0
docker tag xarcanoid-entrypoint:local <dockerhub-user>/xarcanoid-entrypoint:1.0
docker push <dockerhub-user>/xarcanoid-db:1.0
docker push <dockerhub-user>/xarcanoid-entrypoint:1.0
```
