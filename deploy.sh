#!/bin/bash

# Product Catalog AI - Google Cloud Deployment Script
# This script automates the deployment of both backend and frontend to Cloud Run

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="elegant-verbena-480615-a4"
REGION="us-central1"
BACKEND_SERVICE="product-catalog-backend"
FRONTEND_SERVICE="product-catalog-frontend"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Product Catalog AI - Cloud Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set project
echo -e "${YELLOW}Setting GCP project to: $PROJECT_ID${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${YELLOW}Enabling required GCP APIs...${NC}"
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com \
    containerregistry.googleapis.com \
    aiplatform.googleapis.com

echo -e "${GREEN}✓ APIs enabled${NC}"

# Create MongoDB URI secret if it doesn't exist
echo -e "${YELLOW}Setting up Secret Manager...${NC}"
if ! gcloud secrets describe mongodb-uri &> /dev/null; then
    echo "Creating mongodb-uri secret..."
    echo -n "mongodb+srv://productcatalog:9Lj6AQuJ62sKohSt@learningcluster.c92lf.mongodb.net/?appName=LearningCluster" | \
        gcloud secrets create mongodb-uri --data-file=-
    echo -e "${GREEN}✓ Secret created${NC}"
else
    echo -e "${GREEN}✓ Secret already exists${NC}"
fi

# Grant Cloud Run access to secrets
echo -e "${YELLOW}Configuring IAM permissions...${NC}"
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
gcloud secrets add-iam-policy-binding mongodb-uri \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet || true

echo -e "${GREEN}✓ IAM configured${NC}"

# Build and deploy backend
echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Deploying Backend Service${NC}"
echo -e "${YELLOW}========================================${NC}"

gcloud builds submit \
    --config=cloudbuild.yaml \
    --substitutions=COMMIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "manual")

echo -e "${GREEN}✓ Backend deployed${NC}"

# Get backend URL
BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE \
    --region=$REGION \
    --format="value(status.url)")

echo -e "${GREEN}Backend URL: $BACKEND_URL${NC}"

# Update frontend to use backend URL
echo -e "${YELLOW}Updating frontend configuration...${NC}"
sed -i.bak "s|http://localhost:8000|$BACKEND_URL|g" frontend/app.js
echo -e "${GREEN}✓ Frontend configured${NC}"

# Build and deploy frontend
echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Deploying Frontend Service${NC}"
echo -e "${YELLOW}========================================${NC}"

gcloud builds submit \
    --config=cloudbuild-frontend.yaml \
    --substitutions=COMMIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "manual")

echo -e "${GREEN}✓ Frontend deployed${NC}"

# Get frontend URL
FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE \
    --region=$REGION \
    --format="value(status.url)")

# Restore frontend file
mv frontend/app.js.bak frontend/app.js

# Update backend CORS settings
echo -e "${YELLOW}Updating CORS configuration...${NC}"
echo "You may need to update the CORS settings in backend/main.py to allow: $FRONTEND_URL"

# Display deployment summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Backend URL:  ${GREEN}$BACKEND_URL${NC}"
echo -e "Frontend URL: ${GREEN}$FRONTEND_URL${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Update CORS in backend/main.py to allow: $FRONTEND_URL"
echo "2. Redeploy backend if CORS was updated"
echo "3. Test the application at: $FRONTEND_URL"
echo "4. (Optional) Map a custom domain"
echo ""
echo -e "${GREEN}Deployment logs are available in Cloud Console${NC}"
