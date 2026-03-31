from __future__ import annotations

import os
from configparser import ConfigParser
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union


DEFAULT_SETTINGS = {
    "screen settings": {
        "resolution": "1920x1080",
        "colorblind": "Normal",
    },
    "mouse settings": {
        "sens": "5.0",
        "zoom_sens": "1.0",
        "auto_fire": "1",
        "ads_only": "0",
    },
    "voice settings": {
        "volume": "80",
        "rate": "7",
    },
    "other settings": {
        "debug": "0",
        "gold_optics": "0",
    },
    "trigger settings": {
        "trigger_only": "0",
        "trigger_button": "Capslock",
    },
}


RESOLUTION_ORDER = [
    "1280x720",
    "1366x768",
    "1600x900",
    "1680x1050",
    "1728x1080",
    "1920x1080",
    "1920x1200",
    "2560x1440",
    "3840x1440",
    "3840x1600",
    "3840x2160",
    "customized",
]


@dataclass
class AppSettings:
    resolution: str = "1920x1080"
    colorblind: str = "Normal"
    sens: float = 5.0
    zoom_sens: float = 1.0
    auto_fire: bool = True
    ads_only: bool = False
    volume: int = 80
    rate: int = 7
    debug: bool = False
    gold_optics: bool = False
    trigger_only: bool = False
    trigger_button: str = "Capslock"

    @classmethod
    def from_parser(cls, parser: ConfigParser) -> "AppSettings":
        return cls(
            resolution=_read_str(parser, "screen settings", "resolution", "1920x1080"),
            colorblind=_read_str(parser, "screen settings", "colorblind", "Normal"),
            sens=_read_float(parser, "mouse settings", "sens", 5.0),
            zoom_sens=_read_float(parser, "mouse settings", "zoom_sens", 1.0),
            auto_fire=_read_bool(parser, "mouse settings", "auto_fire", True),
            ads_only=_read_bool(parser, "mouse settings", "ads_only", False),
            volume=_read_int(parser, "voice settings", "volume", 80),
            rate=_read_int(parser, "voice settings", "rate", 7),
            debug=_read_bool(parser, "other settings", "debug", False),
            gold_optics=_read_bool(parser, "other settings", "gold_optics", False),
            trigger_only=_read_bool(parser, "trigger settings", "trigger_only", False),
            trigger_button=_read_str(parser, "trigger settings", "trigger_button", "Capslock"),
        )

    def to_ini_sections(self) -> Dict[str, Dict[str, str]]:
        values = asdict(self)
        return {
            "screen settings": {
                "resolution": _quote(values["resolution"]),
                "colorblind": _quote(values["colorblind"]),
            },
            "mouse settings": {
                "sens": _quote(f"{values['sens']:.1f}"),
                "zoom_sens": _quote(f"{values['zoom_sens']:.1f}"),
                "auto_fire": _quote(_bool_to_ini(values["auto_fire"])),
                "ads_only": _quote(_bool_to_ini(values["ads_only"])),
            },
            "voice settings": {
                "volume": _quote(str(values["volume"])),
                "rate": _quote(str(values["rate"])),
            },
            "other settings": {
                "debug": _quote(_bool_to_ini(values["debug"])),
                "gold_optics": _quote(_bool_to_ini(values["gold_optics"])),
            },
            "trigger settings": {
                "trigger_only": _quote(_bool_to_ini(values["trigger_only"])),
                "trigger_button": _quote(values["trigger_button"]),
            },
        }


def load_settings(path: Union[str, Path]) -> AppSettings:
    settings_path = Path(path)
    if not settings_path.exists():
        save_settings(settings_path, AppSettings())
        return AppSettings()

    encoding_candidates = ["utf-16", "utf-8-sig", "utf-8"]
    for encoding in encoding_candidates:
        parser = ConfigParser(interpolation=None)
        parser.optionxform = str
        try:
            with settings_path.open("r", encoding=encoding) as handle:
                parser.read_file(handle)
            return AppSettings.from_parser(parser)
        except (UnicodeError, Exception):
            continue

    return AppSettings()


def save_settings(path: Union[str, Path], settings: AppSettings) -> None:
    settings_path = Path(path)
    parser = ConfigParser(interpolation=None)
    parser.optionxform = str

    for section, values in DEFAULT_SETTINGS.items():
        parser[section] = dict(values)

    for section, values in settings.to_ini_sections().items():
        if section not in parser:
            parser[section] = {}
        parser[section].update(values)

    try:
        with settings_path.open("w", encoding="utf-16", newline="\r\n") as handle:
            parser.write(handle)
    except Exception as e:
        print(f"Error saving settings: {e}")


def list_resolutions(resolution_dir: Union[str, Path]) -> List[str]:
    res_path = Path(resolution_dir)
    if not res_path.exists() or not res_path.is_dir():
        return []

    available = {
        path.stem
        for path in res_path.glob("*.ini")
        if path.is_file()
    }
    ordered = [name for name in RESOLUTION_ORDER if name in available]
    extras = sorted(available.difference(ordered))
    return ordered + extras


def _quote(value: str) -> str:
    return f'"{value}"'


def _unquote(value: str) -> str:
    text = value.strip()
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        return text[1:-1]
    return text


def _read_str(parser: ConfigParser, section: str, option: str, default: str) -> str:
    if parser.has_option(section, option):
        return _unquote(parser.get(section, option))
    return default


def _read_bool(parser: ConfigParser, section: str, option: str, default: bool) -> bool:
    return _read_str(parser, section, option, "1" if default else "0") == "1"


def _read_int(parser: ConfigParser, section: str, option: str, default: int) -> int:
    try:
        return int(_read_str(parser, section, option, str(default)))
    except ValueError:
        return default


def _read_float(parser: ConfigParser, section: str, option: str, default: float) -> float:
    try:
        return float(_read_str(parser, section, option, str(default)))
    except ValueError:
        return default


def _bool_to_ini(value: bool) -> str:
    return "1" if value else "0"
