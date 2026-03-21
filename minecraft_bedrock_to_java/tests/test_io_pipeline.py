from pathlib import Path

from minecraft_bedrock_to_java.config import DIMENSION_END, DIMENSION_NETHER, DIMENSION_OVERWORLD
from minecraft_bedrock_to_java.converter.java_writer import JavaWorldWriter
from minecraft_bedrock_to_java.converter.versioning import VersionRegistry
from minecraft_bedrock_to_java.converter.world_model import Block, World


def test_writer_creates_dimension_region_dirs(tmp_path: Path):
    world = World("Demo")
    world.seed = 12345
    world.get_or_create_chunk(0, 0, dimension=DIMENSION_OVERWORLD).set_block(0, 0, 0, Block("minecraft:stone"))
    world.get_or_create_chunk(0, 0, dimension=DIMENSION_NETHER).set_block(0, 0, 0, Block("minecraft:netherrack"))
    world.get_or_create_chunk(0, 0, dimension=DIMENSION_END).set_block(0, 0, 0, Block("minecraft:end_stone"))

    JavaWorldWriter(tmp_path, version_profile=VersionRegistry().resolve('1.20.4')).write_world(world)

    assert (tmp_path / 'region').exists()
    assert (tmp_path / 'DIM-1' / 'region').exists()
    assert (tmp_path / 'DIM1' / 'region').exists()
    assert (tmp_path / 'level.dat').exists()
