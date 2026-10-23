"""Adapter registry — maps simulated service IDs (M1–M16) to their adapter instances."""
from typing import Protocol, runtime_checkable


@runtime_checkable
class AdapterBase(Protocol):
    service_id: str
    service_name: str

    def ping(self) -> bool: ...


_registry: dict[str, AdapterBase] = {}


def register(adapter: AdapterBase) -> None:
    _registry[adapter.service_id] = adapter


def get(service_id: str) -> AdapterBase | None:
    return _registry.get(service_id)


def all_services() -> list[str]:
    return list(_registry.keys())
