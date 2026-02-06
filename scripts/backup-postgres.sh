#!/bin/bash
# PostgreSQL Encrypted Backup Script for Production
set -e

BACKUP_DIR="$HOME/comuniza-backups"
PASSPHRASE_FILE="$HOME/.comuniza_backup_passphrase"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Check if passphrase file exists
if [ ! -f "$PASSPHRASE_FILE" ]; then
    echo "❌ Backup passphrase file not found: $PASSPHRASE_FILE"
    echo "Please create it with: echo 'your-strong-passphrase' > $PASSPHRASE_FILE"
    exit 1
fi

echo "🔄 Creating PostgreSQL encrypted backup (production)..."

# Create encrypted backup
docker ~/.env.production exec comuniza-db pg_dump -U "${DB_USER:-comuniza123}" -d "${DB_NAME:-comuniza123}" | \
gpg --batch --yes --passphrase "$(cat $PASSPHRASE_FILE)" --symmetric \
    --cipher-algo AES256 --compress-algo 1 \
    > "$BACKUP_DIR/postgres_prod_${DATE}.sql.gpg"

echo "✅ PostgreSQL backup created: postgres_prod_${DATE}.sql.gpg"
echo "📁 Backup location: $BACKUP_DIR"

# Optional: Upload to remote storage (uncomment and configure as needed)
# echo "📤 Uploading backup to remote storage..."
# scp "$BACKUP_DIR/postgres_prod_${DATE}.sql.gpg" user@backup-server:/backups/

# Keep only last 30 days (be more conservative in production)
find "$BACKUP_DIR" -name "*.sql.gpg" -mtime +30 -delete

echo "🧹 Cleaned up old backups (kept last 30 days)"
