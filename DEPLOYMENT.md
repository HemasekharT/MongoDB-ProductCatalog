# Product Catalog AI - Deployment Guide

## Quick Deploy to Google Cloud Run

This guide will help you deploy the Product Catalog AI to Google Cloud Platform.

## Prerequisites

1. **Google Cloud Account** with billing enabled
2. **gcloud CLI** installed and authenticated
3. **Docker** installed (optional, Cloud Build handles this)
4. **Git** initialized in project (optional)

## Deployment Steps

### Option 1: Automated Deployment (Recommended)

Run the automated deployment script:

```bash
./deploy.sh
```

This script will:
- Enable required GCP APIs
- Create secrets in Secret Manager
- Build and deploy backend to Cloud Run
- Build and deploy frontend to Cloud Run
- Configure IAM permissions
- Display deployment URLs

### Option 2: Manual Deployment

#### Step 1: Set Up GCP Project

```bash
# Set your project ID
export PROJECT_ID="elegant-verbena-480615-a4"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com \
    containerregistry.googleapis.com \
    aiplatform.googleapis.com
```

#### Step 2: Create Secrets

```bash
# Create MongoDB URI secret
echo -n "YOUR_MONGODB_URI" | gcloud secrets create mongodb-uri --data-file=-

# Grant Cloud Run access to secrets
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
gcloud secrets add-iam-policy-binding mongodb-uri \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

#### Step 3: Deploy Backend

```bash
# Build and deploy using Cloud Build
gcloud builds submit --config=cloudbuild.yaml

# Or deploy directly
gcloud run deploy product-catalog-backend \
    --source . \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --max-instances 10 \
    --set-env-vars MONGODB_DB_NAME=productcatalog,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,VERTEX_AI_LOCATION=us-central1 \
    --set-secrets MONGODB_URI=mongodb-uri:latest
```

#### Step 4: Update Frontend Configuration

```bash
# Get backend URL
BACKEND_URL=$(gcloud run services describe product-catalog-backend \
    --region=us-central1 \
    --format="value(status.url)")

# Update frontend/app.js
sed -i "s|http://localhost:8000|$BACKEND_URL|g" frontend/app.js
```

#### Step 5: Deploy Frontend

```bash
# Build and deploy frontend
gcloud builds submit --config=cloudbuild-frontend.yaml

# Or deploy directly
gcloud run deploy product-catalog-frontend \
    --source . \
    --dockerfile Dockerfile.frontend \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --max-instances 5
```

#### Step 6: Update CORS (Important!)

After deployment, update `backend/main.py` to allow your frontend URL:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-url.run.app"],  # Update this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Then redeploy the backend:

```bash
gcloud builds submit --config=cloudbuild.yaml
```

## Post-Deployment

### Get Service URLs

```bash
# Backend URL
gcloud run services describe product-catalog-backend \
    --region=us-central1 \
    --format="value(status.url)"

# Frontend URL
gcloud run services describe product-catalog-frontend \
    --region=us-central1 \
    --format="value(status.url)"
```

### Test the Deployment

```bash
# Test backend health
curl https://YOUR-BACKEND-URL.run.app/

# Test frontend
open https://YOUR-FRONTEND-URL.run.app/
```

### View Logs

```bash
# Backend logs
gcloud run services logs read product-catalog-backend \
    --region=us-central1 \
    --limit=50

# Frontend logs
gcloud run services logs read product-catalog-frontend \
    --region=us-central1 \
    --limit=50
```

## Custom Domain (Optional)

### Map Custom Domain

```bash
# Map domain to frontend
gcloud run domain-mappings create \
    --service=product-catalog-frontend \
    --domain=your-domain.com \
    --region=us-central1

# Map subdomain to backend
gcloud run domain-mappings create \
    --service=product-catalog-backend \
    --domain=api.your-domain.com \
    --region=us-central1
```

### Update DNS Records

Add the DNS records shown in the domain mapping output to your domain provider.

## Monitoring & Debugging

### Cloud Console

- **Cloud Run**: https://console.cloud.google.com/run
- **Cloud Build**: https://console.cloud.google.com/cloud-build
- **Logs**: https://console.cloud.google.com/logs
- **Secret Manager**: https://console.cloud.google.com/security/secret-manager

### Common Issues

**Issue**: Backend returns 500 errors
- Check logs: `gcloud run services logs read product-catalog-backend`
- Verify secrets are accessible
- Check VertexAI permissions

**Issue**: Frontend can't connect to backend
- Verify CORS settings in `backend/main.py`
- Check backend URL in frontend
- Verify backend is deployed and healthy

**Issue**: Authentication errors
- Verify service account has VertexAI permissions
- Check Secret Manager IAM bindings
- Ensure MongoDB URI is correct

## Cost Management

### Monitor Costs

```bash
# View current month costs
gcloud billing accounts list
```

### Set Budget Alerts

1. Go to Cloud Console → Billing → Budgets & alerts
2. Create budget with email notifications
3. Set threshold at $50/month for development

### Optimize Costs

- Set `--min-instances=0` to scale to zero
- Use `--max-instances` to cap costs
- Monitor request counts and adjust resources
- Consider MongoDB Atlas free tier for development

## Rollback

### Rollback to Previous Revision

```bash
# List revisions
gcloud run revisions list --service=product-catalog-backend

# Rollback to specific revision
gcloud run services update-traffic product-catalog-backend \
    --to-revisions=REVISION_NAME=100
```

## Cleanup

### Delete Services

```bash
# Delete backend
gcloud run services delete product-catalog-backend --region=us-central1

# Delete frontend
gcloud run services delete product-catalog-frontend --region=us-central1

# Delete secrets
gcloud secrets delete mongodb-uri

# Delete container images
gcloud container images delete gcr.io/$PROJECT_ID/product-catalog-backend
gcloud container images delete gcr.io/$PROJECT_ID/product-catalog-frontend
```

## Security Best Practices

1. **Never commit secrets** - Use Secret Manager
2. **Restrict CORS** - Only allow your domain
3. **Enable authentication** - For production, consider Cloud IAP
4. **Rotate credentials** - Regularly update MongoDB and service account keys
5. **Monitor logs** - Set up alerts for errors and unusual activity
6. **Use VPC** - For production, consider VPC connector for MongoDB
7. **Enable Cloud Armor** - For DDoS protection

## Support

For issues or questions:
- Check Cloud Run logs
- Review deployment plan
- Consult GCP documentation
- Check MongoDB Atlas connection
