#!/bin/bash
# Upload secrets to Google Secret Manager

set -e

PROJECT_ID="elegant-verbena-480615-a4"

echo "========================================="
echo "Uploading Secrets to Secret Manager"
echo "========================================="
echo ""

# Set project
gcloud config set project $PROJECT_ID

# Function to create or update secret
create_or_update_secret() {
    local secret_name=$1
    local secret_value=$2
    
    echo "Processing secret: $secret_name"
    
    # Check if secret exists
    if gcloud secrets describe $secret_name --project=$PROJECT_ID &>/dev/null; then
        echo "  ✓ Secret exists, adding new version..."
        echo -n "$secret_value" | gcloud secrets versions add $secret_name --data-file=-
    else
        echo "  ✓ Creating new secret..."
        echo -n "$secret_value" | gcloud secrets create $secret_name --data-file=- --replication-policy="automatic"
    fi
    
    echo "  ✓ Done"
    echo ""
}

# Read MongoDB URI from .env file
if [ -f .env ]; then
    echo "Reading secrets from .env file..."
    
    # Extract MongoDB URI
    MONGODB_URI=$(grep "^MONGODB_URI=" .env | cut -d '=' -f2-)
    
    if [ -n "$MONGODB_URI" ]; then
        create_or_update_secret "mongodb-uri" "$MONGODB_URI"
    else
        echo "⚠️  MONGODB_URI not found in .env"
    fi
else
    echo "❌ .env file not found"
    exit 1
fi

echo "========================================="
echo "Configuring IAM Permissions"
echo "========================================="
echo ""

# Get project number
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo "Granting Secret Manager access to service account..."
gcloud secrets add-iam-policy-binding mongodb-uri \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor" \
    --project=$PROJECT_ID

echo ""
echo "========================================="
echo "✅ Secrets uploaded successfully!"
echo "========================================="
echo ""
echo "Secrets created/updated:"
echo "  - mongodb-uri"
echo ""
echo "Next steps:"
echo "  1. Update your application to use Secret Manager"
echo "  2. Remove sensitive values from .env file"
echo "  3. Redeploy your application"
echo ""
