import pytest
import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db
from app.main import app

# --- Test Setup ---
# Настройки тестовой базы данных
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создать таблицы в тестовой БД
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

# Очистить тестовую БД перед каждым тестом
@pytest.fixture(autouse=True, scope="function")
def prepare():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return

# Регистрируем пользователя и получаем токен для авторизации
@pytest.fixture
def auth_header():
    client.post(
        "/users/register",
        json={
            "email": "user@test.com", 
            "password": "pass123", 
            "risk_tolerance": 0.5
            }
    )
    login_resp = client.post(
        "/users/token",
        json={
            "email": "user@test.com", 
            "password": "pass123"
            }
    )
    token = login_resp.json().get("access_token")
    return { "Authorization": f"Bearer {token}" }

# --- Tests ---

def test_user_registration_and_login():
    # Регистрация пользователя
    resp = client.post(
        "/users/register",
        json={
            "email": "user.registration@test.com", 
            "password": "pass123", 
            "risk_tolerance": 0.2
            }
    )
    assert resp.status_code == 201

    # Авторизация пользователя
    resp = client.post(
        "/users/token",
        json={
            "email": "user.registration@test.com", 
            "password": "pass123"
            }
    )
    assert resp.status_code == 200
    data = resp.json()

    # Проверка наличия токена в ответе
    assert "access_token" in data

def test_assets_crud(auth_header):
    # Создание нового актива
    payload = {
        "symbol": "btc_test", 
        "type": "crypto", 
        "volatility": 0.5, 
        "expected_return": 0.1
        }
    resp = client.post("/assets", json=payload, headers=auth_header)
    assert resp.status_code == 201

    # Получение актива по ID
    asset = resp.json()
    asset_id = asset.get("id")
    resp = client.get(f"/assets/{asset_id}", headers=auth_header)
    assert resp.status_code == 200

    # Список всех активов
    resp = client.get("/assets", headers=auth_header)
    symbols = [a.get("symbol") for a in resp.json()]
    assert "btc_test" in symbols


def test_portfolio_crud(auth_header):
    # Создание активов
    sym1 = "asset1"
    sym2 = "asset2"
    r1 = client.post(
        "/assets",
        json={
            "symbol": sym1, 
            "type": "crypto", 
            "volatility": 0.5, 
            "expected_return": 0.1
            },
        headers=auth_header
    ).json()
    r2 = client.post(
        "/assets",
        json={
            "symbol": sym2, 
            "type": "fiat", 
            "volatility": 0.1, 
            "expected_return": 0.01
            },
        headers=auth_header
    ).json()

    # Создание портфеля
    payload = {
        "name": "TestPortf",
        "assets": [
            {
                "asset_id": r1["id"], 
                "target_pct": 0.6, 
                "quantity": 1.0
            },
            {
                "asset_id": r2["id"], 
                "target_pct": 0.4, 
                "quantity": 100.0
            }
        ]
    }
    resp = client.post("/portfolios", json=payload, headers=auth_header)
    assert resp.status_code == 201
    port = resp.json()
    port_id = port.get("id")
    assert port.get("name") == "TestPortf"
    assert len(port.get("assets")) == 2

    # Обновление портфеля
    updated = payload.copy()
    updated["name"] = "UpdatedName"
    resp = client.put(f"/portfolios/{port_id}", json=updated, headers=auth_header)
    assert resp.status_code == 200
    assert resp.json().get("name") == "UpdatedName"

    # Удаление портфеля
    print(port_id)
    resp = client.delete(f"/portfolios/{port_id}", headers=auth_header)
    assert resp.status_code == 204


def test_rebalance_endpoint(auth_header):
    # Создание активов
    sym1 = "bitcoin"
    sym2 = "usd"
    r1 = client.post(
        "/assets", 
        json={
            "symbol": sym1, 
            "type": "crypto", 
            "volatility": 0.5, 
            "expected_return": 0.1
        }, 
        headers=auth_header).json()
    r2 = client.post(
        "/assets", 
        json={
            "symbol": sym2, 
            "type": "fiat", 
            "volatility": 0.1, 
            "expected_return": 0.01
        }, 
        headers=auth_header).json()
    # Создание портфеля
    payload = {
        "name": "TestPortf",
        "assets": [
            {
                "asset_id": r1["id"], 
                "target_pct": 0.5, 
                "quantity": 1.0
            },
            {
                "asset_id": r2["id"], 
                "target_pct": 0.5, 
                "quantity": 1.0
            }
        ]
    }
    port = client.post("/portfolios", json=payload, headers=auth_header).json()
    port_id = port["id"]
    assert port.get("assets")[0].get("quantity") == 1.0

    resp = client.post(f"/portfolios/{port_id}/rebalance?days=5", headers=auth_header)
    assert resp.status_code == 200
