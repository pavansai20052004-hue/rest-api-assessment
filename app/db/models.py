from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.schemas.repository import GitHubRepositoryMetadata


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RepositoryRecord(Base):
    __tablename__ = "repositories"
    __table_args__ = (
        UniqueConstraint("external_id", name="uq_repositories_external_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    external_id: Mapped[str] = mapped_column(String(140), nullable=False, index=True)
    owner: Mapped[str] = mapped_column(String(39), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    full_name: Mapped[str] = mapped_column(String(140), nullable=False)
    html_url: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    stars: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    forks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    open_issues: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    default_branch: Mapped[str] = mapped_column(String(100), nullable=False)
    language: Mapped[str | None] = mapped_column(String(100), nullable=True)
    visibility: Mapped[str] = mapped_column(String(20), nullable=False)
    raw_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )
    last_fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    def apply_metadata(self, metadata: GitHubRepositoryMetadata) -> None:
        self.external_id = metadata.external_id
        self.owner = metadata.owner
        self.name = metadata.name
        self.full_name = metadata.full_name
        self.html_url = metadata.html_url
        self.description = metadata.description
        self.stars = metadata.stars
        self.forks = metadata.forks
        self.open_issues = metadata.open_issues
        self.default_branch = metadata.default_branch
        self.language = metadata.language
        self.visibility = metadata.visibility
        self.raw_metadata = metadata.raw_metadata
        self.last_fetched_at = metadata.last_fetched_at
