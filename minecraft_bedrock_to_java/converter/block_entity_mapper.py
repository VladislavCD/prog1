from __future__ import annotations

from typing import Any

from .logger import get_logger

LOGGER = get_logger(__name__)


class BlockEntityMapper:
    def map_many(self, payload: Any, chunk_x: int, chunk_z: int) -> list[dict]:
        if not isinstance(payload, list):
            return []
        return [mapped for item in payload if (mapped := self.map_one(item, chunk_x, chunk_z))]

    def map_one(self, payload: dict[str, Any], chunk_x: int, chunk_z: int) -> dict | None:
        identifier = str(payload.get('id') or payload.get('name') or '').lower()
        if not identifier:
            return None
        if 'chest' in identifier:
            return self._map_chest(payload)
        if 'furnace' in identifier or 'smoker' in identifier or 'blast_furnace' in identifier:
            return self._map_furnace_like(payload, identifier)
        LOGGER.debug('Unsupported block entity type %s', identifier)
        return None

    def _map_chest(self, payload: dict[str, Any]) -> dict:
        items = [self._map_item(item) for item in payload.get('Items', []) if isinstance(item, dict)]
        return {
            'id': 'minecraft:chest',
            'x': int(payload.get('x', 0)),
            'y': int(payload.get('y', 0)),
            'z': int(payload.get('z', 0)),
            'keepPacked': 0,
            'Items': items,
        }

    def _map_furnace_like(self, payload: dict[str, Any], identifier: str) -> dict:
        java_id = 'minecraft:furnace'
        if 'smoker' in identifier:
            java_id = 'minecraft:smoker'
        elif 'blast' in identifier:
            java_id = 'minecraft:blast_furnace'
        return {
            'id': java_id,
            'x': int(payload.get('x', 0)),
            'y': int(payload.get('y', 0)),
            'z': int(payload.get('z', 0)),
            'BurnTime': int(payload.get('BurnTime', 0)),
            'CookTime': int(payload.get('CookTime', 0)),
            'CookTimeTotal': int(payload.get('CookTimeTotal', 200)),
            'Items': [self._map_item(item) for item in payload.get('Items', []) if isinstance(item, dict)],
        }

    def _map_item(self, payload: dict[str, Any]) -> dict:
        raw_name = str(payload.get('Name') or payload.get('id') or 'minecraft:air')
        item_name = raw_name if raw_name.startswith('minecraft:') else f'minecraft:{raw_name}'
        return {
            'id': item_name,
            'Count': int(payload.get('Count', payload.get('count', 1))),
            'Slot': int(payload.get('Slot', payload.get('slot', 0))),
        }
