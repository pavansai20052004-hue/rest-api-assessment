# Submission Details: Way of Approach and Implementation Notes

## Project Title

GitHub Repository Metadata API

## Repository

https://github.com/pavansai20052004-hue/rest-api-assessment

## Demo Video

`demo/rest_api_assessment_demo.mp4`

The demo video includes captions and voiceover. It summarizes the problem statement, architecture, endpoint flow, validation/error handling, testing, and production-style additions.

## 1. Problem Understanding

The requirement was to build a backend-only REST API service that connects a local relational database with a public external API. The service needed to accept an identifier or URL, validate it strictly, fetch metadata from the external API, persist that metadata locally, and support create, read, refresh, and delete operations.

The key constraints I followed were:

- use Python 3.10+ and FastAPI
- use PostgreSQL as the main database
- keep the application async-first
- use an ORM model instead of raw table creation SQL
- separate API, service, and data layers
- validate input at the schema/model layer
- enforce uniqueness at the database level
- return the exact HTTP status codes described in the assessment
- provide tests, documentation, `.env.example`, and setup instructions

I intentionally avoided adding extra public endpoints because the assessment says the four-endpoint contract may be tested directly.

## 2. External API Selection

I selected the GitHub REST API and modeled the resource as a GitHub repository.

### Why GitHub?

- GitHub repository identifiers have a clear and testable format: `owner/repo`.
- Repository URLs are easy to validate with domain-specific rules.
- The API returns stable structured JSON.
- Public repository metadata can be fetched without a required token.
- An optional `GITHUB_TOKEN` still gives better rate limits for real-world usage.
- Repository metadata has meaningful fields for storage and refresh, such as stars, forks, open issues, default branch, language, description, visibility, and URL.

### Accepted Input Formats

```text
tiangolo/fastapi
https://github.com/tiangolo/fastapi
```

### Rejected Input Formats

```text
https://gitlab.com/team/project
https://github.com/tiangolo/fastapi/issues
git@github.com:tiangolo/fastapi.git
invalid-repository-name
```

Invalid inputs return `422 Unprocessable Entity` before any database or external API work happens.

## 3. High-Level Architecture

The codebase is organized into focused layers:

| Layer | Folder | Responsibility |
| --- | --- | --- |
| API Layer | `app/api` | FastAPI route handlers and dependency wiring |
| Schema Layer | `app/schemas` | Pydantic request validation and response models |
| Service Layer | `app/services` | Business logic, GitHub API client, and mapping logic |
| Data Layer | `app/data` | Database persistence methods |
| Database Layer | `app/db` | SQLAlchemy async engine, sessions, base model, and ORM model |
| Core Layer | `app/core` | Configuration, exception handling, request logging |
| Migration Layer | `alembic` | Versioned schema migrations |
| Tests | `tests` | Unit and integration coverage |

This structure keeps route handlers small. The route handlers do not contain database queries or external API logic; they delegate to the service layer.

## 4. Request Flow for Create Operation

For `POST /repositories`, the request flow is:

1. Client sends a GitHub repository URL or `owner/repo` identifier.
2. Pydantic validates and normalizes the input in `RepositoryCreate`.
3. If validation fails, FastAPI returns `422`.
4. The service checks whether the normalized `external_id` already exists.
5. If it already exists, the API returns `409 Conflict`.
6. The GitHub client fetches metadata with `httpx.AsyncClient`.
7. If GitHub returns `404`, the API returns `404`.
8. If GitHub returns another upstream error, the API returns `502`.
9. If the request times out or GitHub is unreachable, the API returns `503`.
10. The mapper converts GitHub JSON into an internal metadata object.
11. The data layer saves the metadata using SQLAlchemy async ORM.
12. The database unique constraint protects against race-condition duplicates.
13. The API returns `201 Created` with the stored record.

## 5. Endpoint Summary

| Method | Endpoint | Purpose | Success Code |
| --- | --- | --- | --- |
| `POST` | `/repositories` | Fetch GitHub metadata and create a local record | `201 Created` |
| `GET` | `/repositories/{id}` | Read a stored local record | `200 OK` |
| `PUT` | `/repositories/{id}` | Refresh stored metadata from GitHub | `200 OK` |
| `DELETE` | `/repositories/{id}` | Delete a stored local record | `204 No Content` |

## 6. Status Code Handling

| Status | Scenario |
| --- | --- |
| `200 OK` | Successful read or refresh |
| `201 Created` | Successful create |
| `204 No Content` | Successful delete |
| `404 Not Found` | Local record not found or GitHub repository not found |
| `409 Conflict` | Duplicate repository already exists |
| `422 Unprocessable Entity` | Request body or identifier validation failed |
| `502 Bad Gateway` | GitHub returned an upstream error |
| `503 Service Unavailable` | GitHub timed out or could not be reached |

## 7. Database Design

The main table is `repositories`.

Important columns:

- `id`: database primary key
- `external_id`: normalized unique repository identifier such as `tiangolo/fastapi`
- `owner`: repository owner or organization
- `name`: repository name
- `full_name`: GitHub full name
- `html_url`: GitHub repository URL
- `description`: repository description
- `stars`, `forks`, `open_issues`: selected metadata fields
- `default_branch`, `language`, `visibility`: additional useful metadata
- `raw_metadata`: original GitHub JSON payload
- `created_at`, `updated_at`, `last_fetched_at`: timestamps

The uniqueness requirement is enforced with the database constraint:

```text
uq_repositories_external_id
```

## 8. Configuration and Security

All runtime configuration is loaded from environment variables using Pydantic Settings.

Important variables:

- `DATABASE_URL`
- `GITHUB_API_BASE_URL`
- `GITHUB_TOKEN`
- `HTTP_TIMEOUT_SECONDS`
- `GITHUB_MAX_RETRIES`
- `GITHUB_RETRY_BACKOFF_SECONDS`
- `DATABASE_AUTO_CREATE`
- `LOG_LEVEL`
- `LOG_JSON`

Security choices:

- No real tokens or passwords are committed.
- `.env` is ignored by Git.
- `.env.example` contains placeholders only.
- GitHub token usage is optional and environment-based.

## 9. Production-Style Improvements Added

Beyond the minimum requirements, I added:

- Alembic migrations for versioned database schema setup.
- Docker Compose to run the API and PostgreSQL together.
- GitHub Actions CI to run tests automatically.
- Structured JSON logs for request observability.
- `X-Request-ID` headers for tracing requests.
- Retry/backoff for transient GitHub API failures.
- A detailed README with setup, API reference, testing, assumptions, and troubleshooting.
- A demo video and written approach documentation.

These additions improve evaluator confidence while still keeping the public API limited to the required CRUD endpoints.

## 10. Testing Approach

The project has both unit and integration tests.

### Unit Tests

Unit tests cover:

- valid GitHub identifier parsing
- invalid input categories
- missing field validation
- GitHub JSON mapping
- duplicate detection logic
- GitHub client retry handling
- `502` and `503` exception mapping

### Integration Tests

Integration tests cover:

- successful create returns `201`
- duplicate create returns `409`
- invalid create returns `422`
- existing read returns `200`
- missing read returns `404`
- existing refresh returns `200`
- missing refresh returns `404`
- existing delete returns `204`
- missing delete returns `404`
- external unavailable returns `503`
- external upstream error returns `502`
- request ID header is returned

External GitHub calls are mocked in tests. This keeps the test suite deterministic and avoids real network dependency.

## 11. Trade-Offs

- I used GitHub repositories only, instead of multiple resource types, to keep the domain focused and easy to test.
- I used SQLite only for isolated tests; PostgreSQL remains the intended runtime database.
- I disabled FastAPI docs endpoints because the assessment requested exactly four API endpoints.
- I kept refresh as an overwrite operation on the same local record, because the requirement says to update stored metadata for the same resource.
- I stored `raw_metadata` in JSON so future fields can be inspected without schema changes, while still exposing normalized response fields.

## 12. Future Improvements

If this were extended beyond the assessment, the next improvements would be:

- pagination/list endpoint for stored repositories
- authenticated API access for clients
- rate-limit response handling with `Retry-After`
- observability with OpenTelemetry
- deployment configuration for Render, Fly.io, or AWS
- background refresh jobs for scheduled metadata updates

## 13. Ready-To-Send Explanation

You can send this response:

> I built a FastAPI REST API that stores and refreshes GitHub repository metadata using the public GitHub REST API. My approach was to keep the required four-endpoint contract clean while separating the code into API, schema, service, data, database, and core layers. Input validation happens at the Pydantic schema layer before database or network I/O, GitHub calls use async `httpx` with timeout and retry handling, and duplicate records are protected by a database-level unique constraint. I used async SQLAlchemy with PostgreSQL, Alembic migrations, Docker Compose, structured JSON logging, request ID tracing, GitHub Actions CI, and a full unit/integration test suite covering success and error scenarios. I also included a demo video, demo script, README, and detailed approach documentation in the repository.

Repository:

```text
https://github.com/pavansai20052004-hue/rest-api-assessment
```

Demo video:

```text
demo/rest_api_assessment_demo.mp4
```

Approach document:

```text
docs/SUBMISSION_DETAILS.md
```
