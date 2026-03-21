from __future__ import annotations

import struct
from dataclasses import dataclass

from minecraft_bedrock_to_java.config import BEDROCK_CHUNK_TAGS, BEDROCK_DIMENSION_MAP, DIMENSION_OVERWORLD


@dataclass(frozen=True)
class ChunkKeyInfo:
    dimension: str
    chunk_x: int
    chunk_z: int
    tag: int
    tag_name: str
    subchunk_y: int | None = None


class BedrockKeyParser:
    """
    Best-effort Bedrock LevelDB key parser.

    Known layouts handled here:
    - <chunk_x:int32><chunk_z:int32><tag:uint8>[payload...]
    - <dimension:int32><chunk_x:int32><chunk_z:int32><tag:uint8>[payload...]
    - same layouts with leading prefixes before the recognized window

    The final payload byte immediately following a `subchunk` tag is interpreted as subchunk Y.
    """

    def parse(self, key: bytes) -> ChunkKeyInfo | None:
        match = self._parse_exact_dimensioned(key)
        if match:
            return match
        match = self._parse_exact_overworld(key)
        if match:
            return match
        match = self._scan_windows(key)
        return match

    def _parse_exact_dimensioned(self, key: bytes) -> ChunkKeyInfo | None:
        if len(key) < 13:
            return None
        tag = key[12]
        if tag not in BEDROCK_CHUNK_TAGS:
            return None
        dimension_id = struct.unpack('<i', key[:4])[0]
        chunk_x = struct.unpack('<i', key[4:8])[0]
        chunk_z = struct.unpack('<i', key[8:12])[0]
        return self._build_info(key, BEDROCK_DIMENSION_MAP.get(dimension_id, DIMENSION_OVERWORLD), chunk_x, chunk_z, tag, 13)

    def _parse_exact_overworld(self, key: bytes) -> ChunkKeyInfo | None:
        if len(key) < 9:
            return None
        tag = key[8]
        if tag not in BEDROCK_CHUNK_TAGS:
            return None
        chunk_x = struct.unpack('<i', key[:4])[0]
        chunk_z = struct.unpack('<i', key[4:8])[0]
        return self._build_info(key, DIMENSION_OVERWORLD, chunk_x, chunk_z, tag, 9)

    def _scan_windows(self, key: bytes) -> ChunkKeyInfo | None:
        for start in range(0, max(1, len(key) - 12)):
            window = key[start:]
            result = self._parse_exact_dimensioned(window)
            if result:
                return result
        for start in range(0, max(1, len(key) - 8)):
            window = key[start:]
            result = self._parse_exact_overworld(window)
            if result:
                return result
        return None

    def _build_info(self, key: bytes, dimension: str, chunk_x: int, chunk_z: int, tag: int, payload_offset: int) -> ChunkKeyInfo:
        subchunk_y = None
        if BEDROCK_CHUNK_TAGS.get(tag) == 'subchunk' and len(key) > payload_offset - 1:
            raw = key[payload_offset]
            subchunk_y = raw - 256 if raw >= 128 else raw
        return ChunkKeyInfo(
            dimension=dimension,
            chunk_x=chunk_x,
            chunk_z=chunk_z,
            tag=tag,
            tag_name=BEDROCK_CHUNK_TAGS[tag],
            subchunk_y=subchunk_y,
        )
