# Расчёты через RabbitMQ

Producer раз в две секунды публикует пару чисел в topic-exchange `calc`. Ключ маршрута — операция: `calc.add`, `calc.sub`, `calc.mul` или `calc.div`. Consumer забирает сообщение из очереди `calc.tasks`, считает и пишет строку в журнал. Деление на ноль и битое тело не подтверждаются: брокер перекладывает их в `calc.dlq`.

Каждая вторая операция `div` отправляется с `b = 0`, чтобы отказ и DLQ было видно без ручной порчи сообщения.

## Что чем является

| Файл | Роль |
| --- | --- |
| `producer/` | Периодическая отправка в exchange `calc` |
| `consumer/` | Расчёт и журнал. Отказ уходит в DLQ |
| `docker-compose.yml` | RabbitMQ, producer и consumer |

Очередь `calc.tasks` подписана на ключ `calc.*` и настроена с `x-dead-letter-exchange: calc.dlx`. Обмен `calc.dlx` — fanout в очередь `calc.dlq`. Топологию объявляют оба приложения, повторное объявление безопасно.

Учётные данные брокера демонстрационные: `guest` / `guest`. Панель управления: http://127.0.0.1:15672/

## Запуск

Из этой папки:

```bash
docker compose up -d --build
docker compose ps
```

Дождитесь, пока `rabbitmq` станет healthy, а producer и consumer — running.

## Проверка

Все команды ниже — в терминале из папки `rabbitmq`. На Windows вместо `curl` пишите `curl.exe`. Журнал consumer — это его stdout.

**1. Убедиться, что три сервиса запущены.**

```bash
docker compose ps
```

**2. Посмотреть журнал расчётов.** Строки `ok` — успешные операции. Строки `fail ... -> dlq` — отказ, сообщение ушло в DLQ.

```bash
docker compose logs consumer --tail 30
```

Повторите команду через несколько секунд: появятся новые `ok` для `add`, `sub`, `mul` и `div`, и периодический `fail` на делении на ноль.

**3. Посмотреть, что producer публикует с разными ключами.**

```bash
docker compose logs producer --tail 20
```

В строках есть `routing_key=calc.add` и остальные три ключа.

**4. Посчитать сообщения в очередях.**

```bash
docker compose exec rabbitmq rabbitmqctl list_queues name messages
```

`calc.tasks` близка к нулю: consumer успевает забирать. `calc.dlq` больше нуля: туда легли деления на ноль.

**5. Прочитать одно сообщение из DLQ, не удаляя его из очереди.** Запрос идёт в панель управления брокера.

В PowerShell адрес берите в одинарные кавычки, иначе `%2F` испортится:

```powershell
curl.exe -sS -u guest:guest -H "content-type: application/json" -d '{"count":1,"ackmode":"ack_requeue_true","encoding":"auto"}' 'http://127.0.0.1:15672/api/queues/%2F/calc.dlq/get'
```

В теле будут поля `a` и `b`. У отказа `b` равен `0`. `ackmode` с `ack_requeue_true` возвращает сообщение в очередь.

## Остановка

```bash
docker compose down
```
