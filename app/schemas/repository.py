from datetime import datetime
import re
from typing import Any
from urllib.parse import unquote, urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator

OWNER_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,100}$")


def normalize_github_identifier(value: str) -> str:
    raw = value.strip()
    if not raw:
        raise ValueError("identifier is required")

    if "://" in raw or raw.lower().startswith("www."):
        parsed = urlparse(raw if "://" in raw else f"https://{raw}")
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("identifier URL must use http or https")
        if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
            raise ValueError("identifier must point to github.com")
        parts = [unquote(part) for part in parsed.path.strip("/").split("/") if part]
        if len(parts) != 2:
            raise ValueError("GitHub URL must be in the form https://github.com/{owner}/{repo}")
        owner, repository = parts
    else:
        parts = raw.split("/")
        if len(parts) != 2:
            raise ValueError("identifier must be either owner/repo or a GitHub repository URL")
        owner, repository = parts

    repository = repository.removesuffix(".git")
    if not OWNER_PATTERN.fullmatch(owner):
        raise ValueError("owner must be a valid GitHub account or organization name")
    if not REPOSITORY_PATTERN.fullmatch(repository):
        raise ValueError("repository name contains unsupported characters")
    return f"{owner}/{repository}"


class RepositoryCreate(BaseModel):
    identifier: str = Field(
        ...,
        examples=["https://github.com/tiangolo/fastapi"],
        description="GitHub repository URL or owner/repo identifier.",
    )

    @field_validator("identifier")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return normalize_github_identifier(value)


class GitHubRepositoryMetadata(BaseModel):
    external_id: str
    owner: str
    name: str
    full_name: str
    html_url: str
    description: str | None
    stars: int
    forks: int
    open_issues: int
    default_branch: str
    language: str | None
    visibility: str
    raw_metadata: dict[str, Any]
    last_fetched_at: datetime


class RepositoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: str
    owner: str
    name: str
    full_name: str
    html_url: str
    description: str | None
    stars: int
    forks: int
    open_issues: int
    default_branch: str
    language: str | None
    visibility: str
    created_at: datetime
    updated_at: datetime
    last_fetched_at: datetime
