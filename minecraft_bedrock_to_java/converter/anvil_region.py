from __future__ import annotations

import math
import struct
import time
import zlib
from pathlib import Path

from minecraft_bedrock_to_java.config import REGION_HEADER_SECTORS, REGION_SECTOR_BYTES
from .logger import get_logger
from .utils import ensure_directory, local_chunk_index

LOGGER = get_logger(__name__)


class RegionFile:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.locations = bytearray(REGION_SECTOR_BYTES)
        self.timestamps = bytearray(REGION_SECTOR_BYTES)
        self.sectors: list[bytes] = [b"" for _ in range(REGION_HEADER_SECTORS)]

    def add_chunk(self, chunk_x: int, chunk_z: int, nbt_payload: bytes) -> None:
        local_index = local_chunk_index(chunk_x, chunk_z)
        compressed = zlib.compress(nbt_payload)
        chunk_data = struct.pack(">I", len(compressed) + 1) + b"\x02" + compressed
        sector_count = max(1, math.ceil(len(chunk_data) / REGION_SECTOR_BYTES))
        padded = chunk_data.ljust(sector_count * REGION_SECTOR_BYTES, b"\x00")

        sector_offset = len(self.sectors)
        self.sectors.extend(
            padded[i:i + REGION_SECTOR_BYTES]
            for i in range(0, len(padded), REGION_SECTOR_BYTES)
        )

        if sector_offset > 0xFFFFFF:
            raise ValueError("Region grew beyond supported sector offset range")
        self.locations[local_index * 4: local_index * 4 + 4] = bytes([
            (sector_offset >> 16) & 0xFF,
            (sector_offset >> 8) & 0xFF,
            sector_offset & 0xFF,
            sector_count & 0xFF,
        ])
        timestamp = int(time.time())
        self.timestamps[local_index * 4: local_index * 4 + 4] = struct.pack(">I", timestamp)
        LOGGER.debug(
            "Added chunk (%s, %s) to region %s at sector %s (%s sectors)",
            chunk_x,
            chunk_z,
            self.path.name,
            sector_offset,
            sector_count,
        )

    def save(self) -> Path:
        ensure_directory(self.path.parent)
        with self.path.open("wb") as handle:
            handle.write(self.locations)
            handle.write(self.timestamps)
            for sector in self.sectors[REGION_HEADER_SECTORS:]:
                handle.write(sector)
        return self.path
