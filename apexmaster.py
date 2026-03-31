from __future__ import annotations

import argparse
import json
from configparser import ConfigParser
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
PATTERN_DIR = ROOT_DIR / "Pattern"
RESOLUTION_DIR = ROOT_DIR / "Resolution"


WEAPON_METADATA = {
    "r99": {"label": "R99", "category": "light", "pattern_file": "R99.txt"},
    "r301": {"label": "R301", "category": "light", "pattern_file": "R301.txt"},
    "flatline": {"label": "FLATLINE", "category": "heavy", "pattern_file": "Flatline.txt"},
    "spitfire": {"label": "SPITFIRE", "category": "light", "pattern_file": "Spitfire.txt"},
    "lstar": {"label": "LSTAR", "category": "energy", "pattern_file": "Lstar.txt"},
    "devotion": {"label": "DEVOTION", "category": "energy", "pattern_file": "Devotion.txt"},
    "devotion_turbo": {"label": "DEVOTION TURBO", "category": "energy", "pattern_file": "DevotionTurbo.txt"},
    "volt": {"label": "VOLT", "category": "energy", "pattern_file": "Volt.txt"},
    "havoc": {"label": "HAVOC", "category": "energy", "pattern_file": "Havoc.txt"},
    "nemesis": {"label": "NEMESIS", "category": "energy", "pattern_file": "Nemesis.txt"},
    "nemesis_charged": {"label": "NEMESIS CHARGED", "category": "energy", "pattern_file": "NemesisCharged.txt"},
    "prowler": {"label": "PROWLER", "category": "supply_drop", "pattern_file": "Prowler.txt"},
    "hemlok": {"label": "HEMLOK", "category": "heavy", "pattern_file": "Hemlok.txt"},
    "hemlok_auto": {"label": "HEMLOK AUTO", "category": "heavy", "pattern_file": "HemlokAuto.txt"},
    "re45": {"label": "RE45", "category": "light", "pattern_file": "RE45.txt"},
    "alternator": {"label": "ALTERNATOR", "category": "light", "pattern_file": "Alternator.txt"},
    "p2020": {"label": "P2020", "category": "light", "pattern_file": "P2020.txt"},
    "rampage": {"label": "RAMPAGE", "category": "heavy", "pattern_file": "Rampage.txt"},
    "rampage_amp": {"label": "RAMPAGE AMP", "category": "heavy", "pattern_file": "RampageAmp.txt"},
    "wingman": {"label": "WINGMAN", "category": "sniper", "pattern_file": "Wingman.txt"},
    "g7": {"label": "G7", "category": "light", "pattern_file": "G7.txt"},
    "car": {"label": "CAR", "category": "special", "pattern_file": "CAR.txt"},
    "3030": {"label": "3030", "category": "heavy", "pattern_file": "3030.txt"},
    "sella": {"label": "SELLA", "category": "special", "pattern_file": "Sella.txt"},
}


@dataclass(frozen=True)
class CompensationStep:
    dx: int
    dy: int
    interval_ms: float


@dataclass(frozen=True)
class WeaponPattern:
    key: str
    label: str
    category: str
    file_path: Path
    steps: list[CompensationStep]

    @property
    def step_count(self) -> int:
        return len(self.steps)

    @property
    def total_dx(self) -> int:
        return sum(step.dx for step in self.steps)

    @property
    def total_dy(self) -> int:
        return sum(step.dy for step in self.steps)

    @property
    def total_duration_ms(self) -> float:
        return round(sum(step.interval_ms for step in self.steps), 2)


@dataclass(frozen=True)
class ResolutionProfile:
    name: str
    file_path: Path
    weapon1: tuple[int, int] | None
    weapon2: tuple[int, int] | None
    markers: dict[str, tuple[int, ...]]


def load_pattern(pattern_key: str) -> WeaponPattern:
    key = _normalize_weapon_key(pattern_key)
    metadata = WEAPON_METADATA[key]
    file_path = PATTERN_DIR / metadata["pattern_file"]
    steps: list[CompensationStep] = []

    with file_path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            parts = [part.strip() for part in line.split(",")]
            if len(parts) != 3:
                raise ValueError(f"Invalid pattern row in {file_path}:{line_number}")
            steps.append(
                CompensationStep(
                    dx=int(float(parts[0])),
                    dy=int(float(parts[1])),
                    interval_ms=float(parts[2]),
                )
            )

    return WeaponPattern(
        key=key,
        label=metadata["label"],
        category=metadata["category"],
        file_path=file_path,
        steps=steps,
    )


def load_all_patterns() -> dict[str, WeaponPattern]:
    return {key: load_pattern(key) for key in WEAPON_METADATA}


def load_resolution_profile(name: str) -> ResolutionProfile:
    profile_name = name.removesuffix(".ini")
    file_path = RESOLUTION_DIR / f"{profile_name}.ini"
    if not file_path.exists():
        raise FileNotFoundError(f"Unknown resolution profile: {profile_name}")

    parser = ConfigParser(interpolation=None)
    parser.optionxform = str
    parser.read(file_path, encoding="utf-8")

    if "pixels" not in parser:
        raise ValueError(f"Missing [pixels] section in {file_path}")

    markers: dict[str, tuple[int, ...]] = {}
    weapon1 = None
    weapon2 = None
    for key, raw_value in parser["pixels"].items():
        values = _parse_csv_numbers(raw_value)
        if key == "weapon1":
            weapon1 = _expect_pair(values, file_path, key)
        elif key == "weapon2":
            weapon2 = _expect_pair(values, file_path, key)
        else:
            markers[key] = tuple(values)

    return ResolutionProfile(
        name=profile_name,
        file_path=file_path,
        weapon1=weapon1,
        weapon2=weapon2,
        markers=markers,
    )


def list_resolution_profiles() -> list[str]:
    return sorted(path.stem for path in RESOLUTION_DIR.glob("*.ini") if path.is_file())


def build_summary() -> dict[str, object]:
    patterns = load_all_patterns()
    return {
        "weapon_count": len(patterns),
        "resolution_profiles": list_resolution_profiles(),
        "weapons": [
            {
                "key": pattern.key,
                "label": pattern.label,
                "category": pattern.category,
                "steps": pattern.step_count,
                "total_dx": pattern.total_dx,
                "total_dy": pattern.total_dy,
                "total_duration_ms": pattern.total_duration_ms,
            }
            for pattern in sorted(patterns.values(), key=lambda item: item.label)
        ],
    }


def _normalize_weapon_key(value: str) -> str:
    normalized = value.strip().lower().replace(" ", "_")
    if normalized not in WEAPON_METADATA:
        known = ", ".join(sorted(WEAPON_METADATA))
        raise KeyError(f"Unknown weapon '{value}'. Known keys: {known}")
    return normalized


def _parse_csv_numbers(raw_value: str) -> list[int]:
    text = raw_value.strip().strip('"')
    if not text:
        return []
    return [int(part.strip()) for part in text.split(",") if part.strip()]


def _expect_pair(values: list[int], file_path: Path, key: str) -> tuple[int, int]:
    if len(values) != 2:
        raise ValueError(f"Expected exactly 2 integers for {key} in {file_path}")
    return values[0], values[1]


def _to_json(data: object) -> str:
    return json.dumps(data, indent=2, default=_json_default)


def _json_default(value: object) -> object:
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Safe Python port of the data/model portions of apexmaster.ahk."
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("summary", help="Show a summary of known patterns and resolution profiles.")

    weapon_parser = subparsers.add_parser("weapon", help="Show metadata and stats for one weapon pattern.")
    weapon_parser.add_argument("name", help="Weapon key, such as r99, hemlok_auto, or devotion_turbo.")

    resolution_parser = subparsers.add_parser("resolution", help="Show one resolution profile.")
    resolution_parser.add_argument("name", help="Resolution profile name, such as 1920x1080.")

    args = parser.parse_args()

    command = args.command or "summary"
    if command == "summary":
        print(_to_json(build_summary()))
        return
    if command == "weapon":
        print(_to_json(load_pattern(args.name)))
        return
    if command == "resolution":
        print(_to_json(load_resolution_profile(args.name)))
        return

    parser.error(f"Unsupported command: {command}")


if __name__ == "__main__":
    main()
