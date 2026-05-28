from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_github_client, get_session
from app.core.exceptions import ExternalServiceError, ExternalServiceUnavailable
from app.db.base import Base
from app.main import app
from app.schemas.repository import GitHubRepositoryMetadata


def metadata_for(external_id: str, stars: int = 10) -> GitHubRepositoryMetadata:
    owner, name = external_id.split("/", 1)
    return GitHubRepositoryMetadata(
        external_id=external_id,
        owner=owner,
        name=name,
        full_name=external_id,
        html_url=f"https://github.com/{external_id}",
        description=f"{external_id} test repository",
        stars=stars,
        forks=2,
        open_issues=1,
        default_branch="main",
        language="Python",
        visibility="public",
        raw_metadata={"full_name": external_id, "stargazers_count": stars},
        last_fetched_at=datetime.now(timezone.utc),
    )


class FakeGitHubClient:
    def __init__(self):
        self.calls: list[str] = []
        self.errors: dict[str, Exception] = {}
        self.call_counts: dict[str, int] = {}

    async def fetch_repository(self, external_id: str) -> GitHubRepositoryMetadata:
        self.calls.append(external_id)
        if external_id in self.errors:
            raise self.errors[external_id]
        count = self.call_counts.get(external_id, 0)
        self.call_counts[external_id] = count + 1
        return metadata_for(external_id, stars=10 + count)


@pytest.fixture
def fake_github_client() -> FakeGitHubClient:
    return FakeGitHubClient()


@pytest_asyncio.fixture
async def api_client(fake_github_client: FakeGitHubClient):
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async def override_session():
        async with session_maker() as session:
            yield session

    async def override_github_client():
        yield fake_github_client

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_github_client] = override_github_client

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.fixture
def upstream_unavailable() -> ExternalServiceUnavailable:
    return ExternalServiceUnavailable("tiangolo/fastapi")


@pytest.fixture
def upstream_bad_gateway() -> ExternalServiceError:
    return ExternalServiceError("tiangolo/fastapi", upstream_status=500)
