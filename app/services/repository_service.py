from sqlalchemy.exc import IntegrityError

from app.core.exceptions import DuplicateRepository, RepositoryNotFound
from app.data.repository_store import RepositoryStore
from app.db.models import RepositoryRecord
from app.services.github_client import GitHubClient


class RepositoryService:
    def __init__(self, store: RepositoryStore, github_client: GitHubClient):
        self.store = store
        self.github_client = github_client

    async def create(self, external_id: str) -> RepositoryRecord:
        if await self.store.external_id_exists(external_id):
            raise DuplicateRepository(external_id)

        metadata = await self.github_client.fetch_repository(external_id)
        try:
            return await self.store.create(metadata)
        except IntegrityError as exc:
            raise DuplicateRepository(external_id) from exc

    async def get(self, repository_id: int) -> RepositoryRecord:
        record = await self.store.get_by_id(repository_id)
        if record is None:
            raise RepositoryNotFound(repository_id)
        return record

    async def refresh(self, repository_id: int) -> RepositoryRecord:
        record = await self.get(repository_id)
        metadata = await self.github_client.fetch_repository(record.external_id)
        record.apply_metadata(metadata)
        try:
            return await self.store.save(record)
        except IntegrityError as exc:
            raise DuplicateRepository(record.external_id) from exc

    async def delete(self, repository_id: int) -> None:
        record = await self.get(repository_id)
        await self.store.delete(record)
