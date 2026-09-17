from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolSource:
    name: str
    repository: str
    install: str
    note: str


GIT_TOOL_SOURCES: tuple[ToolSource, ...] = (
    ToolSource("pwntools", "https://github.com/Gallopsled/pwntools", "python3 -m pip install pwntools", "Exploit-development toolkit; use only in an isolated challenge workspace."),
    ToolSource("angr", "https://github.com/angr/angr", "python3 -m pip install angr", "Binary analysis and symbolic execution."),
    ToolSource("ROPgadget", "https://github.com/JonathanSalwan/ROPgadget", "python3 -m pip install ROPgadget", "ROP gadget discovery."),
    ToolSource("ropper", "https://github.com/sashs/Ropper", "python3 -m pip install ropper", "ROP and binary gadget analysis."),
    ToolSource("volatility3", "https://github.com/volatilityfoundation/volatility3", "python3 -m pip install volatility3", "Memory forensics framework."),
    ToolSource("zsteg", "https://github.com/zed-0xff/zsteg", "gem install zsteg", "PNG/BMP steganography analysis; Ruby tool."),
    ToolSource("seccomp-tools", "https://github.com/david942j/seccomp-tools", "gem install seccomp-tools", "Seccomp policy inspection."),
    ToolSource("RsaCtfTool", "https://github.com/RsaCtfTool/RsaCtfTool", "python3 -m pip install RsaCtfTool", "RSA CTF analysis; verify results independently."),
    ToolSource("Ghidra", "https://github.com/NationalSecurityAgency/ghidra", "Install the official release package", "Reverse engineering suite; do not execute project source from a challenge."),
)


def source_for(tool_name: str) -> ToolSource | None:
    return next((source for source in GIT_TOOL_SOURCES if source.name.lower() == tool_name.lower()), None)
