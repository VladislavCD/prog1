from __future__ import annotations

import json
from dataclasses import dataclass

from .logger import get_logger

LOGGER = get_logger(__name__)

BEDROCK_BIOME_ID_MAP = {
    0: 'minecraft:ocean',
    1: 'minecraft:plains',
    2: 'minecraft:desert',
    3: 'minecraft:windswept_hills',
    4: 'minecraft:forest',
    5: 'minecraft:taiga',
    6: 'minecraft:swamp',
    7: 'minecraft:river',
    8: 'minecraft:nether_wastes',
    9: 'minecraft:the_end',
    10: 'minecraft:frozen_ocean',
    11: 'minecraft:frozen_river',
    12: 'minecraft:snowy_plains',
    13: 'minecraft:snowy_mountains',
    14: 'minecraft:mushroom_fields',
    16: 'minecraft:beach',
    21: 'minecraft:jungle',
    27: 'minecraft:birch_forest',
    35: 'minecraft:savanna',
    41: 'minecraft:badlands',
}


@dataclass(frozen=True)
class BiomeVolume:
    values: list[str]


class BiomeMapper:
    def decode_biomes(self, raw: bytes) -> BiomeVolume:
        if not raw:
            return BiomeVolume(['minecraft:plains'] * 64)
        if raw[:1] in {b'{', b'['}:
            return self._decode_json_biomes(raw)
        if len(raw) >= 256:
            return self._decode_2d_ids(raw)
        return BiomeVolume(['minecraft:plains'] * 64)

    def _decode_json_biomes(self, raw: bytes) -> BiomeVolume:
        payload = json.loads(raw.decode('utf-8'))
        ids = payload.get('3d_ids') or payload.get('2d_ids') or []
        if ids:
            return self._ids_to_volume(ids)
        names = payload.get('names') or []
        normalized = [self._normalize_name(name) for name in names[:64]]
        while len(normalized) < 64:
            normalized.append('minecraft:plains')
        return BiomeVolume(normalized)

    def _decode_2d_ids(self, raw: bytes) -> BiomeVolume:
        ids = list(raw[:256])
        sampled: list[int] = []
        for z in range(0, 16, 4):
            for y in range(4):
                for x in range(0, 16, 4):
                    sampled.append(ids[(z * 16) + x])
        return self._ids_to_volume(sampled)

    def _ids_to_volume(self, ids: list[int]) -> BiomeVolume:
        normalized = [BEDROCK_BIOME_ID_MAP.get(int(biome_id), 'minecraft:plains') for biome_id in ids[:64]]
        while len(normalized) < 64:
            normalized.append('minecraft:plains')
        return BiomeVolume(normalized)

    def _normalize_name(self, value: str) -> str:
        if value.startswith('minecraft:'):
            return value
        if value:
            return f'minecraft:{value}'
        LOGGER.debug('Unknown biome name payload %r, falling back to plains', value)
        return 'minecraft:plains'
