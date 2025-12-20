# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx


DEFAULT_API_URL = "https://api.firecrawl.dev/v1"


@dataclass(slots=True)
class FirecrawlConfig:
    api_key: str | None = None
    base_url: str = DEFAULT_API_URL
    timeout: float = 30.0

    @classmethod
    def from_env(cls) -> "FirecrawlConfig":
        return cls(
            api_key=os.getenv("FIRECRAWL_API_KEY"),
            base_url=os.getenv("FIRECRAWL_BASE_URL", DEFAULT_API_URL),
            timeout=float(os.getenv("FIRECRAWL_TIMEOUT", "30")),
        )


@dataclass
class FirecrawlResult:
    success: bool
    data: list[dict[str, Any]]
    error: str | None = None


class FirecrawlClient:
    def __init__(self, config: FirecrawlConfig | None = None):
        self._config = config or FirecrawlConfig.from_env()
        if not self._config.api_key:
            raise ValueError("FIRECRAWL_API_KEY is required")

    async def search(self, query: str, limit: int = 5) -> FirecrawlResult:
        url = f"{self._config.base_url}/search"
        headers = {
            "Authorization": f"Bearer {self._config.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "query": query,
            "limit": limit,
        }

        try:
            async with httpx.AsyncClient(timeout=self._config.timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                results = data.get("data", [])
                return FirecrawlResult(success=True, data=results)
        except httpx.HTTPStatusError as e:
            return FirecrawlResult(success=False, data=[], error=f"HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            return FirecrawlResult(success=False, data=[], error=str(e))

    async def scrape(self, url: str, formats: list[str] | None = None) -> FirecrawlResult:
        api_url = f"{self._config.base_url}/scrape"
        headers = {
            "Authorization": f"Bearer {self._config.api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {"url": url}
        if formats:
            payload["formats"] = formats

        try:
            async with httpx.AsyncClient(timeout=self._config.timeout) as client:
                response = await client.post(api_url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                return FirecrawlResult(success=True, data=[data.get("data", {})])
        except httpx.HTTPStatusError as e:
            return FirecrawlResult(success=False, data=[], error=f"HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            return FirecrawlResult(success=False, data=[], error=str(e))

    async def crawl(self, url: str, limit: int = 10, max_depth: int = 2) -> FirecrawlResult:
        api_url = f"{self._config.base_url}/crawl"
        headers = {
            "Authorization": f"Bearer {self._config.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "url": url,
            "limit": limit,
            "maxDepth": max_depth,
        }

        try:
            async with httpx.AsyncClient(timeout=self._config.timeout) as client:
                response = await client.post(api_url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                return FirecrawlResult(success=True, data=[data])
        except httpx.HTTPStatusError as e:
            return FirecrawlResult(success=False, data=[], error=f"HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            return FirecrawlResult(success=False, data=[], error=str(e))


def create_firecrawl_client(config: FirecrawlConfig | None = None) -> FirecrawlClient:
    return FirecrawlClient(config)


__all__ = [
    "FirecrawlConfig",
    "FirecrawlResult",
    "FirecrawlClient",
    "create_firecrawl_client",
]

