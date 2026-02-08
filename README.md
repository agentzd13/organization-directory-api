# Organization Directory API

REST API for managing and searching organizations by building, activity type, and geographic location.

---

## Quick Start (Docker)

### 1. Run the application

```bash
docker-compose up --build
The API will be available at:
http://localhost:8000

API Documentation
Swagger UI

Interactive API documentation is available at:
http://localhost:8000/docs

ReDoc

Alternative documentation is available at:
http://localhost:8000/redoc
Note: ReDoc relies on an external CDN and may not render correctly in restricted or corporate networks. Swagger UI should be used for verification.

Authentication

All API endpoints are protected by a static API key.

To access the API, include the following HTTP header in your requests:
X-API-KEY: test-secret
Example request:curl -H "X-API-KEY: test-secret" http://localhost:8000/organizations/1
Note: Swagger UI does not provide an "Authorize" button by default.
API key authentication must be performed by adding the X-API-KEY header manually when making requests.

Development (Local)
Install dependencies
pip install -r requirements.txt

Run database migrations
alembic upgrade head
Run development server
uvicorn app.main:app --reload

Tests

Run the test suite with:python -m pytest tests/ -v

