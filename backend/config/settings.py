"""Configuration settings for the application."""
import os
from typing import Optional
from dotenv import load_dotenv
from google.cloud import secretmanager

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings with Secret Manager integration."""
    
    def __init__(self):
        """Initialize settings."""
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "elegant-verbena-480615-a4")
        self.environment = os.getenv("ENVIRONMENT", "development")
        self._secret_client: Optional[secretmanager.SecretManagerServiceClient] = None
        
        # MongoDB settings
        self.MONGODB_URI = self._get_secret_or_env("mongodb-uri", "MONGODB_URI")
        self.MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "productcatalog")
        
        # Google Cloud settings
        self.GOOGLE_CLOUD_PROJECT = self.project_id
        self.VERTEX_AI_LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-central1")
        
        # API settings
        self.API_HOST = os.getenv("API_HOST", "0.0.0.0")
        self.API_PORT = int(os.getenv("API_PORT", "8000"))
        
        # CORS settings
        allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
        self.ALLOWED_ORIGINS = [origin.strip() for origin in allowed_origins.split(",")]
        
        # Logging
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    def _get_secret_client(self) -> secretmanager.SecretManagerServiceClient:
        """Get or create Secret Manager client."""
        if self._secret_client is None:
            self._secret_client = secretmanager.SecretManagerServiceClient()
        return self._secret_client
    
    def _get_secret_or_env(self, secret_name: str, env_var: str) -> str:
        """
        Get value from Secret Manager in production, or from environment variable in development.
        
        Args:
            secret_name: Name of the secret in Secret Manager
            env_var: Environment variable name as fallback
            
        Returns:
            Secret value
        """
        # In development, always use environment variable
        if self.environment == "development":
            value = os.getenv(env_var)
            if value:
                return value
            raise ValueError(f"{env_var} not found in environment. Please set it in your .env file.")
        
        # In production, try Secret Manager first
        try:
            client = self._get_secret_client()
            secret_path = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
            response = client.access_secret_version(request={"name": secret_path})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            # Fallback to environment variable
            value = os.getenv(env_var)
            if value:
                return value
            raise ValueError(f"Could not retrieve {secret_name} from Secret Manager or environment: {e}")


# Global settings instance
settings = Settings()
