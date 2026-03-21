from __future__ import annotations

from typing import Any

from .logger import get_logger

LOGGER = get_logger(__name__)

ENTITY_ID_MAP = {
    'minecraft:zombie': 'minecraft:zombie',
    'minecraft:skeleton': 'minecraft:skeleton',
    'minecraft:creeper': 'minecraft:creeper',
    'minecraft:cow': 'minecraft:cow',
    'minecraft:item': 'minecraft:item',
}


class EntityMapper:
    def map_many(self, payload: Any) -> list[dict]:
        if not isinstance(payload, list):
            return []
        return [mapped for item in payload if (mapped := self.map_one(item))]

    def map_one(self, payload: dict[str, Any]) -> dict | None:
        identifier = str(payload.get('identifier') or payload.get('id') or payload.get('name') or '')
        if not identifier:
            return None
        if identifier == 'minecraft:item' or payload.get('Item'):
            return self._map_item_entity(payload)
        java_id = ENTITY_ID_MAP.get(identifier, identifier if identifier.startswith('minecraft:') else f'minecraft:{identifier}')
        position = payload.get('Pos') or payload.get('position') or [0.0, 0.0, 0.0]
        rotation = payload.get('Rotation') or payload.get('rotation') or [0.0, 0.0]
        return {
            'id': java_id,
            'Pos': [float(position[0]), float(position[1]), float(position[2])],
            'Rotation': [float(rotation[0]), float(rotation[1])],
            'Health': float(payload.get('Health', payload.get('health', 20.0))),
        }

    def _map_item_entity(self, payload: dict[str, Any]) -> dict:
        item_payload = payload.get('Item') or {}
        item_name = str(item_payload.get('Name') or item_payload.get('id') or 'minecraft:stone')
        if not item_name.startswith('minecraft:'):
            item_name = f'minecraft:{item_name}'
        position = payload.get('Pos') or payload.get('position') or [0.0, 0.0, 0.0]
        return {
            'id': 'minecraft:item',
            'Pos': [float(position[0]), float(position[1]), float(position[2])],
            'Rotation': [0.0, 0.0],
            'Item': {
                'id': item_name,
                'Count': int(item_payload.get('Count', item_payload.get('count', 1))),
            },
            'Age': int(payload.get('Age', 0)),
            'PickupDelay': int(payload.get('PickupDelay', 0)),
        }
