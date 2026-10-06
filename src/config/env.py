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
