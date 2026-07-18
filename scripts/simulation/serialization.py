"""シミュレーションの不変モデルを JSON 互換値へ変換する純粋関数。"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Mapping


def to_json_compatible(value: Any) -> Any:
    """dataclass、時刻、Decimal、Mapping を精度を失わず再帰変換する。"""
    if is_dataclass(value) and not isinstance(value, type):
        return {item.name: to_json_compatible(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, Enum):
        return to_json_compatible(value.value)
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): to_json_compatible(item) for key, item in value.items()}
    if isinstance(value, frozenset | set):
        return sorted(
            (to_json_compatible(item) for item in value),
            key=lambda item: repr(item),
        )
    if isinstance(value, tuple | list):
        return [to_json_compatible(item) for item in value]
    return value
