import asyncio
import logging

import httpx

from app.core.config import Settings
from app.core.exceptions import (
    ExternalRepositoryNotFound,
    ExternalServiceError,
    ExternalServiceUnavailable,
)
from app.schemas.repository import GitHubRepositoryMetadata
from app.services.github_mapper import map_github_repository

logger = logging.getLogger(__name__)


class GitHubClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "GitHubClient":
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "rest-api-assessment/1.0",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.settings.github_token:
            headers["Authorization"] = f"Bearer {self.settings.github_token}"
        self._client = httpx.AsyncClient(
            base_url=self.settings.github_api_base_url,
            timeout=self.settings.http_timeout_seconds,
            headers=headers,
        )
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        if self._client:
            await self._client.aclose()

    async def fetch_repository(self, external_id: str) -> GitHubRepositoryMetadata:
        if self._client is None:
            raise RuntimeError("GitHubClient must be used as an async context manager.")

        response: httpx.Response | None = None
        attempts = self.settings.github_max_retries + 1
        for attempt in range(1, attempts + 1):
            try:
                response = await self._client.get(f"/repos/{external_id}")
            except (httpx.TimeoutException, httpx.RequestError) as exc:
                if attempt < attempts:
                    await self._sleep_before_retry(attempt, external_id, "network_error")
                    continue
                raise ExternalServiceUnavailable(external_id) from exc

            if response.status_code in {429, 500, 502, 503, 504} and attempt < attempts:
                await self._sleep_before_retry(
                    attempt,
                    external_id,
                    f"upstream_status_{response.status_code}",
                )
                continue
            break

        if response is None:
            raise ExternalServiceUnavailable(external_id)

        if response.status_code == 404:
            raise ExternalRepositoryNotFound(external_id)
        if response.status_code >= 400:
            raise ExternalServiceError(external_id, upstream_status=response.status_code)

        return map_github_repository(response.json())

    async def _sleep_before_retry(self, attempt: int, external_id: str, reason: str) -> None:
        delay = self.settings.github_retry_backoff_seconds * attempt
        logger.warning(
            "Retrying GitHub request",
            extra={
                "external_id": external_id,
                "attempt": attempt,
                "delay_seconds": delay,
                "reason": reason,
            },
        )
        if delay > 0:
            await asyncio.sleep(delay)
