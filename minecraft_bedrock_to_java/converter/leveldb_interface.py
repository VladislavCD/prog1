from __future__ import annotations

import importlib
import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from .logger import get_logger

LOGGER = get_logger(__name__)


@dataclass(frozen=True)
class LevelDBBackend:
    name: str
    open_callable: callable


class LevelDBWrapper:
    def __init__(self, backend_name: str, db_object) -> None:
        self.backend_name = backend_name
        self._db = db_object

    def __enter__(self) -> 'LevelDBWrapper':
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        close = getattr(self._db, 'close', None)
        if callable(close):
            close()

    def __iter__(self) -> Iterator[tuple[bytes, bytes]]:
        if hasattr(self._db, 'iterator'):
            iterator = self._db.iterator(include_value=True)
            for key, value in iterator:
                yield bytes(key), bytes(value)
            return
        if hasattr(self._db, 'RangeIter'):
            for key, value in self._db.RangeIter():
                yield bytes(key), bytes(value)
            return
        for key, value in self._db:
            yield bytes(key), bytes(value)


class LevelDBFactory:
    def create(self, db_path: Path) -> LevelDBWrapper:
        backend = self._select_backend()
        LOGGER.info('Opening LevelDB with backend: %s', backend.name)
        return backend.open_callable(db_path)

    def _select_backend(self) -> LevelDBBackend:
        if importlib.util.find_spec('plyvel') is not None:
            module = importlib.import_module('plyvel')
            return LevelDBBackend('plyvel', lambda path: LevelDBWrapper('plyvel', module.DB(str(path), create_if_missing=False)))
        if importlib.util.find_spec('leveldb') is not None:
            module = importlib.import_module('leveldb')
            return LevelDBBackend('leveldb', lambda path: LevelDBWrapper('leveldb', module.LevelDB(str(path))))
        raise RuntimeError(
            'No supported LevelDB backend installed. Install `plyvel` on Linux/macOS or `leveldb`/`plyvel-wheels` on Windows.'
        )
