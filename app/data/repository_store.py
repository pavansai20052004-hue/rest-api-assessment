from sqlalchemy import exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import RepositoryRecord
from app.schemas.repository import GitHubRepositoryMetadata


class RepositoryStore:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def external_id_exists(self, external_id: str) -> bool:
        statement = select(exists().where(RepositoryRecord.external_id == external_id))
        return bool(await self.session.scalar(statement))

    async def get_by_id(self, repository_id: int) -> RepositoryRecord | None:
        return await self.session.get(RepositoryRecord, repository_id)

    async def create(self, metadata: GitHubRepositoryMetadata) -> RepositoryRecord:
        record = RepositoryRecord(
            external_id=metadata.external_id,
            owner=metadata.owner,
            name=metadata.name,
            full_name=metadata.full_name,
            html_url=metadata.html_url,
            description=metadata.description,
            stars=metadata.stars,
            forks=metadata.forks,
            open_issues=metadata.open_issues,
            default_branch=metadata.default_branch,
            language=metadata.language,
            visibility=metadata.visibility,
            raw_metadata=metadata.raw_metadata,
            last_fetched_at=metadata.last_fetched_at,
        )
        self.session.add(record)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise
        await self.session.refresh(record)
        return record

    async def save(self, record: RepositoryRecord) -> RepositoryRecord:
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise
        await self.session.refresh(record)
        return record

    async def delete(self, record: RepositoryRecord) -> None:
        await self.session.delete(record)
        await self.session.commit()
