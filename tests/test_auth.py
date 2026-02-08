import pytest
from httpx import AsyncClient
from app.main import app
from app.config import settings

@pytest.mark.asyncio
async def test_health_check_public(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_protected_route_missing_key(client):
    # Requesting a made-up path to trigger middleware
    response = await client.get("/some-protected-route")
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing API Key"}

@pytest.mark.asyncio
async def test_protected_route_wrong_key(client):
    response = await client.get("/some-protected-route", headers={"X-API-KEY": "wrong-key"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_protected_route_correct_key(client):
    # Should be 404 because route doesn't exist, NOT 401
    response = await client.get("/some-protected-route", headers={"X-API-KEY": settings.STATIC_API_KEY})
    assert response.status_code == 404
