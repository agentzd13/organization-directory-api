from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.config import settings
from app.routers import organizations

app = FastAPI(title="Organization Directory API")

app.include_router(organizations.router)

HIDDEN_PATHS = {"/docs", "/redoc", "/openapi.json", "/health"}

@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    # Allow exact match or with trailing slash for better UX
    path = request.url.path.rstrip("/")
    if path in HIDDEN_PATHS or request.url.path == "/openapi.json": 
        # openapi.json usually doesn't have trailing slash but to be safe
        # actually rstrip handles it.
        return await call_next(request)
    
    # Also allow strict equality or prefix if needed? Task implies "all other endpoints".
    # Docs are usually exact paths.
    
    api_key = request.headers.get("X-API-KEY")
    if api_key != settings.STATIC_API_KEY:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid or missing API Key"}
        )
    
    return await call_next(request)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
