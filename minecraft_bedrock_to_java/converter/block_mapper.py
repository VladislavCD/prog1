from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .logger import get_logger
from .world_model import Block

LOGGER = get_logger(__name__)


@dataclass
class BedrockBlock:
    name: str
    states: dict[str, object]


MapperFunction = Callable[[BedrockBlock], Block]


def _stringify_properties(states: dict[str, object]) -> dict[str, str]:
    output: dict[str, str] = {}
    for key, value in states.items():
        if isinstance(value, bool):
            output[key] = "true" if value else "false"
        else:
            output[key] = str(value).lower() if isinstance(value, str) else str(value)
    return output


class BlockMapper:
    def __init__(self) -> None:
        self.simple_map: dict[str, str] = {
            "minecraft:air": "minecraft:air",
            "minecraft:cave_air": "minecraft:air",
            "minecraft:void_air": "minecraft:air",
            "minecraft:stone": "minecraft:stone",
            "minecraft:deepslate": "minecraft:deepslate",
            "minecraft:dirt": "minecraft:dirt",
            "minecraft:grass": "minecraft:short_grass",
            "minecraft:grass_block": "minecraft:grass_block",
            "minecraft:cobblestone": "minecraft:cobblestone",
            "minecraft:oak_log": "minecraft:oak_log",
            "minecraft:spruce_log": "minecraft:spruce_log",
            "minecraft:birch_log": "minecraft:birch_log",
            "minecraft:oak_planks": "minecraft:oak_planks",
            "minecraft:spruce_planks": "minecraft:spruce_planks",
            "minecraft:birch_planks": "minecraft:birch_planks",
            "minecraft:water": "minecraft:water",
            "minecraft:flowing_water": "minecraft:water",
            "minecraft:sand": "minecraft:sand",
            "minecraft:red_sand": "minecraft:red_sand",
            "minecraft:glass": "minecraft:glass",
            "minecraft:bedrock": "minecraft:bedrock",
            "minecraft:chest": "minecraft:chest",
            "minecraft:furnace": "minecraft:furnace",
            "minecraft:torch": "minecraft:torch",
            "minecraft:oak_leaves": "minecraft:oak_leaves",
            "minecraft:leaves": "minecraft:oak_leaves",
            "minecraft:spruce_leaves": "minecraft:spruce_leaves",
            "minecraft:birch_leaves": "minecraft:birch_leaves",
        }
        self.special_cases: dict[str, MapperFunction] = {
            "minecraft:stone_slab": self._map_slab,
            "minecraft:oak_stairs": self._map_stairs,
            "minecraft:birch_stairs": self._map_stairs,
            "minecraft:spruce_stairs": self._map_stairs,
            "minecraft:chest": self._map_chest,
            "minecraft:torch": self._map_torch,
            "minecraft:water": self._map_water,
            "minecraft:flowing_water": self._map_water,
        }

    def map_block(self, bedrock_name: str, states: dict[str, object] | None = None) -> Block:
        states = states or {}
        bedrock_block = BedrockBlock(bedrock_name, states)

        if bedrock_name in self.special_cases:
            return self.special_cases[bedrock_name](bedrock_block)

        if bedrock_name in self.simple_map:
            return Block(self.simple_map[bedrock_name], self._normalize_properties(bedrock_name, states))

        if bedrock_name.endswith("_slab"):
            return self._map_slab(bedrock_block)
        if bedrock_name.endswith("_stairs"):
            return self._map_stairs(bedrock_block)
        if bedrock_name.endswith("_log"):
            return self._map_log(bedrock_block)
        if bedrock_name.endswith("_leaves"):
            java_name = bedrock_name if bedrock_name.startswith("minecraft:") else f"minecraft:{bedrock_name}"
            return Block(java_name, self._normalize_properties(bedrock_name, states))
        if bedrock_name.endswith('_trapdoor'):
            return self._map_trapdoor(bedrock_block)

        LOGGER.warning("Unknown Bedrock block '%s', using fallback", bedrock_name)
        fallback = "minecraft:air" if bedrock_name in {"", "minecraft:unknown", "unknown"} else "minecraft:stone"
        return Block(fallback)

    def _normalize_properties(self, name: str, states: dict[str, object]) -> dict[str, str]:
        props = _stringify_properties(states)
        if name.endswith("_log"):
            axis = props.get("pillar_axis", props.get("axis", "y"))
            return {"axis": axis}
        if name.endswith("_leaves") or name == "minecraft:leaves":
            return {
                "persistent": props.get("persistent_bit", "true"),
                "distance": "1",
            }
        if name == "minecraft:grass_block":
            snowy = props.get("snowy", props.get("snowy_bit", "false"))
            return {"snowy": snowy}
        return {}

    def _map_log(self, block: BedrockBlock) -> Block:
        return Block(block.name, self._normalize_properties(block.name, block.states))

    def _map_water(self, block: BedrockBlock) -> Block:
        level = str(block.states.get("liquid_depth", 0))
        return Block("minecraft:water", {"level": level})

    def _map_slab(self, block: BedrockBlock) -> Block:
        material = block.name.split(":", 1)[-1].replace("_slab", "")
        java_name = f"minecraft:{material}_slab"
        raw_type = str(block.states.get("top_slot_bit", "false")).lower()
        slab_type = "top" if raw_type == "true" else str(block.states.get("minecraft:vertical_half", block.states.get("vertical_half", "bottom"))).lower()
        if block.states.get("double_slab_bit"):
            slab_type = "double"
        waterlogged = 'true' if block.states.get('waterlogged_bit') else 'false'
        if slab_type not in {"top", "bottom", "double"}:
            slab_type = "bottom"
        return Block(java_name, {"type": slab_type, "waterlogged": waterlogged})

    def _map_stairs(self, block: BedrockBlock) -> Block:
        facing_map = {
            "0": "east",
            "1": "west",
            "2": "south",
            "3": "north",
            "east": "east",
            "west": "west",
            "south": "south",
            "north": "north",
        }
        half = "top" if block.states.get("upside_down_bit") else "bottom"
        facing_raw = str(block.states.get("weirdo_direction", block.states.get("facing_direction", "2"))).lower()
        facing = facing_map.get(facing_raw, "south")
        waterlogged = 'true' if block.states.get('waterlogged_bit') else 'false'
        return Block(block.name, {"facing": facing, "half": half, "shape": "straight", "waterlogged": waterlogged})

    def _map_torch(self, block: BedrockBlock) -> Block:
        torch_facing = block.states.get("torch_facing_direction", "top")
        if str(torch_facing).lower() in {"top", "up", "unknown"}:
            return Block("minecraft:torch")
        facing_map = {"west": "west", "east": "east", "north": "north", "south": "south", "1": "east", "2": "west", "3": "south", "4": "north"}
        return Block("minecraft:wall_torch", {"facing": facing_map.get(str(torch_facing).lower(), "north")})

    def _map_chest(self, block: BedrockBlock) -> Block:
        facing_map = {
            "2": "north",
            "3": "south",
            "4": "west",
            "5": "east",
            "north": "north",
            "south": "south",
            "west": "west",
            "east": "east",
        }
        facing = facing_map.get(str(block.states.get("facing_direction", "2")).lower(), "north")
        waterlogged = 'true' if block.states.get('waterlogged_bit') else 'false'
        return Block("minecraft:chest", {"facing": facing, "type": "single", "waterlogged": waterlogged})

    def _map_trapdoor(self, block: BedrockBlock) -> Block:
        facing_map = {'0': 'north', '1': 'south', '2': 'west', '3': 'east'}
        facing = facing_map.get(str(block.states.get('direction', '0')), 'north')
        half = 'top' if block.states.get('upside_down_bit') else 'bottom'
        open_state = 'true' if block.states.get('open_bit') else 'false'
        waterlogged = 'true' if block.states.get('waterlogged_bit') else 'false'
        return Block(block.name, {'facing': facing, 'half': half, 'open': open_state, 'waterlogged': waterlogged})
