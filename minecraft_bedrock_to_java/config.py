from __future__ import annotations

JAVA_DATA_VERSION = 3465  # Minecraft Java 1.20.1
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_CHUNK_LIMIT = 0
DEFAULT_WORLD_NAME = "Converted Bedrock World"
DEFAULT_SPAWN_X = 0
DEFAULT_SPAWN_Y = 80
DEFAULT_SPAWN_Z = 0
DEFAULT_JAVA_VERSION = "1.20.1"
REGION_SECTOR_BYTES = 4096
REGION_HEADER_SECTORS = 2
CHUNK_SECTION_HEIGHT = 16
CHUNK_WIDTH = 16
WORLD_MIN_SECTION_Y = -4
WORLD_MAX_SECTION_Y = 19
LEVEL_DAT_VERSION = 19133

DIMENSION_OVERWORLD = "overworld"
DIMENSION_NETHER = "the_nether"
DIMENSION_END = "the_end"
DIMENSION_FOLDER_MAP = {
    DIMENSION_OVERWORLD: "",
    DIMENSION_NETHER: "DIM-1",
    DIMENSION_END: "DIM1",
}
BEDROCK_DIMENSION_MAP = {
    0: DIMENSION_OVERWORLD,
    1: DIMENSION_NETHER,
    2: DIMENSION_END,
}

BEDROCK_CHUNK_TAGS = {
    0x2B: "data_2d",
    0x2D: "data_3d",
    0x2F: "subchunk",
    0x30: "version",
    0x31: "legacy_terrain",
    0x32: "block_entities",
    0x33: "entities",
    0x34: "pending_ticks",
    0x35: "random_ticks",
    0x36: "biomes",
    0x39: "finalized_state",
    0x76: "border_blocks",
}

HEIGHTMAP_BITS_PER_ENTRY = 9
HEIGHTMAP_LONG_COUNT = 37
