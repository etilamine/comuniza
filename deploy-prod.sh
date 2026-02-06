#!/bin/bash
# deploy-prod.sh - Complete production deployment script for Comuniza
# This script handles complete production deployment process

set -e

# Check for reset flag
RESET_DB=false
if [ "$1" = "--reset-db" ]; then
    RESET_DB=true
    echo "🔄 Database reset requested - will wipe all data!"
    echo "   ⚠️  This will delete ALL data including users and content!"
    read -p "   Are you sure? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "   Database reset cancelled."
        exit 0
    fi
    shift
elif [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Comuniza Production Deployment Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --reset-db    Reset database (WARNING: deletes all data)"
    echo "  --no-cache    Rebuild without Docker cache"
    echo "  --help, -h    Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Normal deployment"
    echo "  $0 --no-cache         # Clean rebuild"
    echo "  $0 --reset-db         # Fresh database deployment"
    exit 0
fi

echo "🚀 Deploying Comuniza to Production..."

# Auto-detect and set UID/GID for proper permissions
echo "🔍 Detecting current user UID/GID..."
export HOST_UID=$(id -u)
export HOST_GID=$(id -g)
echo "   ✅ Detected HOST_UID=${HOST_UID}, HOST_GID=${HOST_GID}"

# Step 1: Clean up
echo "📋 Step 1: Cleaning up..."
docker compose --env-file ~/.env.production down
docker volume prune -f
docker system prune -f

# Set volume paths for production
export STATIC_VOLUME=/var/www/comuniza/storage/assets
export MEDIA_VOLUME=/var/www/comuniza/storage/media
export LOGS_VOLUME=/var/www/comuniza/storage/logs

# Step 2: Create storage directory structure
echo "📁 Step 2: Creating storage directory structure..."
mkdir -p $STATIC_VOLUME $MEDIA_VOLUME $LOGS_VOLUME
echo "   ✅ Created storage directory structure"
echo "   ├── $STATIC_VOLUME (for static files)"
echo "   ├── $MEDIA_VOLUME (for user uploads)"
echo "   └── $LOGS_VOLUME (for application logs)"

# Step 3: Build and start database
echo "🗄️ Step 3: Building and starting database..."
# Use cache for faster builds, add --no-cache flag if you need complete rebuild
if [ "$1" = "--no-cache" ]; then
    echo "   Building without cache (explicit request)..."
    docker compose --env-file ~/.env.production build --no-cache
else
    echo "   Building with cache for faster deployment..."
    docker compose --env-file ~/.env.production build --pull
fi
docker compose --env-file ~/.env.production up -d postgres

# Step 4: Wait for database to be healthy
echo "⏳ Step 4: Waiting for database to be healthy..."
sleep 20

# Load environment variables for database connection
echo "   Loading database credentials for health check..."
if [ -f ~/.env.production ]; then
    # Parse environment file and export variables
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ $key =~ ^[[:space:]]*# ]] && continue
        [[ -z $key ]] && continue

        # Remove quotes from value if present
        value=$(echo "$value" | sed 's/^"\(.*\)"$/\1/' | sed "s/^'\(.*\)'$/\1/")
        export "$key=$value"
    done < ~/.env.production
else
    echo "   ⚠️  ~/.env.production not found, using default credentials for health check"
    export DB_USER="${DB_USER:-comuniza123}"
    export DB_PASSWORD="${DB_PASSWORD:-password123}"
fi

# Verify database is ready with proper health check
echo "   Verifying database connection..."
for i in {1..10}; do
    if docker compose --env-file ~/.env.production exec postgres psql -U ${DB_USER:-comuniza123} -d ${DB_NAME:-comuniza123} -c "SELECT 1" > /dev/null 2>&1; then
        echo "   ✅ Database is ready!"
        break
    else
        echo "   ⏳ Waiting for database... (attempt $i/10)"
        sleep 10
    fi
    if [ $i -eq 10 ]; then
        echo "   ❌ Database failed to start after 10 attempts"
        echo "   Check that DB_USER and DB_PASSWORD are correctly set in ~/.env.production"
        exit 1
    fi
done

# Reset database if requested
if [ "$RESET_DB" = true ]; then
    echo "🔄 Resetting database..."

    # Load environment variables from production file
    echo "   Loading database credentials from environment..."
    if [ ! -f ~/.env.production ]; then
        echo "   ❌ ~/.env.production file not found"
        exit 1
    fi

    # Parse environment file and export variables
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ $key =~ ^[[:space:]]*# ]] && continue
        [[ -z $key ]] && continue

        # Remove quotes from value if present
        value=$(echo "$value" | sed 's/^"\(.*\)"$/\1/' | sed "s/^'\(.*\)'$/\1/")
        export "$key=$value"
    done < ~/.env.production

    # Validate required environment variables
    if [ -z "${DB_USER}" ] || [ -z "${DB_PASSWORD}" ] || [ -z "${DB_NAME}" ]; then
        echo "   ❌ Missing required database environment variables"
        echo "   Required variables in ~/.env.production:"
        echo "   - DB_USER (current: ${DB_USER:-'not set'})"
        echo "   - DB_PASSWORD (current: ${DB_PASSWORD:-'not set'})"
        echo "   - DB_NAME (current: ${DB_NAME:-'not set'})"
        exit 1
    fi

    # Test database connection before destructive operation
    echo "   Testing database connection with provided credentials..."
    if ! docker compose --env-file ~/.env.production exec postgres psql \
        -U ${DB_USER} -d postgres -c "SELECT 1;" > /dev/null 2>&1; then
        echo "   ❌ Cannot connect to database with provided credentials"
        echo "   Please check DB_USER, DB_PASSWORD in ~/.env.production"
        echo "   Current values: DB_USER=${DB_USER}, DB_NAME=${DB_NAME}"
        exit 1
    fi
    echo "   ✅ Database credentials verified"

    # Drop and recreate the database using environment variables
    echo "   Performing database reset (this will delete ALL data)..."
    if docker compose --env-file ~/.env.production exec postgres psql \
        -U ${DB_USER} -d postgres -c "
            DROP DATABASE IF EXISTS ${DB_NAME};
            CREATE DATABASE ${DB_NAME} WITH ENCODING 'UTF8' LC_COLLATE='C' LC_CTYPE='C';
        " > /dev/null 2>&1; then
        echo "   ✅ Database reset completed successfully!"
        echo "   📝 Note: All data has been permanently deleted"
        echo "   🔄 Run deployment again to create fresh database schema"
    else
        echo "   ❌ Database reset failed!"
        echo "   Check database logs and environment configuration"
        exit 1
    fi
fi

# Step 5: Start Redis and wait for health
echo "🔴 Step 5: Starting Redis and waiting for health..."
docker compose --env-file ~/.env.production up -d redis

# Wait for Redis to be healthy
for i in {1..8}; do
    if docker compose --env-file ~/.env.production exec redis redis-cli ping > /dev/null 2>&1; then
        echo "   ✅ Redis is ready!"
        break
    else
        echo "   ⏳ Waiting for Redis... (attempt $i/8)"
        sleep 5
    fi
    if [ $i -eq 8 ]; then
        echo "   ❌ Redis failed to start after 8 attempts"
        exit 1
    fi
done

# Step 6: Start application services
echo "🌐 Step 6: Starting application services..."
docker compose --env-file ~/.env.production up -d app celery

# Step 7: Wait for app to be ready
echo "⏳ Step 7: Waiting for application to be ready..."
sleep 15

# Verify app is ready before migrations
echo "   Verifying app health..."
for i in {1..6}; do
    if docker compose --env-file ~/.env.production exec app python manage.py check --deploy > /dev/null 2>&1; then
        echo "   ✅ App is ready!"
        break
    else
        echo "   ⏳ Waiting for app... (attempt $i/6)"
        sleep 5
    fi
    if [ $i -eq 6 ]; then
        echo "   ❌ App failed to become ready after 6 attempts"
        docker compose --env-file ~/.env.production logs app --tail=20
        exit 1
    fi
done

# Step 8: Run migrations
echo "🔄 Step 7: Running database migrations..."

# Show current migration status before running
echo "   Checking migration status..."
docker compose --env-file ~/.env.production exec app python manage.py showmigrations --verbosity=0

# Run migrations with verbose output for debugging
echo "   Running migrations with verbose output..."
if docker compose --env-file ~/.env.production exec app python manage.py migrate --verbosity=2; then
    echo "   ✅ Migrations completed successfully!"
    MIGRATIONS_SUCCESS=true
else
    echo "   ❌ Migrations failed, checking detailed logs..."
    docker compose --env-file ~/.env.production logs app --tail=50
    
    echo "   📋 Migration status after failure:"
    docker compose --env-file ~/.env.production exec app python manage.py showmigrations --verbosity=1
    
    echo "   ⚠️  MIGRATION FAILED - DO NOT use --fake to skip this issue!"
    echo "   Please investigate the error above and fix the root cause."
    echo "   Common issues:"
    echo "   1. Circular imports in model save() methods"
    echo "   2. Missing dependencies in migrations"
    echo "   3. Database connection issues"
    echo "   4. Missing installed apps in settings"
    exit 1
fi

# Step 9: Collect static files
echo "📦 Step 8: Collecting static files..."
echo "   Running collectstatic to storage/assets/..."
if [ "$MIGRATIONS_SUCCESS" = true ] && docker compose --env-file ~/.env.production exec app python manage.py collectstatic --noinput --clear; then
    echo "   ✅ Static files collected successfully!"
    echo "   Verifying static files exist..."
    if [ -f "$STATIC_VOLUME/css/base.css" ]; then
        echo "   ✅ CSS files are ready!"
        ls -la $STATIC_VOLUME/css/ | head -5
    else
        echo "   ❌ CSS files not found!"
        ls -la $STATIC_VOLUME/ || echo "   Directory doesn't exist"
    fi
else
    echo "   ❌ Static files collection failed, checking logs..."
    docker compose --env-file ~/.env.production logs app --tail=10
fi

# Step 10: Create superuser if needed
echo "👤 Step 9: Creating superuser..."
if docker compose --env-file ~/.env.production exec app python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
try:
    if not User.objects.filter(is_superuser=True).exists():
        user = User.objects.create_superuser('admin@comuniza.org', 'admin123', first_name='Admin', username='AdminUser')
        print('✅ Superuser created successfully')
        print(f'   Username: {user.username}')
        print(f'   Email: {user.email}')
    else:
        admin = User.objects.filter(is_superuser=True).first()
        print('✅ Superuser already exists')
        print(f'   Username: {admin.username}')
        print(f'   Email: {admin.email}')
except Exception as e:
    print(f'❌ Error creating superuser: {e}')
    import traceback
    traceback.print_exc()
" > /dev/null 2>&1; then
    echo "   ✅ Superuser setup completed!"
else
    echo "   ❌ Superuser setup failed, checking logs..."
    docker compose --env-file ~/.env.production logs app --tail=10
fi

# Step 11: Restart services to ensure clean state
echo "🔄 Step 10: Restarting services..."
docker compose --env-file ~/.env.production restart

# Step 11.5: Re-collect static files after restart (ensures clean state)
echo "📦 Step 10.5: Re-collecting static files after restart..."
if docker compose --env-file ~/.env.production exec app python manage.py collectstatic --noinput --clear > /dev/null 2>&1; then
    echo "   ✅ Post-restart static files collection successful!"
else
    echo "   ⚠️  Post-restart static files collection failed (may still work)"
fi

# Step 12: Verify deployment
echo "✅ Step 11: Verifying deployment..."
sleep 10

echo "📊 Container Status:"
docker compose --env-file ~/.env.production ps

# Check for any restarting containers
RESTARTING=$(docker compose --env-file ~/.env.production ps | grep -c "Restarting" || echo "0")
if [ "$RESTARTING" -eq "0" ]; then
    echo "✅ All containers are running properly!"
else
    echo "❌ Some containers are still restarting. Checking logs..."
    docker compose --env-file ~/.env.production logs --tail=20
fi

# Step 13: Test application access
echo "🌐 Step 12: Testing application access..."
if curl -s http://localhost:4002 > /dev/null; then
    echo "✅ Application is accessible locally!"
else
    echo "❌ Application not accessible locally. Checking logs..."
    docker compose --env-file ~/.env.production logs app --tail=10
fi

# Step 14: Test database connectivity
echo "🗄️ Step 13: Testing database connectivity..."
if docker compose --env-file ~/.env.production exec app python manage.py check --deploy > /dev/null 2>&1; then
    echo "   ✅ Database connectivity verified!"
else
    echo "   ❌ Database connection failed. Checking logs..."
    docker compose --env-file ~/.env.production logs app --tail=10
fi

echo "🎯 Production deployment complete!"
echo ""
# Step 15: Final verification
echo "🔍 Step 14: Final verification..."
echo "   Testing CSS access..."
if curl -s -I http://localhost:4002/static/css/base.css | grep -q "200 OK"; then
    echo "   ✅ CSS files are accessible!"
else
    echo "   ❌ CSS files not accessible!"
    echo "   Checking storage directory:"
    ls -la $STATIC_VOLUME/ || echo "   No static files directory found"
fi

echo "🎯 Production deployment complete!"
echo ""
echo "🌐 Next steps:"
echo "   - Test external access: curl -I http://$(curl -s ifconfig.me):4002"
echo "   - Test CSS: curl -I http://$(curl -s ifconfig.me):4002/static/css/base.css"
echo "   - View logs: docker compose --env-file ~/.env.production logs -f app"
echo "   - Access shell: docker compose --env-file ~/.env.production shell-prod"
echo "   - Check status: docker compose --env-file ~/.env.production status-prod"
echo "   - Rebuild without cache: ./deploy-prod.sh --no-cache"
echo "   - Reset database: ./deploy-prod.sh --reset-db"
echo "   - Show help: ./deploy-prod.sh --help"
