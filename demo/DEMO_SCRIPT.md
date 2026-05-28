# Demo Video Script

Video file: `demo/rest_api_assessment_demo.mp4`

The MP4 includes on-screen captions and generated voiceover narration, so it can be submitted directly even without recording a separate walkthrough.

## Short Narration

This project is a backend REST API assessment built with FastAPI, async SQLAlchemy, PostgreSQL, and the GitHub REST API. The service accepts a GitHub repository URL or `owner/repo` identifier, validates it at the schema layer, fetches repository metadata from GitHub, stores it locally, and supports read, refresh, and delete operations through exactly four endpoints. The implementation is layered into API, service, data, schema, database, and core modules, with Alembic migrations, Docker Compose, structured logging, request IDs, retry handling, CI, and a complete test suite.

## Demo Flow

1. Show the GitHub repository link.
2. Explain the external API choice: GitHub repositories.
3. Show the architecture layers.
4. Show the four endpoint contract.
5. Demonstrate the happy path:
   - `POST /repositories` returns `201`
   - `GET /repositories/{id}` returns `200`
   - `PUT /repositories/{id}` returns `200`
   - `DELETE /repositories/{id}` returns `204`
6. Show validation and error mapping:
   - invalid input returns `422`
   - duplicates return `409`
   - missing local records return `404`
   - upstream failures return `502` or `503`
7. Show quality additions:
   - Alembic migrations
   - Docker Compose
   - structured JSON logs
   - `X-Request-ID`
   - retry/backoff
   - GitHub Actions CI
8. End with test results and the repository link.

## Submission Email Summary

I built a FastAPI REST API that stores and refreshes GitHub repository metadata using the public GitHub REST API. The service follows a layered architecture with separate API, service, data, schema, database, and core modules, and it uses async SQLAlchemy with PostgreSQL plus Alembic migrations. I added strict Pydantic validation for GitHub repository URLs and `owner/repo` identifiers, database-level duplicate protection, structured error handling, retry/backoff for transient upstream failures, Docker Compose, GitHub Actions CI, and a full test suite covering the required CRUD and error scenarios.

Repository: https://github.com/pavansai20052004-hue/rest-api-assessment
