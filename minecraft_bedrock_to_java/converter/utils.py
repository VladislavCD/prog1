from __future__ import annotations

import math
import struct
from pathlib import Path
from typing import Iterable, Iterator


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def chunk_coords_to_region(chunk_x: int, chunk_z: int) -> tuple[int, int]:
    return math.floor(chunk_x / 32), math.floor(chunk_z / 32)


def local_chunk_index(chunk_x: int, chunk_z: int) -> int:
    return (chunk_x & 31) + ((chunk_z & 31) * 32)


def floor_div(a: int, b: int) -> int:
    return a // b if a >= 0 else -((-a + b - 1) // b)


def iter_chunks(sequence: Iterable, size: int) -> Iterator[list]:
    bucket: list = []
    for item in sequence:
        bucket.append(item)
        if len(bucket) >= size:
            yield bucket
            bucket = []
    if bucket:
        yield bucket


def read_i32_le(data: bytes, offset: int = 0) -> int:
    return struct.unpack_from("<i", data, offset)[0]


def read_u32_le(data: bytes, offset: int = 0) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def read_i16_le(data: bytes, offset: int = 0) -> int:
    return struct.unpack_from("<h", data, offset)[0]


def read_varint(buffer: bytes, start: int = 0) -> tuple[int, int]:
    result = 0
    shift = 0
    offset = start
    while offset < len(buffer):
        byte = buffer[offset]
        result |= (byte & 0x7F) << shift
        offset += 1
        if not (byte & 0x80):
            return result, offset
        shift += 7
        if shift > 35:
            raise ValueError("VarInt is too large")
    raise ValueError("Unexpected end of buffer while reading varint")


def read_signed_varint(buffer: bytes, start: int = 0) -> tuple[int, int]:
    value, offset = read_varint(buffer, start)
    if value & 1:
        return -(value >> 1) - 1, offset
    return value >> 1, offset


def pack_u32_array(values: list[int]) -> bytes:
    return struct.pack(f">{len(values)}I", *values) if values else b""
