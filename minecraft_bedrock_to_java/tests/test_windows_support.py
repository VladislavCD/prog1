from pathlib import Path
from unittest.mock import patch

from minecraft_bedrock_to_java.converter.leveldb_interface import LevelDBFactory, LevelDBWrapper


class DummyLevelDB:
    def RangeIter(self):
        yield b'key', b'value'


class DummyPlyvelDB:
    def iterator(self, include_value=True):
        yield b'key2', b'value2'


class DummyModule:
    def __init__(self, db_cls_name, instance):
        setattr(self, db_cls_name, lambda *args, **kwargs: instance)


def test_factory_uses_leveldb_backend_when_plyvel_missing():
    with patch('importlib.util.find_spec', side_effect=lambda name: object() if name == 'leveldb' else None), patch(
        'importlib.import_module', return_value=DummyModule('LevelDB', DummyLevelDB())
    ):
        wrapper = LevelDBFactory().create(Path('C:/world/db'))
        assert wrapper.backend_name == 'leveldb'
        assert list(wrapper) == [(b'key', b'value')]


def test_wrapper_iterates_plyvel_style_iterator():
    wrapper = LevelDBWrapper('plyvel', DummyPlyvelDB())
    assert list(wrapper) == [(b'key2', b'value2')]
