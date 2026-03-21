from __future__ import annotations

from dataclasses import dataclass, field

from minecraft_bedrock_to_java.config import DEFAULT_JAVA_VERSION, LEVEL_DAT_VERSION


@dataclass(frozen=True)
class JavaVersionProfile:
    name: str
    data_version: int
    pack_format: int
    level_dat_version: int = LEVEL_DAT_VERSION
    min_y: int = -64
    height: int = 384
    worldgen_preset: str = "minecraft:normal"
    game_rules: dict[str, str] = field(default_factory=lambda: {
        "doDaylightCycle": "true",
        "doWeatherCycle": "true",
        "doMobSpawning": "true",
        "keepInventory": "false",
        "mobGriefing": "true",
        "randomTickSpeed": "3",
    })


class VersionRegistry:
    def __init__(self) -> None:
        self._profiles = {
            "1.20": JavaVersionProfile(name="1.20", data_version=3463, pack_format=15),
            "1.20.1": JavaVersionProfile(name="1.20.1", data_version=3465, pack_format=15),
            "1.20.4": JavaVersionProfile(name="1.20.4", data_version=3700, pack_format=26),
            "1.21": JavaVersionProfile(name="1.21", data_version=3953, pack_format=41),
        }

    def resolve(self, requested: str | None) -> JavaVersionProfile:
        if not requested:
            return self._profiles[DEFAULT_JAVA_VERSION]
        if requested in self._profiles:
            return self._profiles[requested]
        aliases = {
            "latest": "1.21",
            "stable": DEFAULT_JAVA_VERSION,
            "1.20.x": "1.20.4",
        }
        normalized = aliases.get(requested, requested)
        if normalized in self._profiles:
            return self._profiles[normalized]
        return self._profiles[DEFAULT_JAVA_VERSION]
