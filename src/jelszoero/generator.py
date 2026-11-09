"""Erős jelszó és jelmondat generálása kriptográfiailag biztonságos
véletlenszámokkal (``secrets`` modul – a ``random`` modul erre NEM alkalmas)."""

from __future__ import annotations

import secrets
import string

from .wordlists import PASSPHRASE_WORDS

SYMBOLS = "!@#$%&*()-_=+[]{};:,.?"
AMBIGUOUS = set("Il1O0o")


def generate_password(length: int = 16, use_symbols: bool = True,
                      avoid_ambiguous: bool = True) -> str:
    """Véletlen jelszó, amely minden kiválasztott karakterosztályból tartalmaz legalább egyet."""
    if length < 4:
        raise ValueError("A jelszó hossza legalább 4 legyen.")
    groups = [string.ascii_lowercase, string.ascii_uppercase, string.digits]
    if use_symbols:
        groups.append(SYMBOLS)
    if avoid_ambiguous:
        groups = ["".join(c for c in g if c not in AMBIGUOUS) for g in groups]
    alphabet = "".join(groups)
    while True:
        pw = [secrets.choice(alphabet) for _ in range(length)]
        if all(any(c in g for c in pw) for g in groups):
            return "".join(pw)


def generate_passphrase(words: int = 5, separator: str = "-", add_number: bool = True) -> str:
    """Véletlen szavakból álló, könnyen megjegyezhető jelmondat."""
    chosen = [secrets.choice(PASSPHRASE_WORDS) for _ in range(words)]
    phrase = separator.join(chosen)
    if add_number:
        phrase += str(secrets.randbelow(90) + 10)
    return phrase
