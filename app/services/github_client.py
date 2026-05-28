import httpx

from app.core.config import Settings
from app.core.exceptions import (
    ExternalRepositoryNotFound,
    ExternalServiceError,
    ExternalServiceUnavailable,
)
from app.schemas.repository import GitHubRepositoryMetadata
from app.services.github_mapper import map_github_repository


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

        try:
            response = await self._client.get(f"/repos/{external_id}")
        except (httpx.TimeoutException, httpx.RequestError) as exc:
            raise ExternalServiceUnavailable(external_id) from exc

        if response.status_code == 404:
            raise ExternalRepositoryNotFound(external_id)
        if response.status_code >= 400:
            raise ExternalServiceError(external_id, upstream_status=response.status_code)

        return map_github_repository(response.json())
