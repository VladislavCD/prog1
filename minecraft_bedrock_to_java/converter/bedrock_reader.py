from __future__ import annotations

import gzip
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from minecraft_bedrock_to_java.config import DEFAULT_WORLD_NAME
from .bedrock_chunk_parser import BedrockChunkParser
from .bedrock_key_parser import BedrockKeyParser, ChunkKeyInfo
from .biome_mapper import BiomeMapper
from .block_entity_mapper import BlockEntityMapper
from .block_mapper import BlockMapper
from .entity_mapper import EntityMapper
from .heightmaps import HeightmapCalculator
from .leveldb_interface import LevelDBFactory
from .logger import get_logger
from .world_model import World

LOGGER = get_logger(__name__)


class BedrockWorldReader:
    def __init__(self, world_path: Path) -> None:
        self.world_path = world_path
        self.db_path = self._resolve_db_path(world_path)
        self.chunk_parser = BedrockChunkParser()
        self.key_parser = BedrockKeyParser()
        self.biome_mapper = BiomeMapper()
        self.block_entity_mapper = BlockEntityMapper()
        self.entity_mapper = EntityMapper()
        self.heightmaps = HeightmapCalculator()
        self.leveldb_factory = LevelDBFactory()

    def _resolve_db_path(self, world_path: Path) -> Path:
        if not world_path.exists():
            raise FileNotFoundError(f"Bedrock world path does not exist: {world_path}")
        db_path = world_path / "db"
        if not db_path.exists():
            raise FileNotFoundError(f"Bedrock db directory not found: {db_path}")
        return db_path

    def _open_db(self):
        try:
            return self.leveldb_factory.create(self.db_path)
        except Exception as exc:
            raise RuntimeError(f"Failed to open LevelDB at {self.db_path}: {exc}") from exc

    def read_world(self, chunk_limit: int = 0, mapper: BlockMapper | None = None) -> World:
        mapper = mapper or BlockMapper()
        world = World(self._read_world_name())

        with self._open_db() as db:
            chunk_records = self._collect_chunk_records(db)
            LOGGER.info("Found %s chunk coordinate groups in LevelDB", len(chunk_records))

            converted = 0
            for chunk_id, record_group in sorted(chunk_records.items()):
                if chunk_limit and converted >= chunk_limit:
                    break
                try:
                    chunk = self._build_chunk_from_records(record_group, mapper, world)
                    chunk.heightmaps = self.heightmaps.compute(chunk)
                    world.add_chunk(chunk)
                    converted += 1
                except Exception as exc:
                    LOGGER.exception("Failed to convert chunk %s: %s", chunk_id, exc)
        return world

    def _read_world_name(self) -> str:
        levelname = self.world_path / 'levelname.txt'
        if levelname.exists():
            content = levelname.read_text(encoding='utf-8', errors='replace').strip()
            if content:
                return content
        return DEFAULT_WORLD_NAME

    def _collect_chunk_records(self, db: Any) -> dict[tuple[str, int, int], list[tuple[ChunkKeyInfo, bytes]]]:
        grouped: dict[tuple[str, int, int], list[tuple[ChunkKeyInfo, bytes]]] = defaultdict(list)
        for key, value in db:
            info = self.key_parser.parse(key)
            if info is None:
                LOGGER.debug("Skipping unknown Bedrock key: %r", key)
                continue
            grouped[(info.dimension, info.chunk_x, info.chunk_z)].append((info, value))
        return grouped

    def _build_chunk_from_records(
        self,
        records: list[tuple[ChunkKeyInfo, bytes]],
        mapper: BlockMapper,
        world: World,
    ):
        first_info = records[0][0]
        chunk = world.get_or_create_chunk(first_info.chunk_x, first_info.chunk_z, dimension=first_info.dimension)
        for info, value in records:
            if info.tag_name == 'subchunk':
                self._apply_subchunk_record(chunk, info, value, mapper)
            elif info.tag_name in {'biomes', 'data_2d', 'data_3d'}:
                self._apply_biome_record(chunk, value)
            elif info.tag_name == 'block_entities':
                payload = self._decode_structured_payload(value)
                chunk.block_entities.extend(self.block_entity_mapper.map_many(payload, chunk.x, chunk.z))
            elif info.tag_name == 'entities':
                payload = self._decode_structured_payload(value)
                chunk.entities.extend(self.entity_mapper.map_many(payload))
            elif info.tag_name in {'pending_ticks', 'random_ticks'}:
                payload = self._decode_structured_payload(value)
                if isinstance(payload, list):
                    chunk.scheduled_ticks.extend(payload)
            else:
                LOGGER.debug(
                    "Chunk (%s,%s,%s) record %s (%s bytes) retained as metadata only",
                    chunk.dimension,
                    chunk.x,
                    chunk.z,
                    info.tag_name,
                    len(value),
                )
        return chunk

    def _apply_subchunk_record(self, chunk, info: ChunkKeyInfo, value: bytes, mapper: BlockMapper) -> None:
        subchunk_y = info.subchunk_y or 0
        parsed = self.chunk_parser.parse_subchunk(value)
        for index, parsed_block in enumerate(parsed[:4096]):
            x = index & 15
            z = (index >> 4) & 15
            y = (index >> 8) & 15
            world_y = (subchunk_y * 16) + y
            java_block = mapper.map_block(parsed_block.name, parsed_block.states)
            chunk.set_block(x, world_y, z, java_block)

    def _apply_biome_record(self, chunk, value: bytes) -> None:
        volume = self.biome_mapper.decode_biomes(value)
        if not chunk.sections:
            chunk.get_or_create_section(0)
        for section in chunk.iter_sections():
            section.set_biomes(volume.values)

    def _decode_structured_payload(self, value: bytes) -> Any:
        if not value:
            return []
        if value[:2] == b'\x1f\x8b':
            try:
                return self._decode_structured_payload(gzip.decompress(value))
            except OSError:
                return []
        if value[:1] in {b'{', b'['}:
            try:
                return json.loads(value.decode('utf-8'))
            except json.JSONDecodeError:
                LOGGER.debug('Failed to decode JSON payload for structured Bedrock record')
                return []
        return []
