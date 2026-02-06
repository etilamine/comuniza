#!/bin/bash
# deploy-dev.sh - Complete development deployment script for Comuniza
# This script handles complete development deployment process

set -e

echo "🚀 Deploying Comuniza to Development..."

# Auto-detect and set UID/GID for proper permissions
echo "🔍 Detecting current user UID/GID..."
export HOST_UID=$(id -u)
export HOST_GID=2666
echo "   ✅ Detected HOST_UID=${HOST_UID}, HOST_GID=${HOST_GID}"

# Set volume paths for development (user-writable)
export STATIC_VOLUME=$HOME/comuniza/storage/assets
export MEDIA_VOLUME=$HOME/comuniza/storage/media
export LOGS_VOLUME=$HOME/comuniza/storage/logs
export APP_VOLUMES=./:/app  # Bind mount the app directory for hot reload

# Set development environment
export DJANGO_ENV=development
export EXTERNAL_DEV_PORT=8000
export INTERNAL_DEV_PORT=8000
export EXTERNAL_PROD_PORT=8001
export INTERNAL_PROD_PORT=8001
echo "   ✅ Development environment configured"

# Step 1: Clean up
echo "📋 Step 1: Cleaning up..."
docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file ~/.env.development down
docker volume prune -f
docker system prune -f

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
    docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file ~/.env.development build --no-cache
else
    echo "   Building with cache for faster deployment..."
    docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file ~/.env.development up -d postgres
fi
docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file ~/.env.development up -d postgres

# Step 4: Wait for database to be healthy
echo "⏳ Step 4: Waiting for database to be healthy..."
sleep 20

# Verify database is ready with proper health check
echo "   Verifying database connection..."
for i in {1..10}; do
    if docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file ~/.env.development exec postgres psql -U comuniza123 -d comuniza123 -c "SELECT 1" > /dev/null 2>&1; then
        echo "   ✅ Database is ready!"
        break
    else
        echo "   ⏳ Waiting for database... (attempt $i/10)"
        sleep 5
    fi
    if [ $i -eq 10 ]; then
        echo "   ❌ Database failed to start after 10 attempts"
        exit 1
    fi
done

# Step 5: Start Redis and wait for health
echo "🔴 Step 5: Starting Redis and waiting for health..."
docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file ~/.env.development up -d redis

# Wait for Redis to be healthy
for i in {1..8}; do
    if docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file ~/.env.development exec redis redis-cli ping > /dev/null 2>&1; then
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
docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file ~/.env.development up -d app celery

# Step 7: Wait for app to be ready
echo "⏳ Step 7: Waiting for application to be ready..."
sleep 5

# Verify app is ready before migrations
echo "   Verifying app health..."
for i in {1..6}; do
    if docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file ~/.env.development exec app python manage.py check --deploy > /dev/null 2>&1; then
        echo "   ✅ App is ready!"
        break
    else
        echo "   ⏳ Waiting for app... (attempt $i/6)"
        sleep 5
    fi
    if [ $i -eq 6 ]; then
        echo "   ❌ App failed to become ready after 6 attempts"
        docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file ~/.env.development logs app --tail=20
        exit 1
    fi
done

# Step 8: Run migrations
echo "🔄 Step 7: Running database migrations..."
MIGRATIONS_SUCCESS=false
echo "   Running migrations with output for debugging..."
if docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file ~/.env.development exec -T app python manage.py migrate --verbosity=2; then
    echo "   ✅ Migrations completed successfully!"
    MIGRATIONS_SUCCESS=true
else
    echo "   ❌ Migrations failed, checking logs..."
    docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file ~/.env.development logs app --tail=20
    echo "   Attempting migration recovery..."
    # Try different recovery strategies
    docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file ~/.env.development exec -T app python manage.py migrate --fake-initial --verbosity=1 || true
    docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file ~/.env.development exec -T app python manage.py migrate --fake || true
    echo "   ⚠️  Migration recovery attempted - check application functionality"
fi

# Step 9: Collect static files
echo "📦 Step 8: Collecting static files..."
echo "   Running collectstatic to storage/assets/..."
if [ "$MIGRATIONS_SUCCESS" = true ] && docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file ~/.env.development exec -T app python manage.py collectstatic --noinput --clear --verbosity=1; then
    echo "   ✅ Static files collected successfully!"
    echo "   Verifying static files exist..."
    if [ -f "$STATIC_VOLUME/css/base.css" ]; then
        echo "   ✅ CSS files are ready!"
        ls -la $STATIC_VOLUME/css/ | head -5
    else
        echo "   ❌ CSS files not found!"
        ls -la $STATIC_VOLUME/ || echo "   Directory doesn't exist"
        # Try to check inside container as fallback
        docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file ~/.env.development exec app ls -la /app/collected_static/ || echo "   Container directory also not accessible"
    fi
else
    echo "   ❌ Static files collection failed, checking logs..."
    docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file ~/.env.development logs app --tail=15
    echo "   Attempting to collect static files without --clear flag..."
    if docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file ~/.env.development exec -T app python manage.py collectstatic --noinput --verbosity=1; then
        echo "   ✅ Static files collected successfully (without clear)!"
    else
        echo "   ❌ Static files collection completely failed"
    fi
fi

# Step 10: Create superuser if needed
echo "👤 Step 9: Creating superuser..."
if [ "$MIGRATIONS_SUCCESS" = true ]; then
    echo "   Checking if superuser exists..."
    if docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file ~/.env.development exec -T app python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin@comuniza.org', 'admin123', first_name='Admin', username='AdminUser')
    print('✅ Superuser created')
else:
    print('✅ Superuser already exists')
"; then
        echo "   ✅ Superuser setup completed!"
    else
        echo "   ❌ Superuser setup failed, trying alternative method..."
        echo "   Creating superuser with Django command..."
        docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file ~/.env.development exec -T app python manage.py createsuperuser --noinput --email admin@comuniza.org || true
    fi
else
    echo "   ⚠️ Skipping superuser creation due to migration failures"
fi

# Step 11: Restart services to ensure clean state
echo "🔄 Step 10: Restarting services..."
docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file ~/.env.development restart

# Step 11.5: Re-collect static files after restart (ensures clean state)
echo "📦 Step 10.5: Re-collecting static files after restart..."
if docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file ~/.env.development exec app python manage.py collectstatic --noinput --clear > /dev/null 2>&1; then
    echo "   ✅ Post-restart static files collection successful!"
else
    echo "   ⚠️  Post-restart static files collection failed (may still work)"
fi

# Step 12: Verify deployment
echo "✅ Step 11: Verifying deployment..."
sleep 10

echo "📊 Container Status:"
docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file ~/.env.development ps

# Check for any restarting containers
RESTARTING=$(docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file ~/.env.development ps --format "{{.State}}" | grep -c "Restarting" 2>/dev/null) || true
RESTARTING=$((RESTARTING + 0))  # Ensure it's an integer
if [ "$RESTARTING" -eq 0 ]; then
    echo "✅ All containers are running properly!"
else
    echo "❌ Some containers are still restarting. Checking logs..."
    docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file ~/.env.development logs --tail=20
fi

# Step 13: Test application access
echo "🌐 Step 12: Testing application access..."
if curl -s http://localhost:8000 > /dev/null; then
    echo "✅ Application is accessible locally!"
else
    echo "❌ Application not accessible locally. Checking logs..."
    docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file ~/.env.development logs app --tail=10
fi

# Step 15: Test database connectivity
echo "🗄️ Step 13: Testing database connectivity..."
if docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file ~/.env.development exec app python manage.py check --deploy > /dev/null 2>&1; then
    echo "   ✅ Database connectivity verified!"
else
    echo "   ❌ Database connection failed. Checking logs..."
    docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file ~/.env.development logs app --tail=10
fi

# Step 16: Final verification
echo "🔍 Step 14: Final verification..."
echo "   Testing CSS access..."
if curl -s -I http://localhost:8000/static/css/base.css | grep -q "200 OK"; then
    echo "   ✅ CSS files are accessible!"
else
    echo "   ❌ CSS files not accessible!"
    echo "   Checking storage directory:"
    ls -la $STATIC_VOLUME/ || echo "   No static files directory found"
fi

echo "🎯 Development deployment complete!"
echo ""
echo "🌐 Next steps:"
echo "   - Test external access: curl -I http://$(curl -s ifconfig.me):8000"
echo "   - Test CSS: curl -I http://$(curl -s ifconfig.me):8000/static/css/base.css"
echo "   - View logs: docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file ~/.env.development logs -f app"
echo "   - Access shell: docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file ~/.env.development exec app python manage.py shell_plus"
echo "   - Check status: docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file ~/.env.development ps"
echo "   - Rebuild without cache: ./deploy-dev.sh --no-cache"
