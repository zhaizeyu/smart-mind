from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    try:
        import tomli as tomllib  # type: ignore
    except ModuleNotFoundError:  # pragma: no cover
        tomllib = None  # type: ignore

CONFIG_PATH = Path(__file__).resolve().parent / "config.toml"
DEFAULT_CONFIG = {
    "ai": {
        "provider": "echo",
        "base_url": "",
        "api_key": "",
        "model": "gpt-4o-mini",
        "headers": {},
    }
}


def _parse_value(value: str) -> Any:
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def _simple_toml_load(text: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    current: Dict[str, Any] = data
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            if not section:
                continue
            current = data.setdefault(section, {})
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        value = value.split("#", 1)[0].strip()
        current[key] = _parse_value(value)
    return data


def _load_from(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    if tomllib is not None:
        with path.open("rb") as fp:
            return tomllib.load(fp)
    # Fallback：简单解析器，支持当前配置格式
    return _simple_toml_load(path.read_text(encoding="utf-8"))


def load_ai_config() -> Dict[str, Any]:
    data = DEFAULT_CONFIG.copy()
    config = _load_from(CONFIG_PATH)
    if config:
        data.update(config)
    return data.get("ai", {})
