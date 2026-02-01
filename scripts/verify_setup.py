"""
Quick verification script to check if the environment is properly configured.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_environment():
    """Check if all required environment variables are set."""
    print("🔍 Checking environment configuration...\n")
    
    required_vars = {
        "MONGODB_URI": "MongoDB Atlas connection string",
        "MONGODB_DB_NAME": "MongoDB database name",
        "GOOGLE_CLOUD_PROJECT": "Google Cloud project ID",
        "GOOGLE_APPLICATION_CREDENTIALS": "Path to service account JSON",
        "VERTEX_AI_LOCATION": "VertexAI location"
    }
    
    missing = []
    configured = []
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value and value != f"your-{var.lower().replace('_', '-')}":
            configured.append(f"✅ {var}: {description}")
        else:
            missing.append(f"❌ {var}: {description}")
    
    # Print results
    if configured:
        print("Configured variables:")
        for item in configured:
            print(f"  {item}")
    
    if missing:
        print("\nMissing or not configured:")
        for item in missing:
            print(f"  {item}")
        print("\n⚠️  Please update your .env file with the required credentials.")
        print("   Copy .env.example to .env and fill in your values.")
        return False
    else:
        print("\n✅ All environment variables are configured!")
        return True

def check_dependencies():
    """Check if required Python packages are installed."""
    print("\n🔍 Checking Python dependencies...\n")
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "pymongo",
        "motor",
        "pydantic",
        "google.cloud.aiplatform"
    ]
    
    missing = []
    installed = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            installed.append(f"✅ {package}")
        except ImportError:
            missing.append(f"❌ {package}")
    
    if installed:
        print("Installed packages:")
        for item in installed:
            print(f"  {item}")
    
    if missing:
        print("\nMissing packages:")
        for item in missing:
            print(f"  {item}")
        print("\n⚠️  Please install dependencies:")
        print("   pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All dependencies are installed!")
        return True

def main():
    """Run all checks."""
    print("=" * 60)
    print("Product Catalog - Environment Verification")
    print("=" * 60)
    print()
    
    env_ok = check_environment()
    deps_ok = check_dependencies()
    
    print("\n" + "=" * 60)
    if env_ok and deps_ok:
        print("✅ Environment is ready!")
        print("\nNext steps:")
        print("  1. python scripts/setup_indexes.py")
        print("  2. Create Vector Search index in MongoDB Atlas UI")
        print("  3. python scripts/generate_products.py")
        print("  4. cd backend && uvicorn main:app --reload")
        print("  5. cd frontend && python -m http.server 3000")
    else:
        print("⚠️  Please fix the issues above before proceeding.")
    print("=" * 60)

if __name__ == "__main__":
    main()
