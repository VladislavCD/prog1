from __future__ import annotations

import gzip
import io
import struct
from dataclasses import dataclass
from typing import Any

TAG_END = 0
TAG_BYTE = 1
TAG_SHORT = 2
TAG_INT = 3
TAG_LONG = 4
TAG_FLOAT = 5
TAG_DOUBLE = 6
TAG_BYTE_ARRAY = 7
TAG_STRING = 8
TAG_LIST = 9
TAG_COMPOUND = 10
TAG_INT_ARRAY = 11
TAG_LONG_ARRAY = 12


@dataclass(frozen=True)
class Byte:
    value: int


@dataclass(frozen=True)
class Short:
    value: int


@dataclass(frozen=True)
class Int:
    value: int


@dataclass(frozen=True)
class Long:
    value: int


@dataclass(frozen=True)
class Float:
    value: float


@dataclass(frozen=True)
class Double:
    value: float


@dataclass(frozen=True)
class String:
    value: str


@dataclass(frozen=True)
class ByteArray:
    value: bytes


@dataclass(frozen=True)
class IntArray:
    value: list[int]


@dataclass(frozen=True)
class LongArray:
    value: list[int]


def guess_tag_type(value: Any) -> int:
    if isinstance(value, Byte):
        return TAG_BYTE
    if isinstance(value, Short):
        return TAG_SHORT
    if isinstance(value, Int):
        return TAG_INT
    if isinstance(value, Long):
        return TAG_LONG
    if isinstance(value, Float):
        return TAG_FLOAT
    if isinstance(value, Double):
        return TAG_DOUBLE
    if isinstance(value, ByteArray):
        return TAG_BYTE_ARRAY
    if isinstance(value, String):
        return TAG_STRING
    if isinstance(value, list):
        return TAG_LIST
    if isinstance(value, dict):
        return TAG_COMPOUND
    if isinstance(value, IntArray):
        return TAG_INT_ARRAY
    if isinstance(value, LongArray):
        return TAG_LONG_ARRAY
    if isinstance(value, str):
        return TAG_STRING
    if isinstance(value, bytes):
        return TAG_BYTE_ARRAY
    if isinstance(value, bool):
        return TAG_BYTE
    if isinstance(value, int):
        return TAG_INT
    if isinstance(value, float):
        return TAG_DOUBLE
    raise TypeError(f"Unsupported NBT value type: {type(value)!r}")


def _write_string(buffer: io.BytesIO, value: str) -> None:
    encoded = value.encode("utf-8")
    buffer.write(struct.pack(">H", len(encoded)))
    buffer.write(encoded)


def _normalize_list_element_type(list_value: list[Any]) -> int:
    if not list_value:
        return TAG_END
    first = guess_tag_type(list_value[0])
    if all(guess_tag_type(item) == first for item in list_value):
        return first
    raise TypeError("NBT lists must be homogeneous")


def _write_payload(buffer: io.BytesIO, tag_type: int, value: Any) -> None:
    if tag_type == TAG_BYTE:
        raw = value.value if isinstance(value, Byte) else int(value)
        buffer.write(struct.pack(">b", raw))
    elif tag_type == TAG_SHORT:
        raw = value.value if isinstance(value, Short) else int(value)
        buffer.write(struct.pack(">h", raw))
    elif tag_type == TAG_INT:
        raw = value.value if isinstance(value, Int) else int(value)
        buffer.write(struct.pack(">i", raw))
    elif tag_type == TAG_LONG:
        raw = value.value if isinstance(value, Long) else int(value)
        buffer.write(struct.pack(">q", raw))
    elif tag_type == TAG_FLOAT:
        raw = value.value if isinstance(value, Float) else float(value)
        buffer.write(struct.pack(">f", raw))
    elif tag_type == TAG_DOUBLE:
        raw = value.value if isinstance(value, Double) else float(value)
        buffer.write(struct.pack(">d", raw))
    elif tag_type == TAG_BYTE_ARRAY:
        raw = value.value if isinstance(value, ByteArray) else value
        buffer.write(struct.pack(">i", len(raw)))
        buffer.write(raw)
    elif tag_type == TAG_STRING:
        raw = value.value if isinstance(value, String) else str(value)
        _write_string(buffer, raw)
    elif tag_type == TAG_LIST:
        list_value = value
        element_type = _normalize_list_element_type(list_value)
        buffer.write(struct.pack(">b", element_type))
        buffer.write(struct.pack(">i", len(list_value)))
        for element in list_value:
            _write_payload(buffer, element_type, element)
    elif tag_type == TAG_COMPOUND:
        for name, nested_value in value.items():
            nested_type = guess_tag_type(nested_value)
            buffer.write(struct.pack(">b", nested_type))
            _write_string(buffer, name)
            _write_payload(buffer, nested_type, nested_value)
        buffer.write(struct.pack(">b", TAG_END))
    elif tag_type == TAG_INT_ARRAY:
        raw = value.value if isinstance(value, IntArray) else value
        buffer.write(struct.pack(">i", len(raw)))
        for item in raw:
            buffer.write(struct.pack(">i", int(item)))
    elif tag_type == TAG_LONG_ARRAY:
        raw = value.value if isinstance(value, LongArray) else value
        buffer.write(struct.pack(">i", len(raw)))
        for item in raw:
            buffer.write(struct.pack(">q", int(item)))
    else:
        raise ValueError(f"Unsupported tag type: {tag_type}")


def serialize_nbt(root_name: str, compound: dict[str, Any]) -> bytes:
    buffer = io.BytesIO()
    buffer.write(struct.pack(">b", TAG_COMPOUND))
    _write_string(buffer, root_name)
    _write_payload(buffer, TAG_COMPOUND, compound)
    return buffer.getvalue()


def gzip_nbt(root_name: str, compound: dict[str, Any]) -> bytes:
    raw = serialize_nbt(root_name, compound)
    return gzip.compress(raw)
