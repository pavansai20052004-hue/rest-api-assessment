import pytest

from app.core.exceptions import DuplicateRepository
from app.services.repository_service import RepositoryService
from tests.conftest import metadata_for


class FakeStore:
    def __init__(self, exists: bool):
        self.exists = exists
        self.created = False

    async def external_id_exists(self, external_id: str) -> bool:
        return self.exists

    async def create(self, metadata):
        self.created = True
        return metadata


class FakeClient:
    def __init__(self):
        self.called = False

    async def fetch_repository(self, external_id: str):
        self.called = True
        return metadata_for(external_id)


@pytest.mark.asyncio
async def test_create_short_circuits_duplicate_without_network_call():
    store = FakeStore(exists=True)
    github_client = FakeClient()
    service = RepositoryService(store=store, github_client=github_client)

    with pytest.raises(DuplicateRepository):
        await service.create("tiangolo/fastapi")

    assert github_client.called is False
    assert store.created is False


@pytest.mark.asyncio
async def test_create_fetches_and_persists_when_not_duplicate():
    store = FakeStore(exists=False)
    github_client = FakeClient()
    service = RepositoryService(store=store, github_client=github_client)

    created = await service.create("tiangolo/fastapi")

    assert github_client.called is True
    assert store.created is True
    assert created.external_id == "tiangolo/fastapi"
