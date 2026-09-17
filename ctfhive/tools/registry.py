from __future__ import annotations

from .base import Safety, ToolSpec


_GROUPS = {
    "general": ["file", "strings", "xxd", "grep", "rg", "find", "curl", "wget", "python3", "git", "gh", "jq", "tar", "unzip", "7z"],
    "binary": ["readelf", "objdump", "checksec", "gdb", "radare2", "ROPgadget", "angr", "pwntools"],
    "web": ["curl", "nmap", "ffuf", "httpx", "nuclei"],
    "forensics": ["exiftool", "binwalk", "foremost", "tshark", "volatility3", "pngcheck"],
    "stego": ["zsteg", "steghide", "stegseek", "magick", "tesseract"],
    "crypto": ["python", "openssl", "z3", "sage", "RsaCtfTool"],
    "osint": ["spiderfoot", "holehe", "theHarvester", "sherlock"],
}


def default_registry() -> dict[str, ToolSpec]:
    registry: dict[str, ToolSpec] = {}
    for category, names in _GROUPS.items():
        for name in names:
            safety = Safety.NETWORK if category in {"web", "osint"} else Safety.READ_ONLY
            registry[name] = ToolSpec(name, category, name, f"{name} capability", safety=safety)
    return registry


class ToolRegistry:
    def __init__(self, tools: dict[str, ToolSpec] | None = None):
        self._tools = tools or default_registry()

    def get(self, name: str) -> ToolSpec:
        return self._tools[name]

    def all(self) -> list[ToolSpec]:
        return sorted(self._tools.values(), key=lambda tool: (tool.category, tool.name))

    def status(self) -> list[tuple[ToolSpec, str | None]]:
        return [(tool, tool.availability()) for tool in self.all()]
