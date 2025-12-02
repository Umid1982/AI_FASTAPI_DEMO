from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    app_name: str = "AI Video Analytics Microservice"
    app_version: str = "1.0.0"
    debug: bool = True
    environment: str = "development"
    
    # API Authentication
    api_key: str = "your-secret-api-key-here"
    x_api_key_header: str = "X-API-KEY"
    
    # Database
    database_url: str = "postgresql://username:password@localhost:5432/ai_video_analytics"
    database_echo: bool = False
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # Video Processing
    video_source: str = "file"  # webcam, file, or rtsp
    video_source_path: str = "./videos/test_video.mp4"  # Path to video file
    rtsp_url: Optional[str] = None
    
    # AI Models
    yolo_model: str = "yolov8n.pt"
    confidence_threshold: float = 0.5
    iou_threshold: float = 0.45
    
    # LLM Configuration
    llm_provider: str = "ollama"  # ollama or openai
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-3.5-turbo"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    cors_methods: List[str] = ["GET", "POST", "PUT", "DELETE"]
    cors_headers: List[str] = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
