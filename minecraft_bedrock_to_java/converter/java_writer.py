from __future__ import annotations

import struct
from pathlib import Path

from minecraft_bedrock_to_java.config import (
    DEFAULT_SPAWN_X,
    DEFAULT_SPAWN_Y,
    DEFAULT_SPAWN_Z,
    DEFAULT_WORLD_NAME,
    DIMENSION_FOLDER_MAP,
)
from .anvil_region import RegionFile
from .logger import get_logger
from .nbt_helpers import Byte, Int, Long, LongArray, String, gzip_nbt, serialize_nbt
from .utils import chunk_coords_to_region, ensure_directory
from .versioning import JavaVersionProfile, VersionRegistry
from .world_model import Block, Chunk, Section, World

LOGGER = get_logger(__name__)


class JavaWorldWriter:
    def __init__(self, output_path: Path, version_profile: JavaVersionProfile | None = None) -> None:
        self.output_path = output_path
        self.version_profile = version_profile or VersionRegistry().resolve(None)

    def write_world(self, world: World) -> None:
        ensure_directory(self.output_path)
        self._write_level_dat(world)
        self._write_session_lock()

        total_region_files = 0
        for dimension in world.iter_dimensions():
            region_dir = self._region_dir_for_dimension(dimension)
            ensure_directory(region_dir)
            region_files: dict[tuple[int, int], RegionFile] = {}
            for chunk in world.iter_chunks(dimension=dimension):
                region_coords = chunk_coords_to_region(chunk.x, chunk.z)
                if region_coords not in region_files:
                    rx, rz = region_coords
                    region_path = region_dir / f"r.{rx}.{rz}.mca"
                    region_files[region_coords] = RegionFile(region_path)
                region_files[region_coords].add_chunk(chunk.x, chunk.z, self._serialize_chunk(chunk))
            for region in region_files.values():
                region.save()
            total_region_files += len(region_files)

        LOGGER.info("Wrote %s region files to %s", total_region_files, self.output_path)

    def _region_dir_for_dimension(self, dimension: str) -> Path:
        folder = DIMENSION_FOLDER_MAP.get(dimension, "")
        if not folder:
            return self.output_path / "region"
        return self.output_path / folder / "region"

    def _write_session_lock(self) -> None:
        with (self.output_path / "session.lock").open("wb") as handle:
            handle.write(struct.pack(">q", 0))

    def _write_level_dat(self, world: World) -> None:
        gamerules = {
            name: String(value)
            for name, value in {**self.version_profile.game_rules, **world.game_rules}.items()
        }
        data = {
            "Data": {
                "version": Int(self.version_profile.level_dat_version),
                "DataVersion": Int(self.version_profile.data_version),
                "LevelName": String(world.name or DEFAULT_WORLD_NAME),
                "SpawnX": Int(world.spawn_x if world.spawn_x else DEFAULT_SPAWN_X),
                "SpawnY": Int(world.spawn_y if world.spawn_y else DEFAULT_SPAWN_Y),
                "SpawnZ": Int(world.spawn_z if world.spawn_z else DEFAULT_SPAWN_Z),
                "Time": Long(0),
                "DayTime": Long(0),
                "clearWeatherTime": Int(0),
                "rainTime": Int(0),
                "raining": Byte(0),
                "thunderTime": Int(0),
                "thundering": Byte(0),
                "GameType": Int(1),
                "hardcore": Byte(0),
                "initialized": Byte(1),
                "allowCommands": Byte(1),
                "Difficulty": Byte(world.difficulty),
                "BorderCenterX": 0.0,
                "BorderCenterZ": 0.0,
                "BorderSize": 60000000.0,
                "WasModded": Byte(0),
                "GameRules": gamerules,
                "WorldGenSettings": {
                    "seed": Long(world.seed),
                    "generate_features": Byte(1),
                    "bonus_chest": Byte(0),
                    "dimensions": {},
                },
                "ServerBrands": [String('minecraft')],
                "Version": {
                    'Name': String(self.version_profile.name),
                    'Id': Int(self.version_profile.data_version),
                    'Series': String('main'),
                    'Snapshot': Byte(0),
                },
            }
        }
        payload = gzip_nbt("", data)
        with (self.output_path / "level.dat").open("wb") as handle:
            handle.write(payload)

    def _serialize_chunk(self, chunk: Chunk) -> bytes:
        root = {
            "DataVersion": Int(self.version_profile.data_version),
            "xPos": Int(chunk.x),
            "yPos": Int(min(chunk.sections.keys(), default=0)),
            "zPos": Int(chunk.z),
            "LastUpdate": Long(chunk.last_update),
            "InhabitedTime": Long(chunk.inhabited_time),
            "Status": String(chunk.status),
            "sections": [self._build_section_nbt(section) for section in chunk.iter_sections()],
            "block_entities": [self._compoundify(value) for value in chunk.block_entities],
            "entities": [self._compoundify(value) for value in chunk.entities],
            "fluid_ticks": [self._compoundify(value) for value in chunk.scheduled_ticks],
            "block_ticks": [],
            "PostProcessing": [],
            "structures": {"starts": {}, "References": {}},
            "Heightmaps": {name: LongArray(values) for name, values in chunk.heightmaps.items()},
            "isLightOn": Byte(1),
        }
        return serialize_nbt("", root)

    def _build_section_nbt(self, section: Section) -> dict:
        palette, indices = self._build_palette_and_indices(section)
        packed = self._pack_block_states(indices, max(4, (len(palette) - 1).bit_length()))
        biome_palette, biome_indices = self._build_biome_palette_and_indices(section.biomes)
        packed_biomes = self._pack_block_states(biome_indices, max(1, (len(biome_palette) - 1).bit_length()))
        return {
            "Y": Byte(section.y_index),
            "block_states": {
                "palette": [self._block_to_nbt(block) for block in palette],
                "data": LongArray(packed),
            },
            "biomes": {
                "palette": [String(name) for name in biome_palette],
                "data": LongArray(packed_biomes),
            },
            "SkyLight": bytes([0xFF] * 2048),
            "BlockLight": bytes([0x00] * 2048),
        }

    def _build_palette_and_indices(self, section: Section) -> tuple[list[Block], list[int]]:
        palette: list[Block] = []
        palette_index: dict[tuple[str, tuple[tuple[str, str], ...]], int] = {}
        indices: list[int] = []
        for block in section.iter_blocks():
            key = block.canonical_key()
            if key not in palette_index:
                palette_index[key] = len(palette)
                palette.append(block)
            indices.append(palette_index[key])
        return palette or [Block("minecraft:air")], indices or [0] * 4096

    def _build_biome_palette_and_indices(self, values: list[str]) -> tuple[list[str], list[int]]:
        palette: list[str] = []
        palette_index: dict[str, int] = {}
        indices: list[int] = []
        for name in values:
            if name not in palette_index:
                palette_index[name] = len(palette)
                palette.append(name)
            indices.append(palette_index[name])
        return palette or ['minecraft:plains'], indices or [0] * 64

    def _pack_block_states(self, indices: list[int], bits_per_block: int) -> list[int]:
        if not indices:
            return []
        values_per_long = max(1, 64 // bits_per_block)
        packed: list[int] = []
        mask = (1 << bits_per_block) - 1
        for group_start in range(0, len(indices), values_per_long):
            group = indices[group_start:group_start + values_per_long]
            current = 0
            for i, value in enumerate(group):
                current |= (int(value) & mask) << (i * bits_per_block)
            if current >= (1 << 63):
                current -= 1 << 64
            packed.append(current)
        return packed

    def _block_to_nbt(self, block: Block) -> dict:
        entry: dict = {"Name": String(block.name)}
        if block.properties:
            entry["Properties"] = {key: String(value) for key, value in sorted(block.properties.items())}
        return entry

    def _compoundify(self, payload):
        if isinstance(payload, dict):
            converted = {}
            for key, value in payload.items():
                converted[key] = self._compoundify(value)
            return converted
        if isinstance(payload, list):
            return [self._compoundify(item) for item in payload]
        if isinstance(payload, str):
            return String(payload)
        if isinstance(payload, bool):
            return Byte(1 if payload else 0)
        if isinstance(payload, int):
            return Int(payload)
        if isinstance(payload, float):
            return value if (value := float(payload)) else 0.0
        return payload
