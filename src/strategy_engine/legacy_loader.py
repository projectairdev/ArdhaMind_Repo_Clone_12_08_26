from __future__ import annotations

from src.strategy_engine.legacy_base import BaseStrategy

_STRATEGY_REGISTRY: dict[str, BaseStrategy] = {}


def register_strategy(name: str, strategy: BaseStrategy) -> None:
    _STRATEGY_REGISTRY[name] = strategy


def get_strategy(name: str) -> BaseStrategy:
    if name not in _STRATEGY_REGISTRY:
        raise KeyError(f"Strategy '{name}' is not registered.")
    return _STRATEGY_REGISTRY[name]


def list_strategies() -> list[str]:
    return list(_STRATEGY_REGISTRY.keys())
