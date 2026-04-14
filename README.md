## Payment Service (PAYLY)

ДЕМО Сервис для приёма платежей с **API + outbox publisher + consumer**:

- **API (FastAPI)** принимает платёж, пишет его в PostgreSQL и кладёт событие в outbox.
- **Publisher** читает outbox и публикует события в **RabbitMQ**.
- **Consumer** читает сообщения из RabbitMQ и обрабатывает их (в т.ч. вызывает webhook).


### Требования
- Docker (тестировалось на Windows)
- docker compose

### ЗАПУСК
1) Убедитесь, что файл `.env` существует в корне репозитория.
2) Поднимите сервисы:

```bash
git clone https://github.com/ruslanakhmett/payment-service.git
```

```bash
docker compose up --build
```

3) Откройте:

- **Swagger UI**: `http://localhost:5000/docs`
- **RabbitMQ Management UI**: `http://localhost:15672` (логин/пароль в `.env`)


## Переменные окружения
Compose читает настройки из файла`.env`.
> Важно: `.env` содержит секреты. Не используйте боевые значения в репозитории.


### СОЗДАТЬ ПЛАТЕЖ

Запрос:
```bash
curl -X 'POST' \
  'http://localhost:5000/api/v1/payments' \
  -H 'accept: application/json' \
  -H 'Idempotency-Key: test123' \
  -H 'X-API-Key: dev_api_key_change_me' \
  -H 'Content-Type: application/json' \
  -d '{
  "amount": 1000,
  "currency": "RUB",
  "description": "string",
  "metadata": {
    "additionalProp1": {}
  },
  "webhook_url": "http://api:5000/api/v1/webhook/test"
}'
```

Ответ:
```bash
{
  "payment_id": "d5c0b26e-45ee-407c-932e-b70e4818c27a",
  "status": "pending",
  "created_at": "2026-04-14T12:10:32.632757Z"
}
```


### ПОЛУЧИТЬ ПЛАТЕЖ
```bash
curl -X 'GET' \
  'http://localhost:5000/api/v1/payments/d5c0b26e-45ee-407c-932e-b70e4818c27a' \
  -H 'accept: application/json' \
  -H 'X-API-Key: dev_api_key_change_me'
```

Ответ:
```bash
{
  "payment_id": "d5c0b26e-45ee-407c-932e-b70e4818c27a",
  "amount": "1000.00",
  "currency": "RUB",
  "description": "string",
  "metadata": {
    "additionalProp1": {}
  },
  "webhook_url": "http://api:5000/api/v1/webhook/test",
  "status": "succeeded",
  "created_at": "2026-04-14T12:10:32.632757Z",
  "processed_at": "2026-04-14T12:10:37.594011Z"
}
```