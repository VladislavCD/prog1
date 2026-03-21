from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .logger import get_logger
from .utils import read_signed_varint, read_varint

LOGGER = get_logger(__name__)


@dataclass
class ParsedBlockState:
    name: str
    states: dict[str, Any]


class BedrockChunkParser:
    """
    Best-effort parser for Bedrock subchunks.

    Bedrock subchunk payloads changed over time. This parser implements a set of heuristics:
    - legacy 4096-byte runtime IDs (plus optional palette table)
    - newer palette-based payloads with bits-per-block and packed words
    - explicit JSON fallback for synthetic/debug payloads
    """

    def parse_subchunk(self, raw: bytes) -> list[ParsedBlockState]:
        if not raw:
            return [ParsedBlockState("minecraft:air", {}) for _ in range(4096)]

        if raw[:1] == b"{":
            return self._parse_json_payload(raw)

        version = raw[0]
        if version in {1, 8, 9}:
            try:
                return self._parse_palette_subchunk(raw)
            except Exception as exc:
                LOGGER.debug("Palette subchunk parse failed for version %s: %s", version, exc)

        try:
            return self._parse_legacy_runtime_ids(raw)
        except Exception as exc:
            LOGGER.warning("Failed to parse subchunk payload, filling with air: %s", exc)
            return [ParsedBlockState("minecraft:air", {}) for _ in range(4096)]

    def _parse_json_payload(self, raw: bytes) -> list[ParsedBlockState]:
        payload = json.loads(raw.decode("utf-8"))
        blocks = payload.get("blocks", [])
        output: list[ParsedBlockState] = []
        for item in blocks[:4096]:
            output.append(ParsedBlockState(item.get("name", "minecraft:air"), item.get("states", {})))
        while len(output) < 4096:
            output.append(ParsedBlockState("minecraft:air", {}))
        return output

    def _parse_legacy_runtime_ids(self, raw: bytes) -> list[ParsedBlockState]:
        if len(raw) >= 1 + 4096:
            payload = raw[1:1 + 4096]
        elif len(raw) >= 4096:
            payload = raw[:4096]
        else:
            raise ValueError("Legacy payload is too small")

        runtime_to_block = {
            0: ParsedBlockState("minecraft:air", {}),
            1: ParsedBlockState("minecraft:stone", {}),
            2: ParsedBlockState("minecraft:grass_block", {}),
            3: ParsedBlockState("minecraft:dirt", {}),
            7: ParsedBlockState("minecraft:bedrock", {}),
            8: ParsedBlockState("minecraft:water", {"liquid_depth": 0}),
            9: ParsedBlockState("minecraft:water", {"liquid_depth": 0}),
            12: ParsedBlockState("minecraft:sand", {}),
            20: ParsedBlockState("minecraft:glass", {}),
            54: ParsedBlockState("minecraft:chest", {}),
        }
        return [runtime_to_block.get(byte, ParsedBlockState("minecraft:stone", {})) for byte in payload[:4096]]

    def _parse_palette_subchunk(self, raw: bytes) -> list[ParsedBlockState]:
        version = raw[0]
        storage_count = raw[1] if len(raw) > 1 else 1
        offset = 2
        storages: list[list[ParsedBlockState]] = []

        if version == 9 and len(raw) > 2:
            offset += 1  # skip y-index field embedded in some subchunk payloads

        for _ in range(storage_count):
            if offset >= len(raw):
                break
            header = raw[offset]
            bits_per_block = header >> 1
            offset += 1
            if bits_per_block == 0:
                bits_per_block = 1
            word_count = ((4096 * bits_per_block) + 31) // 32
            words: list[int] = []
            for _word in range(word_count):
                if offset + 4 > len(raw):
                    raise ValueError("Unexpected end while reading packed block words")
                words.append(int.from_bytes(raw[offset:offset + 4], "little"))
                offset += 4

            actual_palette_len, offset = read_varint(raw, offset)
            palette: list[ParsedBlockState] = []
            for _entry in range(actual_palette_len):
                entry_len, offset = read_varint(raw, offset)
                entry_blob = raw[offset:offset + entry_len]
                offset += entry_len
                palette.append(self._parse_palette_entry(entry_blob, version))

            indices = self._unpack_indices(words, bits_per_block, 4096)
            blocks: list[ParsedBlockState] = []
            for index in indices:
                if 0 <= index < len(palette):
                    blocks.append(palette[index])
                else:
                    blocks.append(ParsedBlockState("minecraft:air", {}))
            storages.append(blocks)

        if not storages:
            return [ParsedBlockState("minecraft:air", {}) for _ in range(4096)]
        merged = list(storages[0])
        for storage in storages[1:]:
            for i, block in enumerate(storage):
                if block.name != "minecraft:air":
                    merged[i] = block
        return merged

    def _parse_palette_entry(self, payload: bytes, version: int) -> ParsedBlockState:
        if not payload:
            return ParsedBlockState("minecraft:air", {})
        if payload[:1] == b"{":
            data = json.loads(payload.decode("utf-8"))
            return ParsedBlockState(data.get("name", "minecraft:air"), data.get("states", {}))

        try:
            name_len, offset = read_varint(payload, 0)
            name = payload[offset:offset + name_len].decode("utf-8")
            offset += name_len
            state_count, offset = read_varint(payload, offset)
            states: dict[str, Any] = {}
            for _ in range(state_count):
                key_len, offset = read_varint(payload, offset)
                key = payload[offset:offset + key_len].decode("utf-8")
                offset += key_len
                value_type = payload[offset]
                offset += 1
                if value_type == 1:
                    value, offset = read_signed_varint(payload, offset)
                elif value_type == 2:
                    value = bool(payload[offset])
                    offset += 1
                else:
                    value_len, offset = read_varint(payload, offset)
                    value = payload[offset:offset + value_len].decode("utf-8")
                    offset += value_len
                states[key] = value
            return ParsedBlockState(name, states)
        except Exception:
            LOGGER.debug("Could not parse palette entry as custom-varint format; using opaque fallback")
        return ParsedBlockState("minecraft:stone", {})

    def _unpack_indices(self, words: list[int], bits_per_block: int, count: int) -> list[int]:
        mask = (1 << bits_per_block) - 1
        values: list[int] = []
        current_word_index = 0
        current_bit_index = 0
        for _ in range(count):
            if current_word_index >= len(words):
                values.append(0)
                continue
            word = words[current_word_index]
            if current_bit_index + bits_per_block <= 32:
                value = (word >> current_bit_index) & mask
                current_bit_index += bits_per_block
                if current_bit_index == 32:
                    current_bit_index = 0
                    current_word_index += 1
            else:
                low_bits = 32 - current_bit_index
                high_bits = bits_per_block - low_bits
                next_word = words[current_word_index + 1] if current_word_index + 1 < len(words) else 0
                value = ((word >> current_bit_index) | (next_word << low_bits)) & mask
                current_word_index += 1
                current_bit_index = high_bits
            values.append(value)
        return values
