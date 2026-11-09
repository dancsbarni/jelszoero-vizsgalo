"""Jellemzőkinyerés a gépi tanuló modellekhez.

Két reprezentációt használunk:

1. **Kézzel tervezett numerikus jellemzők** (``extract_features``):
   hossz, karakterosztályok száma és aránya, egyedi karakterek aránya,
   Shannon-entrópia, leghosszabb ismétlés, sorozatok száma stb.
2. **Karakter n-gramok TF-IDF súlyozással** (az ``ml_model`` modulban,
   scikit-learn ``TfidfVectorizer``-rel) – ez a szövegosztályozásban
   bevett módszer, és a jelszavak "kinézetét" tanulja meg.
"""

from __future__ import annotations

import math
import re
from collections import Counter

import numpy as np

from .rules import SPECIAL_CHARS, find_keyboard_patterns, find_sequences

FEATURE_NAMES = [
    "hossz",
    "kisbetuk",
    "nagybetuk",
    "szamjegyek",
    "specialis",
    "nem_ascii",
    "karakterosztalyok",
    "kisbetu_arany",
    "nagybetu_arany",
    "szamjegy_arany",
    "specialis_arany",
    "egyedi_karakterek",
    "egyedi_arany",
    "shannon_entropia",
    "leghosszabb_ismetles",
    "sorozatok",
    "billentyuzetmintak",
    "csak_betu",
    "csak_szam",
    "nagybetuvel_kezd",
    "szammal_vegzodik",
    "evszamot_tartalmaz",
    "maganhangzo_arany",
]

_VOWELS = set("aeiouáéíóöőúüű")


def shannon_entropy(text: str) -> float:
    """Karakterenkénti Shannon-entrópia (bit)."""
    if not text:
        return 0.0
    counts = Counter(text)
    n = len(text)
    return -sum(c / n * math.log2(c / n) for c in counts.values())


def longest_run(text: str) -> int:
    best = cur = 0
    prev = None
    for c in text:
        cur = cur + 1 if c == prev else 1
        best = max(best, cur)
        prev = c
    return best


def extract_features(password: str) -> list[float]:
    """Egy jelszó numerikus jellemzővektora (sorrend: ``FEATURE_NAMES``)."""
    pw = str(password)
    n = len(pw)
    lower = sum(c.islower() and c.isascii() for c in pw)
    upper = sum(c.isupper() and c.isascii() for c in pw)
    digit = sum(c.isdigit() for c in pw)
    special = sum(c in SPECIAL_CHARS for c in pw)
    non_ascii = sum(not c.isascii() for c in pw)
    classes = sum(x > 0 for x in (lower, upper, digit, special, non_ascii))
    unique = len(set(pw))
    letters = [c for c in pw.lower() if c.isalpha()]
    vowels = sum(c in _VOWELS for c in letters)
    d = max(n, 1)
    return [
        n,
        lower,
        upper,
        digit,
        special,
        non_ascii,
        classes,
        lower / d,
        upper / d,
        digit / d,
        special / d,
        unique,
        unique / d,
        shannon_entropy(pw),
        longest_run(pw),
        len(find_sequences(pw)),
        len(find_keyboard_patterns(pw)) if n <= 64 else 0,
        float(n > 0 and pw.isalpha()),
        float(n > 0 and pw.isdigit()),
        float(n > 0 and pw[0].isupper()),
        float(n > 0 and pw[-1].isdigit()),
        float(bool(re.search(r"(19\d{2}|20[0-3]\d)", pw))),
        vowels / max(len(letters), 1),
    ]


def feature_matrix(passwords) -> np.ndarray:
    """Jellemzőmátrix egy jelszólistából."""
    return np.array([extract_features(p) for p in passwords], dtype=float)
