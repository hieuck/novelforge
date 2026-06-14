import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from pydantic import ValidationError

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except Exception:  # pragma: no cover - fallback when pydantic-settings is missing
    try:
        from pydantic import BaseSettings
        SettingsConfigDict = dict  # type: ignore[misc,assignment]
    except Exception as exc:  # pragma: no cover
        raise ImportError("Pydantic is required for application settings") from exc

logger = logging.getLogger(__name__)


class ServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NOVELFORGE_", extra="ignore")

    environment: str = "development"
    log_level: str = "INFO"
    default_locale: str = "vi"


_service_settings: Optional[ServiceSettings] = None


def get_service_settings() -> ServiceSettings:
    global _service_settings
    if _service_settings is None:
        _service_settings = ServiceSettings()
    return _service_settings


def reset_service_settings() -> None:
    global _service_settings
    _service_settings = None
