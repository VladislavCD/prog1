from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, Optional

from minecraft_bedrock_to_java.config import CHUNK_SECTION_HEIGHT, CHUNK_WIDTH, DIMENSION_OVERWORLD


@dataclass(frozen=True)
class Block:
    name: str
    properties: dict[str, str] = field(default_factory=dict)

    def canonical_key(self) -> tuple[str, tuple[tuple[str, str], ...]]:
        return self.name, tuple(sorted((str(k), str(v)) for k, v in self.properties.items()))


class Section:
    def __init__(self, y_index: int) -> None:
        self.y_index = y_index
        self._blocks: list[Block] = [Block("minecraft:air") for _ in range(CHUNK_WIDTH ** 3)]
        self.biomes: list[str] = ['minecraft:plains'] * 64

    @staticmethod
    def _index(x: int, y: int, z: int) -> int:
        if not (0 <= x < 16 and 0 <= y < 16 and 0 <= z < 16):
            raise IndexError(f"Section coordinates out of range: {(x, y, z)}")
        return (y * 16 * 16) + (z * 16) + x

    def set_block(self, x: int, y: int, z: int, block: Block) -> None:
        self._blocks[self._index(x, y, z)] = block

    def get_block(self, x: int, y: int, z: int) -> Block:
        return self._blocks[self._index(x, y, z)]

    def set_biomes(self, values: list[str]) -> None:
        normalized = values[:64]
        while len(normalized) < 64:
            normalized.append('minecraft:plains')
        self.biomes = normalized

    def iter_blocks(self) -> Iterator[Block]:
        return iter(self._blocks)

    def non_air_blocks(self) -> int:
        return sum(1 for block in self._blocks if block.name != "minecraft:air")

    def is_empty(self) -> bool:
        return self.non_air_blocks() == 0


class Chunk:
    def __init__(self, x: int, z: int, dimension: str = DIMENSION_OVERWORLD) -> None:
        self.x = x
        self.z = z
        self.dimension = dimension
        self.sections: Dict[int, Section] = {}
        self.inhabited_time = 0
        self.last_update = 0
        self.status = "minecraft:full"
        self.block_entities: list[dict] = []
        self.entities: list[dict] = []
        self.scheduled_ticks: list[dict] = []
        self.heightmaps: dict[str, list[int]] = {"WORLD_SURFACE": [0] * 37, "MOTION_BLOCKING": [0] * 37}

    def get_or_create_section(self, y_index: int) -> Section:
        if y_index not in self.sections:
            self.sections[y_index] = Section(y_index)
        return self.sections[y_index]

    def set_block(self, x: int, y: int, z: int, block: Block) -> None:
        section_y = y // CHUNK_SECTION_HEIGHT
        local_y = y % CHUNK_SECTION_HEIGHT
        self.get_or_create_section(section_y).set_block(x, local_y, z, block)

    def get_block(self, x: int, y: int, z: int) -> Block:
        section_y = y // CHUNK_SECTION_HEIGHT
        local_y = y % CHUNK_SECTION_HEIGHT
        section = self.sections.get(section_y)
        if section is None:
            return Block("minecraft:air")
        return section.get_block(x, local_y, z)

    def set_section_biomes(self, y_index: int, values: list[str]) -> None:
        self.get_or_create_section(y_index).set_biomes(values)

    def iter_sections(self) -> Iterable[Section]:
        for section_y in sorted(self.sections):
            yield self.sections[section_y]


class World:
    def __init__(self, name: str = "Converted Bedrock World") -> None:
        self.name = name
        self.chunks: Dict[tuple[str, int, int], Chunk] = {}
        self.spawn_x = 0
        self.spawn_y = 80
        self.spawn_z = 0
        self.seed = 0
        self.difficulty = 2
        self.game_rules: dict[str, str] = {}

    def get_or_create_chunk(self, x: int, z: int, dimension: str = DIMENSION_OVERWORLD) -> Chunk:
        key = (dimension, x, z)
        if key not in self.chunks:
            self.chunks[key] = Chunk(x, z, dimension=dimension)
        return self.chunks[key]

    def add_chunk(self, chunk: Chunk) -> None:
        self.chunks[(chunk.dimension, chunk.x, chunk.z)] = chunk

    def get_chunk(self, x: int, z: int, dimension: str = DIMENSION_OVERWORLD) -> Optional[Chunk]:
        return self.chunks.get((dimension, x, z))

    def iter_chunks(self, dimension: str | None = None) -> Iterable[Chunk]:
        for key in sorted(self.chunks):
            chunk = self.chunks[key]
            if dimension is None or chunk.dimension == dimension:
                yield chunk

    def iter_dimensions(self) -> Iterable[str]:
        seen: set[str] = set()
        for dimension, _, _ in sorted(self.chunks):
            if dimension not in seen:
                seen.add(dimension)
                yield dimension
