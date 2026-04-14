run:
	docker compose up -d --build

stop:
	docker compose stop

down:
	docker compose down -v

testdb:
	docker run -d \
  --name test_postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=postgres \
  -p 5432:5432 \
  --restart always \
  postgres:17