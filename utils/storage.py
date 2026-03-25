"""
utils/storage.py  ·  Persistência leve via JSON
Sem banco de dados externo — compatível com qualquer plano ShardCloud.
Cache em memória com lazy-load para economizar RAM.
"""

from __future__ import annotations
import json
import os
import asyncio
import logging
from typing import Any, Optional

log = logging.getLogger("futaba.storage")

DATA_DIR = os.environ.get("DATA_DIR", "data")


def _path(filename: str) -> str:
    os.makedirs(DATA_DIR, exist_ok=True)
    return os.path.join(DATA_DIR, filename)


class Store:
    """
    Key-value store com cache em memória + flush assíncrono para disco.
    Cada instância gerencia um único arquivo .json.
    """

    __slots__ = ("_file", "_data", "_dirty", "_lock")

    def __init__(self, filename: str) -> None:
        self._file  = _path(filename)
        self._data: dict = {}
        self._dirty = False
        self._lock  = asyncio.Lock()
        self._load()

    # ── I/O ──────────────────────────────────────────────────────
    def _load(self) -> None:
        if os.path.exists(self._file):
            try:
                with open(self._file, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except Exception as e:
                log.warning(f"Falha ao ler {self._file}: {e}  — iniciando vazio")
                self._data = {}

    async def save(self) -> None:
        if not self._dirty:
            return
        async with self._lock:
            try:
                tmp = self._file + ".tmp"
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(self._data, f, ensure_ascii=False, indent=2)
                os.replace(tmp, self._file)
                self._dirty = False
            except Exception as e:
                log.error(f"Falha ao salvar {self._file}: {e}")

    # ── API ───────────────────────────────────────────────────────
    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        self._dirty = True

    def delete(self, key: str) -> None:
        if key in self._data:
            del self._data[key]
            self._dirty = True

    def all(self) -> dict:
        return dict(self._data)

    def __contains__(self, key: str) -> bool:
        return key in self._data


# ── Instâncias globais (singleton por arquivo) ───────────────────
_stores: dict[str, Store] = {}


def get_store(name: str) -> Store:
    if name not in _stores:
        _stores[name] = Store(f"{name}.json")
    return _stores[name]


async def flush_all() -> None:
    """Salva todos os stores modificados — chamar no on_close."""
    for store in _stores.values():
        await store.save()
