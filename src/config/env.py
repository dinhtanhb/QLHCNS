"""Small, dependency-free helpers for parsing deployment environment values."""

import os
from collections.abc import Mapping


TRUE_VALUES = frozenset(("true", "1", "t"))


def env_flag(name: str, default: str = "False", environ: Mapping[str, str] | None = None) -> bool:
    """Return a predictable boolean for an environment setting.

    Empty, unknown, and explicitly false values disable the flag.  ``environ``
    makes the parsing rule testable without reloading Django settings.
    """
    values = os.environ if environ is None else environ
    return str(values.get(name, default)).strip().lower() in TRUE_VALUES


def env_choice(name: str, choices: tuple[str, ...], default: str,
               environ: Mapping[str, str] | None = None) -> tuple[str, str | None]:
    """Return ``(value, invalid_raw)`` for an environment setting with fixed choices.

    Empty/unset returns ``default``. A value outside ``choices`` returns
    ``default`` together with the raw value so the caller can log a warning.
    """
    values = os.environ if environ is None else environ
    raw = str(values.get(name, "")).strip().lower()
    if not raw:
        return default, None
    return (raw, None) if raw in choices else (default, raw)
