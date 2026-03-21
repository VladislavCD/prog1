from minecraft_bedrock_to_java.config import DIMENSION_NETHER, DIMENSION_OVERWORLD
from minecraft_bedrock_to_java.converter.heightmaps import HeightmapCalculator
from minecraft_bedrock_to_java.converter.world_model import Block, Chunk, World


def test_chunk_set_and_get_block():
    chunk = Chunk(0, 0)
    chunk.set_block(1, 20, 3, Block("minecraft:stone"))
    assert chunk.get_block(1, 20, 3).name == "minecraft:stone"
    assert chunk.get_block(1, 21, 3).name == "minecraft:air"


def test_world_creates_chunk_on_demand():
    world = World()
    chunk = world.get_or_create_chunk(2, -1)
    assert world.get_chunk(2, -1) is chunk


def test_world_separates_dimensions():
    world = World()
    overworld_chunk = world.get_or_create_chunk(0, 0, dimension=DIMENSION_OVERWORLD)
    nether_chunk = world.get_or_create_chunk(0, 0, dimension=DIMENSION_NETHER)
    assert overworld_chunk is not nether_chunk
    assert world.get_chunk(0, 0, dimension=DIMENSION_NETHER) is nether_chunk


def test_heightmap_ignores_leaves_for_motion_blocking():
    chunk = Chunk(0, 0)
    chunk.set_block(0, 10, 0, Block('minecraft:oak_leaves'))
    chunk.set_block(0, 9, 0, Block('minecraft:stone'))
    maps = HeightmapCalculator().compute(chunk)
    assert len(maps['MOTION_BLOCKING']) == 37
