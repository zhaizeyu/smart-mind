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

CONFIG_PATH = Path(__file__).resolve().parent / 'config.toml'
ROOT_CONFIG_PATH = Path(__file__).resolve().parents[1] / 'config.toml'
DEFAULT_CONFIG = {
    'ai': {
        'provider': 'echo',
        'base_url': '',
        'api_key': '',
        'model': 'gpt-4o-mini',
        'headers': {}
    }
}


def _load_from(path: Path) -> Dict[str, Any]:
    if tomllib is None or not path.exists():
        return {}
    with path.open('rb') as fp:
        return tomllib.load(fp)


def load_ai_config() -> Dict[str, Any]:
    data = DEFAULT_CONFIG.copy()
    for candidate in (CONFIG_PATH, ROOT_CONFIG_PATH):
        config = _load_from(candidate)
        if config:
            data.update(config)
            break
    return data.get('ai', {})
