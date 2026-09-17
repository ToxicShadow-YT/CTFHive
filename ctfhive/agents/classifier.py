from __future__ import annotations

from enum import StrEnum

from ctfhive.intake import Challenge


class Category(StrEnum):
    WEB = "web"
    PWN = "pwn"
    REV = "rev"
    CRYPTO = "crypto"
    FORENSICS = "forensics"
    STEGO = "stego"
    OSINT = "osint"
    MISC = "misc"


def classify(challenge: Challenge, hint: str | None = None) -> Category:
    value = f"{hint or ''} {challenge.name} {' '.join(record.relative_path for record in challenge.files)}".lower()
    scores = {category: 0 for category in Category}
    keywords = {
        Category.WEB: ("web", "http", "url", "server", "php", "html"),
        Category.PWN: ("pwn", "exploit", "elf", "binary", "buffer"),
        Category.REV: ("rev", "reverse", "exe", "assembly", " crack"),
        Category.CRYPTO: ("crypto", "rsa", "cipher", "hash", "encrypt"),
        Category.FORENSICS: ("forensic", "pcap", "memory", "dump", "disk", "zip"),
        Category.STEGO: ("stego", "image", "png", "jpg", "audio", "hidden"),
        Category.OSINT: ("osint", "social", "username", "domain"),
    }
    for category, terms in keywords.items():
        scores[category] = sum(value.count(term) for term in terms)
    if challenge.name.lower().startswith(("rev", "reverse")):
        scores[Category.REV] += 2
    return max(scores, key=scores.get) if max(scores.values()) else Category.MISC
