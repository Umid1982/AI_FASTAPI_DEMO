import httpx
from typing import Dict, Any, Optional, Union
from urllib.parse import urljoin
import structlog
from app.core.config import settings

logger = structlog.get_logger()


class BaseHTTPClient:
    """Base HTTP client with common functionality."""
    
    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        headers: Optional[Dict[str, str]] = None
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.default_headers = headers or {}
        
        # Create httpx client with default configuration
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers=self.default_headers
        )
    
    def _get_headers(self, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Get headers with extra headers merged in."""
        headers = self.default_headers.copy()
        if extra_headers:
            headers.update(extra_headers)
        return headers
    
    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> httpx.Response:
        """Make GET request."""
        url = urljoin(self.base_url, endpoint.lstrip('/'))
        request_headers = self._get_headers(headers)
        
        logger.debug("Making GET request", url=url, params=params)
        
        try:
            response = await self.client.get(
                url,
                params=params,
                headers=request_headers
            )
            logger.debug("GET response", status_code=response.status_code, url=url)
            return response
        except httpx.RequestError as e:
            logger.error("GET request failed", url=url, error=str(e))
            raise
    
    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> httpx.Response:
        """Make POST request."""
        url = urljoin(self.base_url, endpoint.lstrip('/'))
        request_headers = self._get_headers(headers)
        
        logger.debug("Making POST request", url=url, data=data, json=json)
        
        try:
            response = await self.client.post(
                url,
                data=data,
                json=json,
                headers=request_headers
            )
            logger.debug("POST response", status_code=response.status_code, url=url)
            return response
        except httpx.RequestError as e:
            logger.error("POST request failed", url=url, error=str(e))
            raise
    
    async def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> httpx.Response:
        """Make PUT request."""
        url = urljoin(self.base_url, endpoint.lstrip('/'))
        request_headers = self._get_headers(headers)
        
        logger.debug("Making PUT request", url=url, data=data, json=json)
        
        try:
            response = await self.client.put(
                url,
                data=data,
                json=json,
                headers=request_headers
            )
            logger.debug("PUT response", status_code=response.status_code, url=url)
            return response
        except httpx.RequestError as e:
            logger.error("PUT request failed", url=url, error=str(e))
            raise
    
    async def delete(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None
    ) -> httpx.Response:
        """Make DELETE request."""
        url = urljoin(self.base_url, endpoint.lstrip('/'))
        request_headers = self._get_headers(headers)
        
        logger.debug("Making DELETE request", url=url)
        
        try:
            response = await self.client.delete(url, headers=request_headers)
            logger.debug("DELETE response", status_code=response.status_code, url=url)
            return response
        except httpx.RequestError as e:
            logger.error("DELETE request failed", url=url, error=str(e))
            raise
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class OllamaHTTPClient(BaseHTTPClient):
    """HTTP client for Ollama API (аналог AlscomHttpClient)."""
    
    def __init__(self, base_url: str = None, model: str = None):
        base_url = base_url or settings.ollama_base_url
        model = model or settings.ollama_model
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        super().__init__(base_url, headers=headers)
        self.model = model
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate text using Ollama."""
        model = model or self.model
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            **kwargs
        }
        
        response = await self.post("/api/generate", json=payload)
        response.raise_for_status()
        return response.json()
    
    async def chat(
        self,
        messages: list,
        model: Optional[str] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Chat with Ollama."""
        model = model or self.model
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            **kwargs
        }
        
        response = await self.post("/api/chat", json=payload)
        response.raise_for_status()
        return response.json()


class OpenAIHTTPClient(BaseHTTPClient):
    """HTTP client for OpenAI API."""
    
    def __init__(self, api_key: str = None, base_url: str = "https://api.openai.com/v1"):
        api_key = api_key or settings.openai_api_key
        
        if not api_key:
            raise ValueError("OpenAI API key is required")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        super().__init__(base_url, headers=headers)
    
    async def chat_completion(
        self,
        messages: list,
        model: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create chat completion."""
        model = model or settings.openai_model
        
        payload = {
            "model": model,
            "messages": messages,
            **kwargs
        }
        
        response = await self.post("/chat/completions", json=payload)
        response.raise_for_status()
        return response.json()
    
    async def completion(
        self,
        prompt: str,
        model: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create completion."""
        model = model or settings.openai_model
        
        payload = {
            "model": model,
            "prompt": prompt,
            **kwargs
        }
        
        response = await self.post("/completions", json=payload)
        response.raise_for_status()
        return response.json()
