import httpx
import pytest

from app.core.config import Settings
from app.core.exceptions import ExternalServiceError, ExternalServiceUnavailable
from app.services.github_client import GitHubClient


def github_payload(stars: int = 42) -> dict:
    return {
        "owner": {"login": "tiangolo"},
        "name": "fastapi",
        "full_name": "tiangolo/fastapi",
        "html_url": "https://github.com/tiangolo/fastapi",
        "description": "FastAPI framework",
        "stargazers_count": stars,
        "forks_count": 5,
        "open_issues_count": 2,
        "default_branch": "master",
        "language": "Python",
        "visibility": "public",
    }


async def client_with_transport(settings: Settings, transport: httpx.MockTransport):
    client = GitHubClient(settings)
    await client.__aenter__()
    assert client._client is not None
    await client._client.aclose()
    client._client = httpx.AsyncClient(
        base_url=settings.github_api_base_url,
        timeout=settings.http_timeout_seconds,
        transport=transport,
    )
    return client


@pytest.mark.asyncio
async def test_github_client_retries_transient_upstream_errors():
    attempts = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            return httpx.Response(500, json={"message": "temporary failure"})
        return httpx.Response(200, json=github_payload(stars=99))

    settings = Settings(
        github_api_base_url="https://api.github.test",
        github_max_retries=2,
        github_retry_backoff_seconds=0,
    )
    client = await client_with_transport(settings, httpx.MockTransport(handler))

    try:
        metadata = await client.fetch_repository("tiangolo/fastapi")
    finally:
        await client.__aexit__(None, None, None)

    assert attempts == 3
    assert metadata.external_id == "tiangolo/fastapi"
    assert metadata.stars == 99


@pytest.mark.asyncio
async def test_github_client_returns_502_after_retry_exhaustion():
    attempts = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503, json={"message": "still down"})

    settings = Settings(
        github_api_base_url="https://api.github.test",
        github_max_retries=1,
        github_retry_backoff_seconds=0,
    )
    client = await client_with_transport(settings, httpx.MockTransport(handler))

    try:
        with pytest.raises(ExternalServiceError):
            await client.fetch_repository("tiangolo/fastapi")
    finally:
        await client.__aexit__(None, None, None)

    assert attempts == 2


@pytest.mark.asyncio
async def test_github_client_returns_503_after_network_retry_exhaustion():
    attempts = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ConnectError("network unavailable", request=request)

    settings = Settings(
        github_api_base_url="https://api.github.test",
        github_max_retries=1,
        github_retry_backoff_seconds=0,
    )
    client = await client_with_transport(settings, httpx.MockTransport(handler))

    try:
        with pytest.raises(ExternalServiceUnavailable):
            await client.fetch_repository("tiangolo/fastapi")
    finally:
        await client.__aexit__(None, None, None)

    assert attempts == 2
