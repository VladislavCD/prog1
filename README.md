# prog1

This repository contains the `minecraft_bedrock_to_java` converter project.

## Quick start

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py --input "C:\path\to\bedrock_world" --output "C:\path\to\java_world"
```

### Windows CMD

```bat
python -m venv .venv
.venv\\Scripts\\activate.bat
pip install -r requirements.txt
python main.py --input "C:\path\to\bedrock_world" --output "C:\path\to\java_world"
```

### Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py --input "/path/to/bedrock_world" --output "/path/to/java_world"
```

See the full project documentation in `minecraft_bedrock_to_java/README.md`.
