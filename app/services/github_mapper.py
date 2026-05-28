from datetime import datetime, timezone
from typing import Any

from app.core.exceptions import ExternalServiceError
from app.schemas.repository import GitHubRepositoryMetadata


def map_github_repository(payload: dict[str, Any]) -> GitHubRepositoryMetadata:
    try:
        owner_login = payload["owner"]["login"]
        name = payload["name"]
        full_name = payload["full_name"]
        html_url = payload["html_url"]
        default_branch = payload["default_branch"]
    except (KeyError, TypeError) as exc:
        raise ExternalServiceError("unknown") from exc

    visibility = payload.get("visibility")
    if not visibility:
        visibility = "private" if payload.get("private") else "public"

    return GitHubRepositoryMetadata(
        external_id=full_name,
        owner=owner_login,
        name=name,
        full_name=full_name,
        html_url=html_url,
        description=payload.get("description"),
        stars=int(payload.get("stargazers_count") or 0),
        forks=int(payload.get("forks_count") or 0),
        open_issues=int(payload.get("open_issues_count") or 0),
        default_branch=default_branch,
        language=payload.get("language"),
        visibility=visibility,
        raw_metadata=payload,
        last_fetched_at=datetime.now(timezone.utc),
    )
