"""TDD: Tests for Ollama manager endpoints (pull, delete, list models)."""
from __future__ import annotations

from unittest.mock import patch, AsyncMock, Mock


def _make_async_client_mock(response_data, status=200):
    """Mock httpx.AsyncClient so its get() returns controlled data."""
    from unittest.mock import Mock
    mock_resp = Mock(spec=["json", "raise_for_status"])
    mock_resp.status_code = status
    mock_resp.json = Mock(return_value=response_data)
    mock_resp.raise_for_status = Mock()

    async def mock_get(*args, **kwargs):
        return mock_resp

    mock_client = Mock(spec=["get", "__aenter__", "__aexit__"])
    mock_client.get = mock_get
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock()
    return mock_client


def test_list_models_returns_details(client):
    """GET /settings/models returns model objects with size/details."""
    with patch("routes.settings.AsyncClient", return_value=_make_async_client_mock({
        "models": [
            {"name": "gemma3:4b", "size": 4_000_000_000,
             "details": {"parameter_size": "4B", "quantization_level": "Q4_K_M"}},
            {"name": "deepseek-r1:8b", "size": 25_000_000_000,
             "details": {"parameter_size": "8.2B", "quantization_level": "Q4_K_M"}},
        ]
    })):
        r = client.get("/api/settings/models?provider=ollama&base_url=http://localhost:11434")
        assert r.status_code == 200
        data = r.json()
        assert len(data["models"]) == 2
        first = data["models"][0]
        assert first["name"] == "deepseek-r1:8b"
        assert first["size"] == 25_000_000_000
        assert first["parameter_size"] == "4B"
        assert first["quantization"] == "Q4_K_M"


def test_list_models_empty(client):
    """GET /settings/models returns empty list when no models."""
    with patch("routes.settings.AsyncClient", return_value=_make_async_client_mock({"models": []})):
        r = client.get("/api/settings/models?provider=ollama&base_url=http://localhost:11434")
        assert r.status_code == 200
        assert r.json()["models"] == []


def test_list_models_error(client):
    """GET /settings/models returns error when Ollama is unreachable."""
    async def mock_get(*args, **kwargs):
        raise Exception("Connection refused")
    mock_client = Mock(spec=["get", "__aenter__", "__aexit__"])
    mock_client.get = mock_get
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock()
    with patch("routes.settings.AsyncClient", return_value=mock_client):
        r = client.get("/api/settings/models?provider=ollama&base_url=http://localhost:11434")
        assert r.status_code == 200
        data = r.json()
        assert data["models"] == []
        assert "error" in data


def test_pull_model_success(client):
    """POST /settings/models/pull calls ollama pull and returns success."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "pulling manifest"
        mock_run.return_value.stderr = ""

        r = client.post("/api/settings/models/pull", json={"name": "gemma3:1b"})
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert "Pulled" in data["message"]


def test_pull_model_failure(client):
    """POST /settings/models/pull returns error when ollama fails."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "model not found"
        mock_run.return_value.stdout = ""

        r = client.post("/api/settings/models/pull", json={"name": "nonexistent:99b"})
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is False
        assert "model not found" in data["error"]


def test_pull_model_missing_name(client):
    """POST /settings/models/pull requires a name."""
    r = client.post("/api/settings/models/pull", json={"name": ""})
    assert r.status_code == 400


def test_pull_model_no_ollama(client):
    """POST /settings/models/pull handles missing ollama binary."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError()
        r = client.post("/api/settings/models/pull", json={"name": "gemma3:1b"})
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is False
        assert "PATH" in data["error"]


def test_pull_model_timeout(client):
    """POST /settings/models/pull handles subprocess timeout."""
    from subprocess import TimeoutExpired
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = TimeoutExpired("ollama pull", 300)
        r = client.post("/api/settings/models/pull", json={"name": "big-model:70b"})
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is False
        assert "timed out" in data["error"].lower()


def test_delete_model_success(client):
    """DELETE /settings/models/{name} calls ollama rm and returns success."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "deleted"
        mock_run.return_value.stderr = ""

        r = client.delete("/api/settings/models/gemma3:4b")
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert "Deleted" in data["message"]


def test_delete_model_failure(client):
    """DELETE /settings/models/{name} returns error when ollama rm fails."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "model not found"

        r = client.delete("/api/settings/models/nonexistent")
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is False
        assert "model not found" in data["error"]
