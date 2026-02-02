#!/bin/bash
# GitHub Actions Setup Helper Script

set -e

echo "========================================="
echo "GitHub Actions CI/CD Setup"
echo "========================================="
echo ""

# Check if key exists
if [ ! -f "github-actions-key.json" ]; then
    echo "❌ github-actions-key.json not found!"
    echo "Run this command first:"
    echo "  gcloud iam service-accounts keys create github-actions-key.json \\"
    echo "    --iam-account=933628467892-compute@developer.gserviceaccount.com"
    exit 1
fi

echo "✅ Service account key found"
echo ""

echo "========================================="
echo "Step 1: Copy Service Account Key"
echo "========================================="
echo ""
echo "The service account key is ready. You'll need to add it to GitHub."
echo ""
echo "📋 To copy the key to clipboard (macOS):"
echo "  cat github-actions-key.json | pbcopy"
echo ""
echo "Or view it:"
echo "  cat github-actions-key.json"
echo ""

echo "========================================="
echo "Step 2: Add Secret to GitHub"
echo "========================================="
echo ""
echo "1. Go to your GitHub repository"
echo "2. Click: Settings → Secrets and variables → Actions"
echo "3. Click: New repository secret"
echo "4. Name: GCP_SA_KEY"
echo "5. Value: Paste the entire JSON key"
echo "6. Click: Add secret"
echo ""

echo "========================================="
echo "Step 3: Push Workflows to GitHub"
echo "========================================="
echo ""
echo "Run these commands:"
echo "  git add .github/workflows/"
echo "  git add .gitignore"
echo "  git commit -m 'Add GitHub Actions CI/CD workflows'"
echo "  git push origin main"
echo ""

echo "========================================="
echo "Step 4: Monitor Deployment"
echo "========================================="
echo ""
echo "1. Go to your GitHub repository"
echo "2. Click the 'Actions' tab"
echo "3. Watch the deployment progress"
echo ""

echo "========================================="
echo "🎉 Setup Complete!"
echo "========================================="
echo ""
echo "After pushing to GitHub, your app will automatically deploy on every push to main!"
echo ""
