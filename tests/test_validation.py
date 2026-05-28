import pytest
from pydantic import ValidationError

from app.schemas.repository import RepositoryCreate, normalize_github_identifier


def test_accepts_github_repository_url_and_normalizes_identifier():
    payload = RepositoryCreate(identifier="https://github.com/tiangolo/fastapi")

    assert payload.identifier == "tiangolo/fastapi"


def test_accepts_owner_repo_identifier():
    assert normalize_github_identifier("encode/httpx") == "encode/httpx"


@pytest.mark.parametrize(
    "identifier",
    [
        "https://gitlab.com/tiangolo/fastapi",
        "not-a-valid-repository",
        "https://github.com/tiangolo/fastapi/issues",
    ],
)
def test_rejects_invalid_identifier_categories(identifier):
    with pytest.raises(ValueError):
        normalize_github_identifier(identifier)


def test_missing_identifier_is_schema_validation_error():
    with pytest.raises(ValidationError):
        RepositoryCreate.model_validate({})
