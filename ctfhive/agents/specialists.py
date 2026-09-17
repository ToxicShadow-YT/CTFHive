from __future__ import annotations

from dataclasses import dataclass

from .classifier import Category


@dataclass(frozen=True)
class Specialist:
    category: Category
    name: str
    first_tools: tuple[str, ...]
    rationale: str


SPECIALISTS = {
    Category.WEB: Specialist(Category.WEB, "web", ("curl",), "inspect headers, source, robots, and endpoints before testing hypotheses"),
    Category.PWN: Specialist(Category.PWN, "pwn", ("file", "checksec"), "identify the binary and mitigations before crash or exploit analysis"),
    Category.REV: Specialist(Category.REV, "reverse", ("file", "strings", "readelf"), "identify format, strings, symbols, and validation paths first"),
    Category.CRYPTO: Specialist(Category.CRYPTO, "crypto", ("file", "strings", "openssl"), "classify encoding, hashing, classical, or modern cryptography before solving"),
    Category.FORENSICS: Specialist(Category.FORENSICS, "forensics", ("file", "strings", "exiftool"), "establish metadata, containers, and recursive extraction evidence"),
    Category.STEGO: Specialist(Category.STEGO, "stego", ("file", "strings", "pngcheck", "zsteg"), "inspect structure and metadata before extraction or decoding"),
    Category.OSINT: Specialist(Category.OSINT, "osint", ("strings",), "extract clues before selecting narrowly relevant network tools"),
    Category.MISC: Specialist(Category.MISC, "misc", ("file", "strings"), "inventory artifacts and use evidence to choose the next path"),
}
