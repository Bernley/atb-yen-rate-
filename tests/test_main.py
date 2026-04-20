import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import main as main_module


@pytest.fixture(autouse=True)
def reset_cache():
    main_module._cache["rate"] = None
    main_module._cache["updated_at"] = 0.0
    main_module._cache["error"] = False
    yield


@pytest.fixture
def client():
    return TestClient(main_module.app)


def test_index_returns_200(client):
    with patch("main.get_jpy_buy_rate", return_value=46.22):
        response = client.get("/")
    assert response.status_code == 200


def test_index_contains_rate(client):
    with patch("main.get_jpy_buy_rate", return_value=46.22):
        response = client.get("/")
    assert "46.22" in response.text


def test_index_shows_error_message_on_parse_failure(client):
    with patch("main.get_jpy_buy_rate", side_effect=Exception("network error")):
        response = client.get("/")
    assert response.status_code == 200
    assert "Не удалось получить курс" in response.text
