from app.services.github_mapper import map_github_repository


def test_maps_github_json_to_internal_metadata():
    raw = {
        "owner": {"login": "encode"},
        "name": "httpx",
        "full_name": "encode/httpx",
        "html_url": "https://github.com/encode/httpx",
        "description": "A next generation HTTP client.",
        "stargazers_count": 15000,
        "forks_count": 900,
        "open_issues_count": 120,
        "default_branch": "master",
        "language": "Python",
        "visibility": "public",
    }

    metadata = map_github_repository(raw)

    assert metadata.external_id == "encode/httpx"
    assert metadata.owner == "encode"
    assert metadata.name == "httpx"
    assert metadata.stars == 15000
    assert metadata.forks == 900
    assert metadata.open_issues == 120
    assert metadata.raw_metadata == raw
