#!/usr/bin/env python3
"""
Инициализация базы данных
Создание таблиц и начальных данных
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import create_tables, engine
from app.core.config import settings
import structlog

logger = structlog.get_logger()

def init_database():
    """Инициализация базы данных."""
    try:
        print("🚀 Инициализация базы данных...")
        print(f"📊 Подключение к: {settings.database_url}")
        
        # Создать таблицы
        create_tables()
        
        print("✅ Таблицы созданы успешно!")
        print("📋 Созданные таблицы:")
        print("   - video_sessions")
        print("   - detections") 
        print("   - tracked_objects")
        print("   - heatmap_points")
        print("   - reports")
        
        print("\n🎉 База данных готова к использованию!")
        
    except Exception as e:
        print(f"❌ Ошибка при создании таблиц: {e}")
        print("\n🔧 Проверьте:")
        print("   1. PostgreSQL запущен")
        print("   2. База данных 'ai_video_analytics' создана")
        print("   3. Правильные данные в .env файле")
        sys.exit(1)

if __name__ == "__main__":
    init_database()
