# Way of Approach

## 1. Requirement Interpretation

The assessment asks for a backend-only REST API that bridges a local PostgreSQL database with a public external API. I treated the fixed requirements as the boundary of the solution:

- exactly four REST endpoints for create, read, refresh, and delete
- schema-level validation before database or network calls
- async FastAPI endpoints, async database I/O, and async external HTTP calls
- database-level uniqueness enforcement
- predictable status codes for success, validation, duplicate, missing, upstream, and timeout cases
- runnable tests and complete README documentation

I avoided adding extra public API endpoints, dashboards, or UI features because the assessment explicitly says those are not evaluated and the endpoint contract may be tested directly.

## 2. External API Choice

I selected the GitHub REST API and focused the domain on GitHub repositories.

Reasons:

- GitHub repository identifiers have a clear format: `owner/repo`.
- GitHub repository URLs support strong domain-specific validation.
- Public repository metadata is structured JSON and stable.
- The API works without a mandatory token, while `GITHUB_TOKEN` can be used for higher rate limits.
- Repository metadata has useful fields for storage and refresh: stars, forks, issues, language, default branch, visibility, and description.

The service accepts either:

```text
tiangolo/fastapi
https://github.com/tiangolo/fastapi
```

It rejects non-GitHub domains, malformed identifiers, SSH-style URLs, and URLs pointing to subresources such as issues or pull requests.

## 3. Architecture

The project uses a layered structure so each part has one clear responsibility.

```text
app/
  api/        FastAPI route handlers and dependency wiring
  schemas/    Pydantic request, response, and internal DTO models
  services/   Business logic, GitHub client, and metadata mapping
  data/       Persistence operations against SQLAlchemy sessions
  db/         Engine, session factory, ORM base, and ORM models
  core/       Settings, exception handling, and structured logging
alembic/      Versioned database migrations
tests/        Unit and integration tests
```

## 4. POST Request Data Flow

1. FastAPI receives `POST /repositories`.
2. Pydantic validates and normalizes the `identifier` field.
3. Invalid input returns `422` before any database or GitHub call is made.
4. The service checks whether the repository already exists locally.
5. Duplicate records return `409`.
6. The async GitHub client fetches repository metadata with timeout and bounded retry handling.
7. GitHub `404` maps to API `404`.
8. Other GitHub upstream errors map to `502`.
9. Network failures and timeouts map to `503`.
10. The data layer persists the mapped metadata with SQLAlchemy async ORM.
11. The database unique constraint is the final protection against duplicates.
12. The API returns `201 Created` with the stored record.

## 5. Endpoint Contract

The public API surface intentionally contains only the four required endpoints.

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/repositories` | Fetch GitHub metadata and store a new local record. |
| `GET` | `/repositories/{id}` | Read a stored record by local database ID. |
| `PUT` | `/repositories/{id}` | Refresh a stored record from GitHub. |
| `DELETE` | `/repositories/{id}` | Delete a stored record. |

## 6. Error Handling Strategy

The application uses explicit domain exceptions and a global exception handler so route handlers stay clean.

| Case | Returned status |
| --- | --- |
| Successful read or refresh | `200 OK` |
| Successful create | `201 Created` |
| Successful delete | `204 No Content` |
| Local record missing | `404 Not Found` |
| GitHub resource missing | `404 Not Found` |
| Duplicate local repository | `409 Conflict` |
| Invalid request body | `422 Unprocessable Entity` |
| GitHub upstream failure | `502 Bad Gateway` |
| GitHub timeout/network failure | `503 Service Unavailable` |

## 7. Database Design

The `repositories` table stores both normalized fields and the original upstream JSON.

Important fields:

- `id`: local primary key
- `external_id`: unique GitHub identifier such as `tiangolo/fastapi`
- `owner`, `name`, `full_name`, `html_url`
- metadata fields such as stars, forks, issues, language, visibility, and default branch
- `raw_metadata`: JSON copy of the upstream response
- `created_at`, `updated_at`, `last_fetched_at`

Uniqueness is enforced at the database level with `uq_repositories_external_id`.

## 8. Production-Style Additions

To make the project stronger than the minimum requirements, I added:

- Alembic migrations for repeatable schema setup.
- Docker Compose for a one-command API plus PostgreSQL environment.
- GitHub Actions CI that runs the test suite on push and pull request.
- Structured JSON request logging.
- `X-Request-ID` response headers for traceability.
- Bounded retry/backoff for transient GitHub failures.
- A detailed README with setup, API reference, assumptions, troubleshooting, and design decisions.

## 9. Testing Strategy

The test suite is split into unit and integration coverage.

Unit tests cover:

- valid and invalid identifier parsing
- missing-field schema validation
- GitHub JSON to internal metadata mapping
- duplicate detection logic without real I/O
- GitHub client retry and error mapping

Integration tests cover:

- successful `POST`
- duplicate `POST`
- invalid-input `POST`
- successful `GET`
- missing-record `GET`
- successful `PUT`
- missing-record `PUT`
- successful `DELETE`
- missing-record `DELETE`
- external `502` and `503` paths
- request ID response header behavior

All external API calls are mocked in tests, and the integration tests use isolated in-memory SQLite so they are fast and deterministic.

## 10. Trade-Offs and Assumptions

- I did not add a frontend because the assessment is backend-only.
- I disabled FastAPI docs routes so automated evaluators see only the required four API endpoints.
- SQLite is used only in tests; the real runtime configuration is PostgreSQL.
- I kept refresh as an overwrite operation on the same local ID because that best matches the requirement to update stored metadata.
- I used GitHub repositories only, not GitHub users, gists, issues, or pull requests, to keep the API focused and easy to evaluate.
