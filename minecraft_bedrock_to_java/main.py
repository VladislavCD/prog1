from __future__ import annotations

import argparse
import sys
from pathlib import Path

from minecraft_bedrock_to_java.config import DEFAULT_CHUNK_LIMIT, DEFAULT_JAVA_VERSION, DEFAULT_LOG_LEVEL
from minecraft_bedrock_to_java.converter.bedrock_reader import BedrockWorldReader
from minecraft_bedrock_to_java.converter.block_mapper import BlockMapper
from minecraft_bedrock_to_java.converter.java_writer import JavaWorldWriter
from minecraft_bedrock_to_java.converter.logger import configure_logging, get_logger
from minecraft_bedrock_to_java.converter.versioning import VersionRegistry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert a Minecraft Bedrock world into a Java Edition world (best-effort production-oriented build)."
    )
    parser.add_argument("--input", required=True, help="Path to the Bedrock world directory")
    parser.add_argument("--output", required=True, help="Path to the destination Java world directory")
    parser.add_argument(
        "--chunk-limit",
        type=int,
        default=DEFAULT_CHUNK_LIMIT,
        help="Optional maximum number of chunks to convert",
    )
    parser.add_argument(
        "--log-level",
        default=DEFAULT_LOG_LEVEL,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )
    parser.add_argument(
        "--java-version",
        default=DEFAULT_JAVA_VERSION,
        help="Target Java version profile, e.g. 1.20, 1.20.1, 1.20.4, 1.21",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    configure_logging(args.log_level)
    logger = get_logger(__name__)

    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    try:
        version_profile = VersionRegistry().resolve(args.java_version)
        reader = BedrockWorldReader(input_path)
        mapper = BlockMapper()
        java_world = reader.read_world(chunk_limit=args.chunk_limit, mapper=mapper)

        writer = JavaWorldWriter(output_path, version_profile=version_profile)
        writer.write_world(java_world)
    except Exception as exc:  # pragma: no cover - top-level safety net
        logger.exception("Conversion failed: %s", exc)
        return 1

    logger.info(
        "Conversion completed successfully for Java %s: %s -> %s",
        args.java_version,
        input_path,
        output_path,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
