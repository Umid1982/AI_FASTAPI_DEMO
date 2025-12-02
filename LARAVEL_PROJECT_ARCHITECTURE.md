# 🚀 Laravel Backend - Архитектура Проекта

## 📋 Общая Концепция

**Laravel Backend** = Бизнес-логика, пользователи, авторизация, управление
**FastAPI Microservice** = AI обработка видео, детекция, трекинг

---

## 🏗️ Архитектура Системы

```
┌─────────────────────────────────────────────────────────────┐
│                    Клиент (Frontend/API)                    │
│                  Laravel Backend API                        │
└────────────────────────┬──────────────────────────────────┘
                         │
                         ├───► PostgreSQL (Business Data)
                         ├───► Redis (Cache/Queue)
                         ├───► WebSockets (Real-time)
                         │
                         └───► HTTP API Calls
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Microservice (Python)                   │
│  POST   /api/v1/video/analyze                               │
│  GET    /api/v1/video/analyze/{session_id}                  │
│  POST   /api/v1/reports/generate                            │
│  GET    /api/v1/reports/sessions/{session_id}/analytics      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Ключевые Компоненты Laravel Проекта
# 🚀 Laravel Backend - Архитектура Проекта

## 📋 Общая Концепция

**Laravel Backend** = Бизнес-логика, пользователи, авторизация, управление
**FastAPI Microservice** = AI обработка видео, детекция, трекинг

---

## 🏗️ Архитектура Системы

```
┌─────────────────────────────────────────────────────────────┐
│                    Клиент (Frontend/API)                    │
│                  Laravel Backend API                        │
└────────────────────────┬──────────────────────────────────┘
                         │
                         ├───► PostgreSQL (Business Data)
                         ├───► Redis (Cache/Queue)
                         ├───► WebSockets (Real-time)
                         │
                         └───► HTTP API Calls
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Microservice (Python)                   │
│  POST   /api/v1/video/analyze                               │
│  GET    /api/v1/video/analyze/{session_id}                  │
│  POST   /api/v1/reports/generate                            │
│  GET    /api/v1/reports/sessions/{session_id}/analytics      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Ключевые Компоненты Laravel Проекта

### 1. **API Endpoints (Laravel)**

#### Авторизация
- `POST /api/auth/register` - Регистрация
- `POST /api/auth/login` - Вход
- `POST /api/auth/logout` - Выход
- `GET /api/auth/me` - Текущий пользователь

#### Управление Видео Сессиями
- `GET /api/sessions` - Список сессий пользователя
- `POST /api/sessions` - Создать новую сессию
- `GET /api/sessions/{id}` - Детали сессии
- `DELETE /api/sessions/{id}` - Удалить сессию
- `POST /api/sessions/{id}/start-analysis` - Запустить анализ (вызывает FastAPI)
- `GET /api/sessions/{id}/status` - Статус анализа

#### Отчеты и Аналитика
- `GET /api/reports` - Список отчетов
- `POST /api/reports/generate` - Создать отчет
- `GET /api/reports/{id}` - Детали отчета
- `GET /api/reports/{id}/analytics` - Получить аналитику
- `GET /api/reports/{id}/heatmap` - Получить heatmap

#### Настройки и Уведомления
- `GET /api/settings` - Получить настройки
- `PUT /api/settings` - Обновить настройки
- `POST /api/notifications/telegram/connect` - Подключить Telegram
- `GET /api/notifications` - История уведомлений

#### WebSockets (Real-time)
- `ws://localhost:6001/live` - WebSocket соединение
- События: `analysis.started`, `analysis.progress`, `analysis.completed`

---

### 2. **Модели (Models)**

```php
// app/Models/User.php - Расширенная модель пользователя
// app/Models/VideoSession.php - Видео сессии
// app/Models/AnalysisReport.php - Отчеты анализа
// app/Models/Detection.php - Детекции
// app/Models/HeatmapPoint.php - Точки heatmap
// app/Models/Notification.php - Уведомления
// app/Models/Settings.php - Настройки
```

---

### 3. **Контроллеры (Controllers)**

```
app/Http/Controllers/
├── AuthController.php           # Авторизация
├── SessionController.php        # Управление сессиями
├── ReportController.php         # Отчеты
├── AnalysisController.php       # Анализ видео
├── NotificationController.php   # Уведомления
├── WebSocketController.php     # WebSocket
└── SettingsController.php      # Настройки
```

---

### 4. **Сервисы (Services)**

```
app/Services/
├── VideoAnalysisService.php    # Интеграция с FastAPI
├── ReportGenerationService.php # Генерация отчетов
├── NotificationService.php     # Telegram уведомления
├── CacheService.php            # Redis кэширование
└── WebSocketService.php        # WebSocket события
```

---

### 5. **Jobs (Очереди)**

```
app/Jobs/
├── ProcessVideoAnalysis.php    # Обработка видео в фоне
├── GenerateReport.php          # Генерация отчета
└── SendNotification.php        # Отправка уведомлений
```

---

### 6. **Events & Listeners**

```
app/Events/
├── AnalysisStarted.php
├── AnalysisCompleted.php
└── AnalysisFailed.php

app/Listeners/
├── SendTelegramNotification.php
├── BroadcastWebSocketEvent.php
└── UpdateCache.php
```

---

### 7. **Middleware**

```
app/Http/Middleware/
├── Authenticate.php
├── RateLimiting.php
└── ApiKeyValidation.php
```

---

### 8. **Интеграция с FastAPI**

#### Service Class для FastAPI

```php
// app/Services/FastApiClient.php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class FastApiClient
{
    private string $baseUrl;
    private string $apiKey;
    
    public function __construct()
    {
        $this->baseUrl = config('services.fastapi.base_url');
        $this->apiKey = config('services.fastapi.api_key');
    }
    
    /**
     * Начать анализ видео
     */
    public function startAnalysis(array $data): array
    {
        $response = Http::withHeaders([
            'X-API-KEY' => $this->apiKey,
        ])->post("{$this->baseUrl}/api/v1/video/analyze", [
            'source_type' => $data['source_type'],
            'source_path' => $data['source_path'],
            'duration' => $data['duration'] ?? null,
            'confidence_threshold' => $data['confidence_threshold'] ?? 0.5,
        ]);
        
        if ($response->successful()) {
            return $response->json();
        }
        
        throw new \Exception('Failed to start analysis: ' . $response->body());
    }
    
    /**
     * Получить статус анализа
     */
    public function getAnalysisStatus(string $sessionId): array
    {
        $response = Http::withHeaders([
            'X-API-KEY' => $this->apiKey,
        ])->get("{$this->baseUrl}/api/v1/video/analyze/{$sessionId}");
        
        return $response->json();
    }
    
    /**
     * Получить аналитику
     */
    public function getAnalytics(string $sessionId): array
    {
        $response = Http::withHeaders([
            'X-API-KEY' => $this->apiKey,
        ])->get("{$this->baseUrl}/api/v1/reports/sessions/{$sessionId}/analytics");
        
        return $response->json();
    }
    
    /**
     * Получить heatmap
     */
    public function getHeatmap(string $sessionId, int $width = 100, int $height = 100): array
    {
        $response = Http::withHeaders([
            'X-API-KEY' => $this->apiKey,
        ])->get(
            "{$this->baseUrl}/api/v1/reports/sessions/{$sessionId}/heatmap",
            ['width' => $width, 'height' => $height]
        );
        
        return $response->json();
    }
    
    /**
     * Сгенерировать отчет
     */
    public function generateReport(string $sessionId, string $reportType = 'summary'): array
    {
        $response = Http::withHeaders([
            'X-API-KEY' => $this->apiKey,
        ])->post("{$this->baseUrl}/api/v1/reports/generate", [
            'session_id' => $sessionId,
            'report_type' => $reportType,
            'include_heatmap' => true,
            'include_timeline' => true,
        ]);
        
        return $response->json();
    }
}
```

---

### 9. **Миграции Базы Данных**

```php
// database/migrations/xxxx_create_video_sessions_table.php
// database/migrations/xxxx_create_analysis_reports_table.php
// database/migrations/xxxx_create_detections_table.php
// database/migrations/xxxx_create_notifications_table.php
// database/migrations/xxxx_create_settings_table.php
```

---

### 10. **Telegram Интеграция**

```php
// app/Services/TelegramService.php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class TelegramService
{
    private string $botToken;
    private string $chatId;
    
    public function __construct()
    {
        $this->botToken = config('services.telegram.bot_token');
        $this->chatId = config('services.telegram.chat_id');
    }
    
    public function sendMessage(string $message): bool
    {
        try {
            $response = Http::post("https://api.telegram.org/bot{$this->botToken}/sendMessage", [
                'chat_id' => $this->chatId,
                'text' => $message,
                'parse_mode' => 'HTML',
            ]);
            
            return $response->successful();
        } catch (\Exception $e) {
            Log::error('Failed to send Telegram message', ['error' => $e->getMessage()]);
            return false;
        }
    }
    
    public function sendAnalysisNotification(string $sessionId, string $status): bool
    {
        $message = "🔍 <b>Видео Анализ</b>\n\n";
        $message .= "Сессия: {$sessionId}\n";
        $message .= "Статус: {$status}\n";
        $message .= "Время: " . now()->format('Y-m-d H:i:s');
        
        return $this->sendMessage($message);
    }
}
```

---

### 11. **WebSocket Сервер**

```php
// config/broadcasting.php - Настройка Laravel WebSockets
// Использовать: pusher/pusher-js или soketi
```

---

### 12. **Конфигурация (.env)**

```env
# Laravel Settings
APP_NAME="AI Video Analytics Backend"
APP_ENV=production
APP_KEY=
APP_DEBUG=false

# Database
DB_CONNECTION=postgresql
DB_HOST=127.0.0.1
DB_PORT=5432
DB_DATABASE=video_analytics
DB_USERNAME=username
DB_PASSWORD=password

# Redis
REDIS_HOST=127.0.0.1
REDIS_PASSWORD=null
REDIS_PORT=6379

# FastAPI Integration
FASTAPI_BASE_URL=http://localhost:8080
FASTAPI_API_KEY=my-super-secret-key-123

# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# WebSockets (Pusher)
PUSHER_APP_ID=your-app-id
PUSHER_APP_KEY=your-app-key
PUSHER_APP_SECRET=your-app-secret
PUSHER_APP_CLUSTER=mt1
```

---

### 13. **Тестирование API**

```bash
# Регистрация
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"User","email":"user@example.com","password":"password"}'

# Вход
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'

# Создать сессию
curl -X POST http://localhost:8000/api/sessions \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Session","video_path":"test.mp4"}'

# Запустить анализ
curl -X POST http://localhost:8000/api/sessions/{id}/start-analysis \
  -H "Authorization: Bearer {token}"
```

---

### 14. **Структура Проекта**

```
video-analytics-backend/
├── app/
│   ├── Http/
│   │   ├── Controllers/
│   │   ├── Middleware/
│   │   └── Requests/
│   ├── Models/
│   ├── Services/
│   ├── Jobs/
│   ├── Events/
│   └── Listeners/
│   └── Broadcast/
├── config/
├── database/
│   ├── migrations/
│   └── seeders/
├── resources/
│   └── js/
│       └── websockets.js
├── routes/
│   ├── api.php
│   └── web.php
├── tests/
├── .env.example
└── composer.json
```

---

## 🎯 План Реализации

### Этап 1: Базовая Структура (Day 1)
1. Создать Laravel проект
2. Настроить PostgreSQL
3. Создать модели (User, VideoSession, Report)
4. Настроить авторизацию (Laravel Sanctum)

### Этап 2: Интеграция с FastAPI (Day 2)
1. Создать FastApiClient service
2. Создать контроллеры для видео
3. Интегрировать с API
4. Настроить очереди для фоновой обработки

### Этап 3: Отчеты и Аналитика (Day 3)
1. Создать ReportController
2. Интегрировать с аналитикой FastAPI
3. Настроить кэширование
4. Добавить экспорт отчетов

### Этап 4: Telegram & WebSockets (Day 4)
1. Интегрировать Telegram
2. Настроить WebSockets
3. Добавить real-time обновления
4. Создать дашборды

### Этап 5: Production (Day 5)
1. Тестирование
2. Оптимизация
3. Документация API
4. Деплой

---

## 📊 Технологический Стек

- **Backend**: Laravel 11
- **Database**: PostgreSQL
- **Cache**: Redis
- **Queue**: Redis/Database
- **WebSockets**: Laravel WebSockets (Soketi)
- **Auth**: Laravel Sanctum
- **Microservice**: FastAPI (Python)
- **Notifications**: Telegram Bot API

---

## ✅ Checklist для Реализации

- [ ] Laravel проект создан
- [ ] PostgreSQL настроен
- [ ] Авторизация (Sanctum) работает
- [ ] FastAPI интеграция работает
- [ ] API endpoints реализованы
- [ ] Очереди настроены
- [ ] Redis кэширование работает
- [ ] Telegram уведомления работают
- [ ] WebSockets работают
- [ ] Тесты написаны
- [ ] Документация готова

---

**Команда для создания проекта:**
```bash
composer create-project laravel/laravel video-analytics-backend
cd video-analytics-backend
php artisan install:api
```


### 1. **API Endpoints (Laravel)**

#### Авторизация
- `POST /api/auth/register` - Регистрация
- `POST /api/auth/login` - Вход
- `POST /api/auth/logout` - Выход
- `GET /api/auth/me` - Текущий пользователь

#### Управление Видео Сессиями
- `GET /api/sessions` - Список сессий пользователя
- `POST /api/sessions` - Создать новую сессию
- `GET /api/sessions/{id}` - Детали сессии
- `DELETE /api/sessions/{id}` - Удалить сессию
- `POST /api/sessions/{id}/start-analysis` - Запустить анализ (вызывает FastAPI)
- `GET /api/sessions/{id}/status` - Статус анализа

#### Отчеты и Аналитика
- `GET /api/reports` - Список отчетов
- `POST /api/reports/generate` - Создать отчет
- `GET /api/reports/{id}` - Детали отчета
- `GET /api/reports/{id}/analytics` - Получить аналитику
- `GET /api/reports/{id}/heatmap` - Получить heatmap

#### Настройки и Уведомления
- `GET /api/settings` - Получить настройки
- `PUT /api/settings` - Обновить настройки
- `POST /api/notifications/telegram/connect` - Подключить Telegram
- `GET /api/notifications` - История уведомлений

#### WebSockets (Real-time)
- `ws://localhost:6001/live` - WebSocket соединение
- События: `analysis.started`, `analysis.progress`, `analysis.completed`

---

### 2. **Модели (Models)**

```php
// app/Models/User.php - Расширенная модель пользователя
// app/Models/VideoSession.php - Видео сессии
// app/Models/AnalysisReport.php - Отчеты анализа
// app/Models/Detection.php - Детекции
// app/Models/HeatmapPoint.php - Точки heatmap
// app/Models/Notification.php - Уведомления
// app/Models/Settings.php - Настройки
```

---

### 3. **Контроллеры (Controllers)**

```
app/Http/Controllers/
├── AuthController.php           # Авторизация
├── SessionController.php        # Управление сессиями
├── ReportController.php         # Отчеты
├── AnalysisController.php       # Анализ видео
├── NotificationController.php   # Уведомления
├── WebSocketController.php     # WebSocket
└── SettingsController.php      # Настройки
```

---

### 4. **Сервисы (Services)**

```
app/Services/
├── VideoAnalysisService.php    # Интеграция с FastAPI
├── ReportGenerationService.php # Генерация отчетов
├── NotificationService.php     # Telegram уведомления
├── CacheService.php            # Redis кэширование
└── WebSocketService.php        # WebSocket события
```

---

### 5. **Jobs (Очереди)**

```
app/Jobs/
├── ProcessVideoAnalysis.php    # Обработка видео в фоне
├── GenerateReport.php          # Генерация отчета
└── SendNotification.php        # Отправка уведомлений
```

---

### 6. **Events & Listeners**

```
app/Events/
├── AnalysisStarted.php
├── AnalysisCompleted.php
└── AnalysisFailed.php

app/Listeners/
├── SendTelegramNotification.php
├── BroadcastWebSocketEvent.php
└── UpdateCache.php
```

---

### 7. **Middleware**

```
app/Http/Middleware/
├── Authenticate.php
├── RateLimiting.php
└── ApiKeyValidation.php
```

---

### 8. **Интеграция с FastAPI**

#### Service Class для FastAPI

```php
// app/Services/FastApiClient.php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class FastApiClient
{
    private string $baseUrl;
    private string $apiKey;
    
    public function __construct()
    {
        $this->baseUrl = config('services.fastapi.base_url');
        $this->apiKey = config('services.fastapi.api_key');
    }
    
    /**
     * Начать анализ видео
     */
    public function startAnalysis(array $data): array
    {
        $response = Http::withHeaders([
            'X-API-KEY' => $this->apiKey,
        ])->post("{$this->baseUrl}/api/v1/video/analyze", [
            'source_type' => $data['source_type'],
            'source_path' => $data['source_path'],
            'duration' => $data['duration'] ?? null,
            'confidence_threshold' => $data['confidence_threshold'] ?? 0.5,
        ]);
        
        if ($response->successful()) {
            return $response->json();
        }
        
        throw new \Exception('Failed to start analysis: ' . $response->body());
    }
    
    /**
     * Получить статус анализа
     */
    public function getAnalysisStatus(string $sessionId): array
    {
        $response = Http::withHeaders([
            'X-API-KEY' => $this->apiKey,
        ])->get("{$this->baseUrl}/api/v1/video/analyze/{$sessionId}");
        
        return $response->json();
    }
    
    /**
     * Получить аналитику
     */
    public function getAnalytics(string $sessionId): array
    {
        $response = Http::withHeaders([
            'X-API-KEY' => $this->apiKey,
        ])->get("{$this->baseUrl}/api/v1/reports/sessions/{$sessionId}/analytics");
        
        return $response->json();
    }
    
    /**
     * Получить heatmap
     */
    public function getHeatmap(string $sessionId, int $width = 100, int $height = 100): array
    {
        $response = Http::withHeaders([
            'X-API-KEY' => $this->apiKey,
        ])->get(
            "{$this->baseUrl}/api/v1/reports/sessions/{$sessionId}/heatmap",
            ['width' => $width, 'height' => $height]
        );
        
        return $response->json();
    }
    
    /**
     * Сгенерировать отчет
     */
    public function generateReport(string $sessionId, string $reportType = 'summary'): array
    {
        $response = Http::withHeaders([
            'X-API-KEY' => $this->apiKey,
        ])->post("{$this->baseUrl}/api/v1/reports/generate", [
            'session_id' => $sessionId,
            'report_type' => $reportType,
            'include_heatmap' => true,
            'include_timeline' => true,
        ]);
        
        return $response->json();
    }
}
```

---

### 9. **Миграции Базы Данных**

```php
// database/migrations/xxxx_create_video_sessions_table.php
// database/migrations/xxxx_create_analysis_reports_table.php
// database/migrations/xxxx_create_detections_table.php
// database/migrations/xxxx_create_notifications_table.php
// database/migrations/xxxx_create_settings_table.php
```

---

### 10. **Telegram Интеграция**

```php
// app/Services/TelegramService.php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class TelegramService
{
    private string $botToken;
    private string $chatId;
    
    public function __construct()
    {
        $this->botToken = config('services.telegram.bot_token');
        $this->chatId = config('services.telegram.chat_id');
    }
    
    public function sendMessage(string $message): bool
    {
        try {
            $response = Http::post("https://api.telegram.org/bot{$this->botToken}/sendMessage", [
                'chat_id' => $this->chatId,
                'text' => $message,
                'parse_mode' => 'HTML',
            ]);
            
            return $response->successful();
        } catch (\Exception $e) {
            Log::error('Failed to send Telegram message', ['error' => $e->getMessage()]);
            return false;
        }
    }
    
    public function sendAnalysisNotification(string $sessionId, string $status): bool
    {
        $message = "🔍 <b>Видео Анализ</b>\n\n";
        $message .= "Сессия: {$sessionId}\n";
        $message .= "Статус: {$status}\n";
        $message .= "Время: " . now()->format('Y-m-d H:i:s');
        
        return $this->sendMessage($message);
    }
}
```

---

### 11. **WebSocket Сервер**

```php
// config/broadcasting.php - Настройка Laravel WebSockets
// Использовать: pusher/pusher-js или soketi
```

---

### 12. **Конфигурация (.env)**

```env
# Laravel Settings
APP_NAME="AI Video Analytics Backend"
APP_ENV=production
APP_KEY=
APP_DEBUG=false

# Database
DB_CONNECTION=postgresql
DB_HOST=127.0.0.1
DB_PORT=5432
DB_DATABASE=video_analytics
DB_USERNAME=username
DB_PASSWORD=password

# Redis
REDIS_HOST=127.0.0.1
REDIS_PASSWORD=null
REDIS_PORT=6379

# FastAPI Integration
FASTAPI_BASE_URL=http://localhost:8080
FASTAPI_API_KEY=my-super-secret-key-123

# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# WebSockets (Pusher)
PUSHER_APP_ID=your-app-id
PUSHER_APP_KEY=your-app-key
PUSHER_APP_SECRET=your-app-secret
PUSHER_APP_CLUSTER=mt1
```

---

### 13. **Тестирование API**

```bash
# Регистрация
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"User","email":"user@example.com","password":"password"}'

# Вход
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'

# Создать сессию
curl -X POST http://localhost:8000/api/sessions \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Session","video_path":"test.mp4"}'

# Запустить анализ
curl -X POST http://localhost:8000/api/sessions/{id}/start-analysis \
  -H "Authorization: Bearer {token}"
```

---

### 14. **Структура Проекта**

```
video-analytics-backend/
├── app/
│   ├── Http/
│   │   ├── Controllers/
│   │   ├── Middleware/
│   │   └── Requests/
│   ├── Models/
│   ├── Services/
│   ├── Jobs/
│   ├── Events/
│   └── Listeners/
│   └── Broadcast/
├── config/
├── database/
│   ├── migrations/
│   └── seeders/
├── resources/
│   └── js/
│       └── websockets.js
├── routes/
│   ├── api.php
│   └── web.php
├── tests/
├── .env.example
└── composer.json
```

---

## 🎯 План Реализации

### Этап 1: Базовая Структура (Day 1)
1. Создать Laravel проект
2. Настроить PostgreSQL
3. Создать модели (User, VideoSession, Report)
4. Настроить авторизацию (Laravel Sanctum)

### Этап 2: Интеграция с FastAPI (Day 2)
1. Создать FastApiClient service
2. Создать контроллеры для видео
3. Интегрировать с API
4. Настроить очереди для фоновой обработки

### Этап 3: Отчеты и Аналитика (Day 3)
1. Создать ReportController
2. Интегрировать с аналитикой FastAPI
3. Настроить кэширование
4. Добавить экспорт отчетов

### Этап 4: Telegram & WebSockets (Day 4)
1. Интегрировать Telegram
2. Настроить WebSockets
3. Добавить real-time обновления
4. Создать дашборды

### Этап 5: Production (Day 5)
1. Тестирование
2. Оптимизация
3. Документация API
4. Деплой

---

## 📊 Технологический Стек

- **Backend**: Laravel 11
- **Database**: PostgreSQL
- **Cache**: Redis
- **Queue**: Redis/Database
- **WebSockets**: Laravel WebSockets (Soketi)
- **Auth**: Laravel Sanctum
- **Microservice**: FastAPI (Python)
- **Notifications**: Telegram Bot API

---

## ✅ Checklist для Реализации

- [ ] Laravel проект создан
- [ ] PostgreSQL настроен
- [ ] Авторизация (Sanctum) работает
- [ ] FastAPI интеграция работает
- [ ] API endpoints реализованы
- [ ] Очереди настроены
- [ ] Redis кэширование работает
- [ ] Telegram уведомления работают
- [ ] WebSockets работают
- [ ] Тесты написаны
- [ ] Документация готова

---

**Команда для создания проекта:**
```bash
composer create-project laravel/laravel video-analytics-backend
cd video-analytics-backend
php artisan install:api
```

