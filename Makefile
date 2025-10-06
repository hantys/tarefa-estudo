# Comandos de produção
start-build:
	docker compose up --profile dev -d --build --remove-orphans

start:
	docker compose --profile dev up -d

bash:
	docker compose exec tarefas-dev sh

# Comandos gerais
stop:
	docker compose down; docker system prune -f

logs:
	docker compose logs -f

clean:
	docker compose down -v
	docker system prune -a -f

