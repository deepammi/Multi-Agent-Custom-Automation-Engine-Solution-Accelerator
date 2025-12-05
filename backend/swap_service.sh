#!/bin/bash
# Script to swap between simple and complex langextract service

set -e

BACKUP_DIR="backend/app/services/backups"
SIMPLE_SERVICE="backend/app/services/langextract_service_simple.py"
CURRENT_SERVICE="backend/app/services/langextract_service.py"

# Create backup directory
mkdir -p "$BACKUP_DIR"

case "$1" in
    "use-simple")
        echo "📦 Backing up current service..."
        cp "$CURRENT_SERVICE" "$BACKUP_DIR/langextract_service_complex_$(date +%Y%m%d_%H%M%S).py"
        
        echo "🔄 Switching to simplified service..."
        cp "$SIMPLE_SERVICE" "$CURRENT_SERVICE"
        
        echo "✅ Now using SIMPLIFIED service"
        echo "   Test with: python3 backend/test_simple_service.py"
        ;;
        
    "use-complex")
        echo "🔄 Restoring complex service..."
        LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/langextract_service_complex_*.py 2>/dev/null | head -1)
        
        if [ -z "$LATEST_BACKUP" ]; then
            echo "❌ No backup found!"
            exit 1
        fi
        
        cp "$LATEST_BACKUP" "$CURRENT_SERVICE"
        echo "✅ Restored complex service from: $LATEST_BACKUP"
        ;;
        
    "test")
        echo "🧪 Testing current service..."
        cd backend
        python3 test_simple_service.py
        ;;
        
    *)
        echo "Usage: $0 {use-simple|use-complex|test}"
        echo ""
        echo "Commands:"
        echo "  use-simple   - Switch to simplified service (backs up current)"
        echo "  use-complex  - Restore complex service from backup"
        echo "  test         - Test current service"
        exit 1
        ;;
esac
