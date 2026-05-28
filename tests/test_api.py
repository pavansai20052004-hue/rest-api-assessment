import pytest


@pytest.mark.asyncio
async def test_post_success_returns_201(api_client):
    response = await api_client.post(
        "/repositories",
        json={"identifier": "https://github.com/tiangolo/fastapi"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["external_id"] == "tiangolo/fastapi"
    assert body["html_url"] == "https://github.com/tiangolo/fastapi"


@pytest.mark.asyncio
async def test_post_duplicate_returns_409(api_client, fake_github_client):
    await api_client.post("/repositories", json={"identifier": "tiangolo/fastapi"})

    response = await api_client.post("/repositories", json={"identifier": "tiangolo/fastapi"})

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "duplicate_repository"
    assert fake_github_client.calls == ["tiangolo/fastapi"]


@pytest.mark.asyncio
async def test_post_invalid_input_returns_422(api_client, fake_github_client):
    response = await api_client.post(
        "/repositories",
        json={"identifier": "https://bitbucket.org/team/project"},
    )

    assert response.status_code == 422
    assert fake_github_client.calls == []


@pytest.mark.asyncio
async def test_get_existing_returns_200(api_client):
    created = await api_client.post("/repositories", json={"identifier": "encode/httpx"})

    response = await api_client.get(f"/repositories/{created.json()['id']}")

    assert response.status_code == 200
    assert response.json()["external_id"] == "encode/httpx"


@pytest.mark.asyncio
async def test_get_missing_returns_404(api_client):
    response = await api_client.get("/repositories/999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "repository_not_found"


@pytest.mark.asyncio
async def test_put_existing_refreshes_metadata(api_client):
    created = await api_client.post("/repositories", json={"identifier": "encode/httpx"})
    repository_id = created.json()["id"]

    response = await api_client.put(f"/repositories/{repository_id}")

    assert response.status_code == 200
    assert response.json()["stars"] == 11


@pytest.mark.asyncio
async def test_put_missing_returns_404(api_client, fake_github_client):
    response = await api_client.put("/repositories/999")

    assert response.status_code == 404
    assert fake_github_client.calls == []


@pytest.mark.asyncio
async def test_delete_existing_returns_204(api_client):
    created = await api_client.post("/repositories", json={"identifier": "encode/httpx"})
    repository_id = created.json()["id"]

    response = await api_client.delete(f"/repositories/{repository_id}")

    assert response.status_code == 204
    assert response.content == b""


@pytest.mark.asyncio
async def test_delete_missing_returns_404(api_client):
    response = await api_client.delete("/repositories/999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "repository_not_found"


@pytest.mark.asyncio
async def test_external_unavailable_returns_503(
    api_client, fake_github_client, upstream_unavailable
):
    fake_github_client.errors["tiangolo/fastapi"] = upstream_unavailable

    response = await api_client.post("/repositories", json={"identifier": "tiangolo/fastapi"})

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "external_service_unavailable"


@pytest.mark.asyncio
async def test_external_error_returns_502(api_client, fake_github_client, upstream_bad_gateway):
    fake_github_client.errors["tiangolo/fastapi"] = upstream_bad_gateway

    response = await api_client.post("/repositories", json={"identifier": "tiangolo/fastapi"})

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "external_service_error"
