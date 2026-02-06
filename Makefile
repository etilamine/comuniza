.PHONY: help dev dev-fast dev-reload dev-status prod build migrate superuser test clean logs shell migrate-prod collectstatic-prod superuser-prod logs-prod shell-prod status-prod restart-prod migrate-db migrate-db-verify clean-old-vols

help:
	@echo "Comuniza - Sharing Community Platform"
	@echo ""
	@echo "Available commands:"
	@echo "  make dev        - Start development environment (standard)"
	@echo "  make dev-fast   - Start development environment with hot reload"
	@echo "  make dev-reload - Restart development server with reload"
	@echo "  make dev-status - Check development containers status"
	@echo "  make prod       - Start production environment"
	@echo "  make build      - Build Docker images"
	@echo "  make migrate    - Run database migrations"
	@echo "  make superuser  - Create Django superuser"
	@echo "  make test       - Run tests"
	@echo "  make clean      - Remove containers and volumes"
	@echo "  make logs       - View application logs"
	@echo "  make shell      - Open Django shell"
	@echo "  make format     - Format code with black/isort"
	@echo ""
	@echo "Production commands:"
	@echo "  make migrate-prod     - Run database migrations in production"
	@echo "  make collectstatic-prod - Collect static files in production"
	@echo "  make superuser-prod    - Create Django superuser in production"
	@echo "  make logs-prod         - View production application logs"
	@echo "  make shell-prod        - Open Django shell in production"
	@echo "  make status-prod       - Show production container status"
	@echo "  make restart-prod      - Restart production services"

dev:
	docker compose --env-file ~/.env.development up

prod:
	docker compose --env-file ~/.env.production up -d

build:
	docker compose --env-file ~/.env.development build

migrate:
	docker compose --env-file ~/.env.development exec app python manage.py migrate

superuser:
	docker compose --env-file ~/.env.development exec app python manage.py createsuperuser

test:
	docker compose --env-file ~/.env.development exec app python manage.py test

clean:
	docker compose --env-file ~/.env.development down -v
	docker system prune -f

logs:
	docker compose --env-file ~/.env.development logs -f app

shell:
	docker compose --env-file ~/.env.development exec app python manage.py shell_plus

format:
	docker compose --env-file ~/.env.development exec app black .
	docker compose --env-file ~/.env.development exec app isort .

# Add production commands
migrate-prod:
	docker compose --env-file ~/.env.production exec app python manage.py migrate

collectstatic-prod:
	docker compose --env-file ~/.env.production exec app python manage.py collectstatic --noinput

superuser-prod:
	docker compose --env-file ~/.env.production exec app python manage.py createsuperuser

logs-prod:
	docker compose --env-file ~/.env.production logs -f app

shell-prod:
	docker compose --env-file ~/.env.production exec app python manage.py shell_plus

status-prod:
	docker compose --env-file ~/.env.production ps

restart-prod:
	docker compose --env-file ~/.env.production restart

# Database migration commands
migrate-db:
	@echo "🔄 Safely migrating database from old to new volumes..."
	./safe-migrate.sh

migrate-db-verify:
	@echo "🔍 Verifying database migration status..."
	./migrate-database.sh verify

clean-old-vols:
	@echo "🧹 Cleaning old database volumes (with confirmation)..."
	./migrate-database.sh clean

# Quick migration and deploy
migrate-deploy:
	@echo "🚀 Migrate and deploy in one command..."
	./migrate-and-deploy.sh

# Database volume management
list-vols:
	@echo "📊 Listing database volumes..."
	./migrate-database.sh list

backup-db:
	@echo "📦 Backing up current database..."
	./backup-postgres.sh

backup-postgres:
	@echo "📦 Backing up PostgreSQL database..."
	./backup-postgres.sh

backup-postgres-dev:
	@echo "📦 Backing up PostgreSQL database (development)..."
	./backup-postgres-dev.sh

backup-prod:
	@echo "📦 Backing up PostgreSQL database (production)..."
	./backup-postgres.sh

# Enhanced development commands
dev-fast:
	@echo "🚀 Starting fast development environment with hot reload..."
	./deploy-dev-fast.sh

dev-reload:
	@echo "🔄 Restarting development server with reload..."
	docker compose -f docker-compose.yml -f docker-compose.dev.yml restart app

dev-status:
	@echo "📊 Development environment status:"
	docker compose -f docker-compose.yml -f docker-compose.dev.yml ps
