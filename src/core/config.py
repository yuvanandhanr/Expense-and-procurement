"""
Configuration module.

Responsible for loading and validating environment variables for the
Enterprise Expense & Procurement Workflow Platform.
"""

from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings.
    
    Loads configuration parameters from environment variables or a local .env file.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # General App Config
    ENVIRONMENT: Literal["development", "testing", "staging", "production"] = Field(
        default="development",
        description="Deployment environment name"
    )
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level for the application"
    )
    APP_VERSION: str = Field(
        default="1.0.0",
        description="Version of the application"
    )

    # Database & Supabase Credentials
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
        description="Database connection DSN including the asyncpg driver"
    )
    SUPABASE_URL: str = Field(
        default="https://placeholder-project.supabase.co",
        description="Supabase service URL"
    )
    SUPABASE_KEY: str = Field(
        default="placeholder-anon-key",
        description="Supabase API key"
    )
    JWT_SECRET: str = Field(
        default="placeholder-jwt-secret",
        description="JWT secret key for user authentication"
    )

    # AWS Configuration
    AWS_REGION: str = Field(
        default="us-east-1",
        description="Default AWS region"
    )
    AWS_ACCESS_KEY_ID: str = Field(
        default="mock-access-key-id",
        description="AWS access key ID for services like Textract and S3"
    )
    AWS_SECRET_ACCESS_KEY: str = Field(
        default="mock-secret-access-key",
        description="AWS secret access key"
    )
    TEXTRACT_REGION: str = Field(
        default="us-east-1",
        description="AWS Region designated for AWS Textract OCR operations"
    )


# Instantiate settings for global usage
settings = Settings()
