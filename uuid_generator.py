from __future__ import annotations

import argparse
import uuid
from pathlib import Path


DEFAULT_UUID_PATH = Path(__file__).resolve().with_name(".app_uuid")


def get_or_create_uuid(path: str | Path = DEFAULT_UUID_PATH, regenerate: bool = False) -> str:
    uuid_path = Path(path)
    if uuid_path.exists() and not regenerate:
        existing = uuid_path.read_text(encoding="utf-8").strip()
        if existing:
            return existing

    new_uuid = uuid.uuid4().hex
    uuid_path.write_text(f"{new_uuid}\n", encoding="utf-8")
    return new_uuid


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate or fetch the app UUID.")
    parser.add_argument("--regenerate", action="store_true", help="Replace the existing UUID with a new one.")
    parser.add_argument("--path", type=Path, default=DEFAULT_UUID_PATH, help="Location of the UUID file.")
    args = parser.parse_args()

    print(get_or_create_uuid(args.path, regenerate=args.regenerate))


if __name__ == "__main__":
    main()

