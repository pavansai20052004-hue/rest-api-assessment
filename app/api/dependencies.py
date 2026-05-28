from collections.abc import AsyncIterator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.data.repository_store import RepositoryStore
from app.db.database import async_session_maker
from app.services.github_client import GitHubClient
from app.services.repository_service import RepositoryService


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session_maker() as session:
        yield session


async def get_github_client(
    settings: Settings = Depends(get_settings),
) -> AsyncIterator[GitHubClient]:
    async with GitHubClient(settings) as client:
        yield client


def get_repository_store(
    session: AsyncSession = Depends(get_session),
) -> RepositoryStore:
    return RepositoryStore(session)


def get_repository_service(
    store: RepositoryStore = Depends(get_repository_store),
    github_client: GitHubClient = Depends(get_github_client),
) -> RepositoryService:
    return RepositoryService(store=store, github_client=github_client)
