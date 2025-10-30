# AI Video Analytics Microservice

Профессиональный микросервис для анализа видео в реальном времени с использованием ИИ, построенный на FastAPI с соблюдением принципов SOLID и лучших практик.

## 🚀 Возможности

- **Детекция людей** - YOLOv8 для обнаружения объектов
- **Трекинг объектов** - DeepSORT для отслеживания движения
- **Аналитика в реальном времени** - подсчет людей, время нахождения, пиковые часы
- **Тепловые карты** - визуализация активности
- **AI отчеты** - генерация отчетов через Ollama/OpenAI
- **RESTful API** - полный набор endpoints
- **База данных** - PostgreSQL для хранения данных
- **Аутентификация** - API ключи для безопасности
- **Мониторинг** - Prometheus метрики (`/metrics`)
- **Кэширование** - Redis для оптимизации производительности
- **Health Check** - проверка состояния БД и сервиса

## 🏗️ Архитектура

Проект построен по принципам SOLID с использованием:

- **Dependency Injection** - FastAPI Depends
- **Repository Pattern** - для работы с данными
- **Strategy Pattern** - для различных алгоритмов
- **Factory Pattern** - для создания сервисов
- **Service Layer** - бизнес-логика в сервисах
- **Middleware** - аутентификация, CORS, логирование

## 📁 Структура проекта

```
ai_fastapi_demo/
├── app/
│   ├── core/
│   │   ├── config.py          # Конфигурация
│   │   ├── middleware.py      # Middleware
│   │   ├── metrics.py         # Prometheus метрики
│   │   └── redis_cache.py    # Redis кэш
│   ├── database/
│   │   ├── connection.py      # Подключение к БД
│   │   └── models.py          # SQLAlchemy модели
│   ├── models/
│   │   └── schemas.py         # Pydantic модели
│   ├── repositories/
│   │   ├── base_repository.py
│   │   ├── video_session_repository.py
│   │   └── detection_repository.py
│   ├── routes/
│   │   ├── video.py          # API endpoints для видео
│   │   └── reports.py        # API endpoints для отчетов
│   ├── services/
│   │   ├── video_service.py   # Обработка видео
│   │   ├── detection_service.py # Детекция объектов
│   │   ├── tracking_service.py  # Трекинг объектов
│   │   ├── llm_service.py     # LLM интеграция
│   │   └── analytics_service.py # Аналитика
│   └── utils/
│       ├── http_client.py     # HTTP клиенты
│       └── response_helper.py # Response helpers
├── main.py                    # Точка входа
├── requirements.txt           # Зависимости
└── README.md
```

## 🛠️ Установка

### 1. Клонирование и установка зависимостей

```bash
# Клонировать проект
git clone <repository-url>
cd ai_fastapi_demo

# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установить зависимости
pip install -r requirements.txt
```

### 2. Настройка базы данных

```bash
# Установить PostgreSQL
# Создать базу данных
createdb ai_video_analytics

# Настроить подключение в .env файле
DATABASE_URL=postgresql://username:password@localhost:5432/ai_video_analytics
```

### 3. Настройка конфигурации

Создайте `.env` файл:

```env
# Application
APP_NAME=AI Video Analytics Microservice
APP_VERSION=1.0.0
DEBUG=True
ENVIRONMENT=development

# API Authentication
API_KEY=your-secret-api-key-here
X_API_KEY_HEADER=X-API-KEY

# Database
DATABASE_URL=postgresql://username:password@localhost:5432/ai_video_analytics
DATABASE_ECHO=False

# Video Processing
VIDEO_SOURCE=0  # 0 for webcam, or path to video file
RTSP_URL=rtsp://username:password@ip:port/stream

# AI Models
YOLO_MODEL=yolov8n.pt
CONFIDENCE_THRESHOLD=0.5
IOU_THRESHOLD=0.45

# LLM Configuration
LLM_PROVIDER=ollama  # ollama or openai
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
OPENAI_API_KEY=your-openai-key-here
OPENAI_MODEL=gpt-3.5-turbo

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
CORS_METHODS=["GET", "POST", "PUT", "DELETE"]
CORS_HEADERS=["*"]

# Redis (опционально - для кэширования)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### 4. Настройка Redis (опционально)

```bash
# Установить Redis
# macOS
brew install redis

# Ubuntu/Debian
sudo apt-get install redis-server

# Запустить Redis
redis-server
```

### 5. Настройка Ollama (опционально)

```bash
# Установить Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Запустить Ollama
ollama serve

# Скачать модель
ollama pull llama3
```

## 🚀 Запуск

```bash
# Запуск сервера
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Или через Python
python main.py
```

Сервер будет доступен по адресу: http://localhost:8000

## 📚 API Документация

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔑 Аутентификация

Все API endpoints (кроме `/`, `/health`, `/docs`) требуют API ключ в заголовке:

```
X-API-KEY: your-secret-api-key-here
```

## 📡 API Endpoints

### Видео анализ

- `POST /api/v1/video/analyze` - Запустить анализ видео
- `GET /api/v1/video/analyze/{session_id}` - Статус анализа
- `GET /api/v1/video/sessions` - Список сессий
- `DELETE /api/v1/video/sessions/{session_id}` - Удалить сессию

### Отчеты

- `POST /api/v1/reports/generate` - Сгенерировать отчет
- `GET /api/v1/reports/sessions/{session_id}/analytics` - Аналитика сессии
- `GET /api/v1/reports/sessions/{session_id}/heatmap` - Тепловая карта
- `GET /api/v1/reports/sessions/{session_id}/detection-stats` - Статистика детекции
- `GET /api/v1/reports/sessions/{session_id}/summary` - Краткое резюме

### Система

- `GET /` - Информация о сервисе
- `GET /health` - Проверка здоровья (с проверкой БД)
- `GET /info` - Подробная информация
- `GET /metrics` - Prometheus метрики (для мониторинга)

## 💡 Примеры использования

### 1. Запуск анализа видео

```bash
curl -X POST "http://localhost:8000/api/v1/video/analyze" \
  -H "X-API-KEY: your-secret-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "webcam",
    "duration": 60,
    "confidence_threshold": 0.5
  }'
```

### 2. Получение статуса анализа

```bash
curl -X GET "http://localhost:8000/api/v1/video/analyze/{session_id}" \
  -H "X-API-KEY: your-secret-api-key-here"
```

### 3. Генерация отчета

```bash
curl -X POST "http://localhost:8000/api/v1/reports/generate" \
  -H "X-API-KEY: your-secret-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session-uuid",
    "report_type": "summary",
    "include_heatmap": true
  }'
```

## 🔧 Разработка

### Структура кода

- **Сервисы** - бизнес-логика, инжектируются через DI
- **Репозитории** - работа с данными, наследуются от BaseRepository
- **Модели** - Pydantic схемы для валидации
- **Middleware** - аутентификация, CORS, логирование
- **Utils** - вспомогательные функции

### Добавление новых функций

1. Создайте сервис в `app/services/`
2. Добавьте репозиторий в `app/repositories/` если нужно
3. Создайте Pydantic модели в `app/models/schemas.py`
4. Добавьте endpoints в `app/routes/`
5. Обновите dependency injection

## 🐛 Отладка

### Миграции и пересоздание таблиц

```bash
# Создать таблицы
python3 init_db.py

# Пересоздать таблицы (удалить и создать заново)
python3 -c "
from app.database.connection import engine
from app.database.models import Base
print('Удаляем старые таблицы...')
Base.metadata.drop_all(bind=engine)
print('Создаем новые таблицы...')
Base.metadata.create_all(bind=engine)
print('Готово!')
"
```

## 📈 Мониторинг

### Health Check

```bash
# Проверка состояния сервиса и БД
curl http://localhost:8000/health
```

Возвращает:
- `status` - общее состояние сервиса
- `database` - статус подключения к БД
- `timestamp` - время проверки

### Prometheus Метрики

```bash
# Получить метрики
curl http://localhost:8000/metrics
```

Доступные метрики:
- `http_requests_total` - количество HTTP запросов
- `http_request_duration_seconds` - время выполнения запросов
- `video_analysis_total` - количество анализов видео
- `frames_processed_total` - количество обработанных кадров
- `detections_total` - количество детекций

### Интеграция с Grafana

1. Настройте Prometheus для сбора метрик
2. Добавьте Prometheus как data source в Grafana
3. Создайте дашборды для визуализации

### Логи

Логи настраиваются через structlog и выводятся в JSON формате:

```bash
# Просмотр логов
tail -f logs/app.log

# Фильтрация по уровню
grep "ERROR" logs/app.log
```

### База данных

```bash
# Подключение к БД
psql ai_video_analytics

# Просмотр таблиц
\dt

# Просмотр данных
SELECT * FROM video_sessions LIMIT 10;
```

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature branch
3. Сделайте изменения
4. Добавьте тесты
5. Создайте Pull Request

## 📄 Лицензия

MIT License

## 🆘 Поддержка

При возникновении проблем:

1. Проверьте логи
2. Убедитесь в правильности конфигурации
3. Проверьте подключение к базе данных
4. Создайте issue в репозитории

---

**Создано с  для демонстрации профессиональной разработки на Python/FastAPI**
