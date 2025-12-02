#!/usr/bin/env python3
"""
AI Video Analytics Microservice
Запуск сервера с настройками по умолчанию
"""

import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
