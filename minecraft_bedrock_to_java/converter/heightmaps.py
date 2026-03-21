from __future__ import annotations

from minecraft_bedrock_to_java.config import HEIGHTMAP_BITS_PER_ENTRY, HEIGHTMAP_LONG_COUNT
from .world_model import Block, Chunk

NON_MOTION_BLOCKING = {
    'minecraft:air',
    'minecraft:cave_air',
    'minecraft:void_air',
    'minecraft:short_grass',
    'minecraft:tall_grass',
    'minecraft:fern',
    'minecraft:water',
    'minecraft:lava',
}

WORLD_SURFACE_IGNORED = {
    'minecraft:air',
    'minecraft:cave_air',
    'minecraft:void_air',
}


class HeightmapCalculator:
    def compute(self, chunk: Chunk) -> dict[str, list[int]]:
        world_surface = []
        motion_blocking = []
        for z in range(16):
            for x in range(16):
                world_surface.append(self._column_top(chunk, x, z, mode='world_surface'))
                motion_blocking.append(self._column_top(chunk, x, z, mode='motion_blocking'))
        return {
            'WORLD_SURFACE': self._pack(world_surface),
            'MOTION_BLOCKING': self._pack(motion_blocking),
        }

    def _column_top(self, chunk: Chunk, x: int, z: int, mode: str) -> int:
        for section_y in sorted(chunk.sections.keys(), reverse=True):
            section = chunk.sections[section_y]
            for local_y in range(15, -1, -1):
                block = section.get_block(x, local_y, z)
                world_y = section_y * 16 + local_y + 1
                if mode == 'world_surface' and block.name not in WORLD_SURFACE_IGNORED:
                    return world_y
                if mode == 'motion_blocking' and self._is_motion_blocking(block):
                    return world_y
        return 0

    def _is_motion_blocking(self, block: Block) -> bool:
        if block.name.endswith('_leaves'):
            return False
        return block.name not in NON_MOTION_BLOCKING

    def _pack(self, values: list[int]) -> list[int]:
        packed: list[int] = []
        current = 0
        used = 0
        mask = (1 << HEIGHTMAP_BITS_PER_ENTRY) - 1
        for value in values:
            value &= mask
            if used + HEIGHTMAP_BITS_PER_ENTRY > 64:
                packed.append(self._to_signed(current))
                current = 0
                used = 0
            current |= value << used
            used += HEIGHTMAP_BITS_PER_ENTRY
            if used == 64:
                packed.append(self._to_signed(current))
                current = 0
                used = 0
        if used or not packed:
            packed.append(self._to_signed(current))
        while len(packed) < HEIGHTMAP_LONG_COUNT:
            packed.append(0)
        return packed[:HEIGHTMAP_LONG_COUNT]

    @staticmethod
    def _to_signed(value: int) -> int:
        if value >= (1 << 63):
            return value - (1 << 64)
        return value
