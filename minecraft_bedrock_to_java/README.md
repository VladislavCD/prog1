# minecraft_bedrock_to_java

Production-oriented Minecraft Bedrock Edition -> Java Edition converter with Windows-first usage notes.

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
│   ├── leveldb_interface.py
│   ├── logger.py
│   ├── nbt_helpers.py
│   ├── utils.py
│   ├── versioning.py
│   └── world_model.py
└── tests/
```

## Windows support

- Paths are handled through `pathlib`, so CLI arguments can use Windows paths like `C:\Users\name\AppData\Local\Packages\...`.
- LevelDB access now uses a backend factory: it prefers `plyvel` when available and falls back to `leveldb`, which is more practical on Windows.
- The converter no longer assumes shell commands such as `source`; Windows PowerShell/CMD examples are documented below.

## Install

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Windows CMD

```bat
python -m venv .venv
.venv\\Scripts\\activate.bat
pip install -r requirements.txt
```

### Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

### Windows example

```powershell
python main.py --input "C:\BedrockWorlds\MyWorld" --output "D:\ConvertedWorlds\MyJavaWorld" --java-version 1.20.4
```

### Linux / macOS example

```bash
python main.py --input "/path/to/bedrock_world" --output "/path/to/java_world" --java-version 1.20.4
```

## Current constraints

- Bedrock binary NBT-like payloads for entities/block entities are still handled best-effort; JSON/gzipped JSON payloads are supported explicitly.
- On Windows you may need `leveldb` or `plyvel-wheels`; on Linux/macOS `plyvel` remains the preferred backend.
- Many Bedrock-only features still need per-version reverse engineering.
- Modern Java chunk format is targeted for 1.20+ profiles; older versions are not supported.
