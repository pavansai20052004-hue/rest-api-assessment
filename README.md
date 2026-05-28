# GitHub Repository Metadata API

## Project Overview

This service stores metadata for public GitHub repositories in a local database and exposes a small REST API to create, read, refresh, and delete those records. I chose the GitHub REST API because repository URLs are easy to validate strictly, responses are stable JSON, and unauthenticated access works for local evaluation while an optional token can raise rate limits.

## Demo And Approach

- Demo video: [`demo/rest_api_assessment_demo.mp4`](demo/rest_api_assessment_demo.mp4)
- Demo narration/script: [`demo/DEMO_SCRIPT.md`](demo/DEMO_SCRIPT.md)
- Detailed way of approach: [`docs/APPROACH.md`](docs/APPROACH.md)

## Architecture Summary

The application uses a layered FastAPI architecture:

- `app/api`: route handlers and dependency wiring only.
- `app/services`: business rules plus the async GitHub HTTP client and response mapper.
- `app/data`: database access methods for repository records.
- `app/db`: SQLAlchemy async engine, ORM base, and models.
- `app/schemas`: request validation, response schemas, and internal DTOs.
- `alembic`: versioned database migrations for repeatable PostgreSQL setup.

For a `POST /repositories` request, Pydantic first normalizes and validates the supplied GitHub URL or `owner/repo` identifier. The service checks for an existing local record, fetches metadata from GitHub with `httpx.AsyncClient`, maps the upstream JSON into an internal DTO, and asks the data layer to persist it with SQLAlchemy. Duplicate protection is enforced both by service logic and by a database-level unique constraint on `external_id`.

Every request receives an `X-Request-ID` response header and emits a structured JSON access log with method, path, status code, duration, and trace ID. GitHub calls use bounded retry/backoff for transient network failures, rate limits, and temporary upstream outages before returning the assessment-required `502` or `503` response.

## Prerequisites

- Python 3.10 or newer.
- PostgreSQL 13 or newer.
- Git.
- Optional: Docker 24+ and Docker Compose v2 for one-command local startup.
- Optional: a GitHub personal access token if you want higher API rate limits.

## Setup Instructions

1. Clone the repository:

   ```bash
   git clone https://github.com/pavansai20052004-hue/rest-api-assessment.git
   cd rest-api-assessment
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

   On macOS/Linux:

   ```bash
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create your environment file:

   ```bash
   copy .env.example .env
   ```

   On macOS/Linux:

   ```bash
   cp .env.example .env
   ```

5. Create a PostgreSQL database named `rest_api_assessment`, or update `DATABASE_URL` in `.env` to point to your database.

6. Initialize the schema:

   ```bash
   alembic upgrade head
   ```

   If you want the simplest non-migration bootstrap for local experimentation, `python scripts/init_db.py` creates the same ORM tables directly.

7. Start the API:

   ```bash
   uvicorn app.main:app --reload
   ```

8. Send a request:

   ```bash
   curl -X POST http://127.0.0.1:8000/repositories ^
     -H "Content-Type: application/json" ^
     -d "{\"identifier\":\"https://github.com/tiangolo/fastapi\"}"
   ```

   On macOS/Linux, replace `^` with `\`.

### Docker Setup

Run the API and PostgreSQL together:

```bash
docker compose up --build
```

The API listens on `http://127.0.0.1:8000` and runs Alembic migrations before starting.

## Environment Variables Reference

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `DATABASE_URL` | Yes | `postgresql+asyncpg://postgres:postgres@localhost:5432/rest_api_assessment` | Async SQLAlchemy database URL. Plain `postgresql://` is normalized to `postgresql+asyncpg://`. |
| `GITHUB_API_BASE_URL` | No | `https://api.github.com` | Base URL for the GitHub REST API. Useful for tests or proxies. |
| `GITHUB_TOKEN` | No | empty | Optional bearer token for higher GitHub rate limits. Never commit a real value. |
| `HTTP_TIMEOUT_SECONDS` | No | `10` | Timeout for external GitHub API calls. Timeouts return `503`. |
| `GITHUB_MAX_RETRIES` | No | `2` | Number of retry attempts for transient GitHub failures before returning `502` or `503`. |
| `GITHUB_RETRY_BACKOFF_SECONDS` | No | `0.2` | Base async backoff delay between GitHub retry attempts. |
| `DATABASE_AUTO_CREATE` | No | `false` | If true, the app creates ORM tables on startup. The init script is preferred for normal local runs. |
| `LOG_LEVEL` | No | `INFO` | Python logging level. |
| `LOG_JSON` | No | `true` | Emit structured JSON logs suitable for log aggregation. |

## API Reference

The application intentionally exposes only the four assessment endpoints.

### POST `/repositories`

Creates a stored repository record from a GitHub URL or `owner/repo` identifier.

Request body:

```json
{
  "identifier": "https://github.com/tiangolo/fastapi"
}
```

Successful `201 Created` response:

```json
{
  "id": 1,
  "external_id": "tiangolo/fastapi",
  "owner": "tiangolo",
  "name": "fastapi",
  "full_name": "tiangolo/fastapi",
  "html_url": "https://github.com/tiangolo/fastapi",
  "description": "FastAPI framework, high performance, easy to learn, fast to code, ready for production",
  "stars": 80000,
  "forks": 7000,
  "open_issues": 700,
  "default_branch": "master",
  "language": "Python",
  "visibility": "public",
  "created_at": "2026-05-28T06:30:00Z",
  "updated_at": "2026-05-28T06:30:00Z",
  "last_fetched_at": "2026-05-28T06:30:00Z"
}
```

Possible responses:

| Status | Meaning |
| --- | --- |
| `201` | Repository metadata fetched and stored. |
| `404` | GitHub reports the repository does not exist. |
| `409` | The same repository is already stored. |
| `422` | Request body is missing or the identifier is malformed, unsupported, or not a GitHub repository. |
| `502` | GitHub returned an upstream error. |
| `503` | GitHub could not be reached or timed out. |

### GET `/repositories/{id}`

Reads a stored record by database ID. This endpoint never calls GitHub.

Successful `200 OK` response uses the same body shape as `POST`.

Possible responses:

| Status | Meaning |
| --- | --- |
| `200` | Stored repository record found. |
| `404` | No local record exists for that ID. |

### PUT `/repositories/{id}`

Refreshes an existing record by fetching the same repository from GitHub again.

Request body: none.

Successful `200 OK` response uses the same body shape as `POST`, with refreshed metadata and timestamps.

Possible responses:

| Status | Meaning |
| --- | --- |
| `200` | Stored record refreshed. |
| `404` | Local record does not exist, or GitHub now reports that the repository does not exist. |
| `502` | GitHub returned an upstream error. |
| `503` | GitHub could not be reached or timed out. |

### DELETE `/repositories/{id}`

Deletes a stored record by database ID.

Request body: none.

Successful response:

```http
204 No Content
```

Possible responses:

| Status | Meaning |
| --- | --- |
| `204` | Stored record deleted; response body is empty. |
| `404` | No local record exists for that ID. |

## Running The Tests

Run all tests with:

```bash
pytest
```

The unit tests cover schema-level input parsing, invalid input rejection, GitHub JSON mapping, duplicate detection, request tracing, and retry/error mapping without real network or database I/O. The integration tests use FastAPI with an async HTTP client, mock the GitHub client, and use isolated in-memory SQLite to cover the required endpoint scenarios plus upstream `502` and `503` handling.

GitHub Actions runs the same `pytest` command on every push and pull request to `main`.

## Design Decisions

- GitHub was selected as the upstream API because repository URLs have clear domain-specific validation rules and the public API is usable without mandatory secrets.
- The API accepts both `owner/repo` and `https://github.com/owner/repo` but rejects SSH URLs, non-GitHub domains, and URLs with extra path segments such as issues or pulls.
- Route handlers stay thin; they only bind request/response models and delegate to the service layer.
- Duplicate handling checks locally before calling GitHub for a faster `409`, but the database unique constraint is still the final authority.
- Alembic migrations are included instead of relying only on ad hoc table creation, because reviewers can inspect and replay schema history.
- External GitHub failures use bounded retries for transient `429` and `5xx` responses, but permanent upstream `404` responses are not retried.
- Structured JSON logs and `X-Request-ID` headers are included for production-style debugging without changing the required four-endpoint API surface.
- FastAPI's built-in docs routes are disabled so the public route surface remains exactly the four endpoints requested in the assessment.
- Docker Compose is included as a bonus path for evaluators who want a clean PostgreSQL instance without manual setup.

## Assumptions

- Only GitHub repository resources are in scope, not users, gists, issues, or pull requests.
- Repository identifiers are case-preserving and stored in the canonical `owner/repo` form returned by GitHub.
- Refreshing a record should keep the same database ID and overwrite metadata fields in place.
- The assessment asks for local execution, so no cloud deployment configuration is included.
- SQLite is used only in tests to keep integration tests fast and isolated; runtime configuration is PostgreSQL-first.

## Troubleshooting

| Problem | Cause | Fix |
| --- | --- | --- |
| `asyncpg.exceptions.InvalidCatalogNameError` | The configured database does not exist. | Create `rest_api_assessment` in PostgreSQL or update `DATABASE_URL`. |
| `ConnectionRefusedError` on startup or init | PostgreSQL is not running or the port differs. | Start PostgreSQL, verify host/port, or use `docker compose up --build`. |
| Alembic cannot import `app` | The command is being run from outside the repository root. | `cd rest-api-assessment` and rerun `alembic upgrade head`. |
| `422 Unprocessable Entity` for a URL | The URL is not exactly a GitHub repository URL. | Use `owner/repo` or `https://github.com/{owner}/{repo}` with no extra path. |
| `503 Service Unavailable` from POST/PUT | GitHub timed out or the network is unavailable. | Check connectivity and optionally increase `HTTP_TIMEOUT_SECONDS`. |
| GitHub rate-limit errors returning `502` | Unauthenticated GitHub API quota may be exhausted. | Set `GITHUB_TOKEN` in `.env` with a valid token. |

## Security Notes

Secrets are loaded from environment variables only. `.env` is ignored by Git, and `.env.example` contains placeholders only.
