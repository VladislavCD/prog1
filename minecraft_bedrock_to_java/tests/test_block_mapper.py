from minecraft_bedrock_to_java.converter.block_mapper import BlockMapper


mapper = BlockMapper()


def test_maps_basic_block():
    block = mapper.map_block("minecraft:stone")
    assert block.name == "minecraft:stone"
    assert block.properties == {}


def test_maps_slab_with_top_bit():
    block = mapper.map_block("minecraft:stone_slab", {"top_slot_bit": True})
    assert block.name == "minecraft:stone_slab"
    assert block.properties["type"] == "top"


def test_maps_double_waterlogged_slab():
    block = mapper.map_block("minecraft:stone_slab", {"double_slab_bit": True, "waterlogged_bit": True})
    assert block.properties["type"] == "double"
    assert block.properties["waterlogged"] == "true"


def test_maps_log_axis():
    block = mapper.map_block("minecraft:spruce_log", {"pillar_axis": "x"})
    assert block.name == "minecraft:spruce_log"
    assert block.properties["axis"] == "x"


def test_maps_trapdoor():
    block = mapper.map_block("minecraft:oak_trapdoor", {"direction": 3, "open_bit": True, "waterlogged_bit": True})
    assert block.properties["facing"] == "east"
    assert block.properties["open"] == "true"
    assert block.properties["waterlogged"] == "true"


def test_unknown_block_falls_back():
    block = mapper.map_block("minecraft:mystery_block")
    assert block.name in {"minecraft:stone", "minecraft:air"}


def test_chest_has_facing():
    block = mapper.map_block("minecraft:chest", {"facing_direction": 5})
    assert block.name == "minecraft:chest"
    assert block.properties["facing"] == "east"
