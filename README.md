# Organization Directory API

## Quick Start (Docker)

1. **Run the application**:
   ```bash
   docker-compose up --build
   ```

2. **Access Documentation**:
   - Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
   - ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

3. **Authentication**:
   - Click "Authorize" in Swagger UI.
   - Enter `test-secret` (or value from `docker-compose.yml`) in `X-API-KEY`.

## Development (Local)

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run migrations:
   (See migration verification steps)
   
3. Run server:
   ```bash
   uvicorn app.main:app --reload
   ```

## Test
Run tests with:
```bash
python -m pytest tests/ -v
```
