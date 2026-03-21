from minecraft_bedrock_to_java.converter.bedrock_key_parser import BedrockKeyParser
from minecraft_bedrock_to_java.converter.biome_mapper import BiomeMapper
from minecraft_bedrock_to_java.converter.block_entity_mapper import BlockEntityMapper
from minecraft_bedrock_to_java.converter.entity_mapper import EntityMapper
from minecraft_bedrock_to_java.converter.versioning import VersionRegistry


def test_bedrock_key_parser_understands_dimensioned_subchunk_key():
    key = (1).to_bytes(4, 'little', signed=True) + (2).to_bytes(4, 'little', signed=True) + (-3).to_bytes(4, 'little', signed=True) + bytes([0x2F, 5])
    info = BedrockKeyParser().parse(key)
    assert info is not None
    assert info.dimension == 'the_nether'
    assert info.chunk_x == 2
    assert info.chunk_z == -3
    assert info.subchunk_y == 5


def test_biome_mapper_converts_json_volume():
    payload = b'{"3d_ids": [1, 2, 4]}'
    volume = BiomeMapper().decode_biomes(payload)
    assert volume.values[0] == 'minecraft:plains'
    assert volume.values[1] == 'minecraft:desert'
    assert volume.values[2] == 'minecraft:forest'


def test_block_entity_mapper_maps_chest_items():
    mapped = BlockEntityMapper().map_many([
        {'id': 'Chest', 'x': 1, 'y': 2, 'z': 3, 'Items': [{'Name': 'minecraft:stone', 'Count': 4, 'Slot': 1}]}
    ], 0, 0)
    assert mapped[0]['id'] == 'minecraft:chest'
    assert mapped[0]['Items'][0]['Count'] == 4


def test_entity_mapper_maps_item_entity():
    mapped = EntityMapper().map_many([
        {'identifier': 'minecraft:item', 'position': [1, 2, 3], 'Item': {'Name': 'minecraft:dirt', 'Count': 2}}
    ])
    assert mapped[0]['id'] == 'minecraft:item'
    assert mapped[0]['Item']['id'] == 'minecraft:dirt'


def test_version_registry_resolves_latest_alias():
    profile = VersionRegistry().resolve('latest')
    assert profile.name == '1.21'
