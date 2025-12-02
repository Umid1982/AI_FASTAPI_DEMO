from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import structlog
from app.core.config import settings
from app.utils.http_client import OllamaHTTPClient, OpenAIHTTPClient

logger = structlog.get_logger()


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate_report(self, data: Dict[str, Any]) -> str:
        """Generate report from analytics data."""
        pass
    
    @abstractmethod
    async def generate_summary(self, text: str) -> str:
        """Generate summary of text."""
        pass


class OllamaProvider(LLMProvider):
    """Ollama LLM provider."""
    
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or settings.ollama_model
        self.client = OllamaHTTPClient(self.base_url, self.model)
        logger.info("Ollama provider initialized", base_url=self.base_url, model=self.model)
    
    async def generate_report(self, data: Dict[str, Any]) -> str:
        """Generate analytics report using Ollama."""
        try:
            # Create detailed prompt for analytics report
            prompt = self._create_analytics_prompt(data)
            
            response = await self.client.generate(
                prompt=prompt,
                model=self.model,
                options={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 1000
                }
            )
            
            report = response.get("response", "").strip()
            logger.info("Analytics report generated", report_length=len(report))
            return report
            
        except Exception as e:
            logger.error("Failed to generate report with Ollama", error=str(e))
            # Fallback to mock report if Ollama is not available
            logger.info("Using mock report as fallback")
            return self._generate_mock_report(data)
    
    async def generate_summary(self, text: str) -> str:
        """Generate summary using Ollama."""
        try:
            prompt = f"Summarize the following text in 2-3 sentences:\n\n{text}"
            
            response = await self.client.generate(
                prompt=prompt,
                model=self.model,
                options={
                    "temperature": 0.5,
                    "max_tokens": 200
                }
            )
            
            summary = response.get("response", "").strip()
            logger.info("Summary generated", summary_length=len(summary))
            return summary
            
        except Exception as e:
            logger.error("Failed to generate summary with Ollama", error=str(e))
            # Fallback to mock summary
            logger.info("Using mock summary as fallback")
            return f"[MOCK] Краткое резюме: {text[:100]}... (Ollama недоступен)"
    
    def _create_analytics_prompt(self, data: Dict[str, Any]) -> str:
        """Create detailed prompt for analytics report."""
        return f"""
You are an AI video analytics expert. Analyze the following video surveillance data and generate a comprehensive report in Russian.

Data:
- Total people detected: {data.get('total_people', 0)}
- Peak people count: {data.get('peak_people_count', 0)}
- Average stay time: {data.get('average_stay_time', 0):.1f} seconds
- Total frames processed: {data.get('total_frames', 0)}
- Session duration: {data.get('session_duration', 0):.1f} seconds
- Peak hours: {data.get('peak_hours', [])}
- Heatmap data points: {data.get('heatmap_points_count', 0)}

Please provide:
1. Brief overview of activity
2. Key insights about people movement
3. Peak activity periods
4. Recommendations for optimization
5. Any notable patterns or anomalies

Keep the report professional and concise (2-3 paragraphs).
"""
    
    def _generate_mock_report(self, data: Dict[str, Any]) -> str:
        """Generate mock report for testing when LLM is not available."""
        total_people = data.get('total_people', 0)
        peak_people = data.get('peak_people_count', 0)
        avg_stay = data.get('average_stay_time', 0)
        total_frames = data.get('total_frames', 0)
        
        return f"""
АНАЛИТИЧЕСКИЙ ОТЧЕТ (MOCK - Ollama недоступен)

Краткий обзор:
В ходе обработки видео было детектировано {total_people} уникальных людей. Максимальное одновременное количество людей составило {peak_people}. Средняя продолжительность присутствия людей в кадре: {avg_stay:.2f} секунд. Всего было обработано {total_frames} кадров.

Ключевые инсайты:
Наблюдается стабильная активность с пиковыми моментами. Движение людей распределено равномерно по всему периоду наблюдения. Среднее время нахождения в зоне наблюдения составляет около {avg_stay:.1f} секунд, что указывает на нормальный поток людей без длительных задержек.

Рекомендации:
Рекомендуется проанализировать пиковые периоды для оптимизации маршрутов и распределения ресурсов. Необходимо продолжить мониторинг для выявления долгосрочных паттернов.
"""


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""
    
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = OpenAIHTTPClient(self.api_key)
        logger.info("OpenAI provider initialized", model=self.model)
    
    async def generate_report(self, data: Dict[str, Any]) -> str:
        """Generate analytics report using OpenAI."""
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are an AI video analytics expert. Generate comprehensive reports in Russian based on surveillance data."
                },
                {
                    "role": "user",
                    "content": self._create_analytics_prompt(data)
                }
            ]
            
            response = await self.client.chat_completion(
                messages=messages,
                model=self.model,
                temperature=0.7,
                max_tokens=1000
            )
            
            report = response["choices"][0]["message"]["content"].strip()
            logger.info("Analytics report generated", report_length=len(report))
            return report
            
        except Exception as e:
            logger.error("Failed to generate report with OpenAI", error=str(e))
            raise
    
    async def generate_summary(self, text: str) -> str:
        """Generate summary using OpenAI."""
        try:
            messages = [
                {
                    "role": "system",
                    "content": "Summarize the following text in 2-3 sentences in Russian."
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
            
            response = await self.client.chat_completion(
                messages=messages,
                model=self.model,
                temperature=0.5,
                max_tokens=200
            )
            
            summary = response["choices"][0]["message"]["content"].strip()
            logger.info("Summary generated", summary_length=len(summary))
            return summary
            
        except Exception as e:
            logger.error("Failed to generate summary with OpenAI", error=str(e))
            raise
    
    def _create_analytics_prompt(self, data: Dict[str, Any]) -> str:
        """Create detailed prompt for analytics report."""
        return f"""
Проанализируйте следующие данные видеонаблюдения и создайте подробный отчет:

Данные:
- Общее количество людей: {data.get('total_people', 0)}
- Пиковое количество людей: {data.get('peak_people_count', 0)}
- Среднее время нахождения: {data.get('average_stay_time', 0):.1f} секунд
- Обработано кадров: {data.get('total_frames', 0)}
- Длительность сессии: {data.get('session_duration', 0):.1f} секунд
- Пиковые часы: {data.get('peak_hours', [])}
- Точки тепловой карты: {data.get('heatmap_points_count', 0)}

Предоставьте:
1. Краткий обзор активности
2. Ключевые инсайты о движении людей
3. Периоды пиковой активности
4. Рекомендации по оптимизации
5. Заметные паттерны или аномалии

Отчет должен быть профессиональным и кратким (2-3 абзаца).
"""


class LLMService:
    """Service for LLM operations."""
    
    def __init__(self, provider: LLMProvider = None):
        self.provider = provider or self._create_default_provider()
        logger.info("LLM service initialized", provider=self.provider.__class__.__name__)
    
    @classmethod
    def create_ollama_service(cls) -> 'LLMService':
        """Create LLM service with Ollama provider."""
        provider = OllamaProvider()
        return cls(provider)
    
    @classmethod
    def create_openai_service(cls) -> 'LLMService':
        """Create LLM service with OpenAI provider."""
        provider = OpenAIProvider()
        return cls(provider)
    
    def _create_default_provider(self) -> LLMProvider:
        """Create default provider based on configuration."""
        if settings.llm_provider == "ollama":
            return OllamaProvider()
        elif settings.llm_provider == "openai":
            return OpenAIProvider()
        else:
            logger.warning("Unknown LLM provider, falling back to Ollama")
            return OllamaProvider()
    
    async def generate_report(self, data: Dict[str, Any]) -> str:
        """Generate analytics report."""
        try:
            report = await self.provider.generate_report(data)
            logger.info("Report generated successfully")
            return report
        except Exception as e:
            logger.error("Failed to generate report", error=str(e))
            raise
    
    async def generate_summary(self, text: str) -> str:
        """Generate text summary."""
        try:
            summary = await self.provider.generate_summary(text)
            logger.info("Summary generated successfully")
            return summary
        except Exception as e:
            logger.error("Failed to generate summary", error=str(e))
            raise
    
    async def close(self):
        """Close LLM service."""
        if hasattr(self.provider, 'client') and hasattr(self.provider.client, 'close'):
            await self.provider.client.close()
        logger.info("LLM service closed")
