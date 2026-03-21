# minecraft_bedrock_to_java

Production-oriented Minecraft Bedrock Edition -> Java Edition converter.

## Architecture

```text
minecraft_bedrock_to_java/
├── main.py
├── config.py
├── converter/
│   ├── anvil_region.py
│   ├── bedrock_chunk_parser.py
│   ├── bedrock_key_parser.py
│   ├── bedrock_reader.py
│   ├── biome_mapper.py
│   ├── block_entity_mapper.py
│   ├── block_mapper.py
│   ├── entity_mapper.py
│   ├── heightmaps.py
│   ├── java_writer.py
│   ├── logger.py
│   ├── nbt_helpers.py
│   ├── utils.py
│   ├── versioning.py
│   └── world_model.py
└── tests/
```

## Highlights

- Expanded Bedrock key detection through `bedrock_key_parser.py`.
- Dimension-aware chunk routing for overworld, Nether and End.
- Best-effort conversion of block entities, entities and scheduled ticks from structured Bedrock payloads.
- Bedrock biome ID -> Java biome name conversion with section biome palettes.
- Version profiles for Java 1.20, 1.20.1, 1.20.4 and 1.21.
- More complete block state mapping for slabs, waterlogging, trapdoors, stairs and logs.
- Motion-blocking and world-surface heightmaps using dedicated logic.
- Richer `level.dat` with seed, difficulty, gamerules and version metadata.

## CLI

```bash
python main.py --input "/path/to/bedrock_world" --output "/path/to/java_world" --java-version 1.20.4
```

## Current constraints

- Bedrock binary NBT-like payloads for entities/block entities are still handled best-effort; JSON/gzipped JSON payloads are supported explicitly.
- Many Bedrock-only features still need per-version reverse engineering.
- Modern Java chunk format is targeted for 1.20+ profiles; older versions are not supported.
