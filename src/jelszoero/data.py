"""Adatbetöltés és tartalék adatgenerálás.

**Elsődleges adatforrás:** a Kaggle *Password Strength Classifier Dataset*
(``data.csv``, oszlopok: ``password,strength``; 0 = gyenge, 1 = közepes,
2 = erős). A fájlban néhány jelszó vesszőt is tartalmaz, ezért a sorokat
saját, hibatűrő módon olvassuk be: az **utolsó** vessző utáni rész a címke,
minden előtte lévő a jelszó.

**Tartalék adat:** ha a CSV nem érhető el, a ``generate_fallback_dataset``
függvény mesterséges, címkézett jelszavakat állít elő. A címkék a jelszó
*előállítási módjából* adódnak (pl. gyakori jelszó → gyenge, 16 karakteres
véletlen jelszó → erős), nem a szabályalapú értékelőből, így a két módszer
összehasonlítása nem körkörös.
"""

from __future__ import annotations

import random
import string
from pathlib import Path

import pandas as pd

from .wordlists import COMMON_PASSWORDS, DICTIONARY_WORDS, PASSPHRASE_WORDS

VALID_LABELS = {0, 1, 2}


def load_kaggle_csv(path: str | Path, max_rows: int | None = None, seed: int = 42) -> pd.DataFrame:
    """A Kaggle ``data.csv`` hibatűrő beolvasása.

    Visszatérés: DataFrame ``password`` (str) és ``strength`` (int) oszlopokkal.
    Ha ``max_rows`` meg van adva, osztályonként arányos (rétegzett)
    véletlen mintát veszünk.
    """
    path = Path(path)
    rows: list[tuple[str, int]] = []
    skipped = 0
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line_no, line in enumerate(fh):
            line = line.rstrip("\r\n")
            if not line:
                continue
            if "," not in line:
                skipped += 1
                continue
            pw, label = line.rsplit(",", 1)
            label = label.strip().strip('"')
            if line_no == 0 and not label.isdigit():
                continue   # fejléc
            if not label.isdigit() or int(label) not in VALID_LABELS or not pw:
                skipped += 1
                continue
            if len(pw) >= 2 and pw[0] == pw[-1] == '"':
                pw = pw[1:-1]
            rows.append((pw, int(label)))

    if not rows:
        raise ValueError(
            f"A(z) {path.name} fájlból nem sikerült érvényes sort beolvasni. "
            "Elvárt formátum: password,strength (0/1/2)."
        )

    df = pd.DataFrame(rows, columns=["password", "strength"])
    df = df.drop_duplicates(subset="password").reset_index(drop=True)
    df.attrs["skipped_rows"] = skipped
    df.attrs["source"] = str(path)

    if max_rows and len(df) > max_rows:
        frac = max_rows / len(df)
        parts = [df[df["strength"] == lab].sample(frac=frac, random_state=seed)
                 for lab in sorted(df["strength"].unique())]
        df = pd.concat(parts).sample(frac=1.0, random_state=seed).reset_index(drop=True)
        df.attrs["skipped_rows"] = skipped
        df.attrs["source"] = str(path)
    return df


# ---------------------------------------------------------------------------
# Tartalék adatgenerálás
# ---------------------------------------------------------------------------

_ALL_CHARS = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{};:,.?/"


def _weak(rng: random.Random) -> str:
    kind = rng.randint(0, 5)
    if kind == 0:
        return rng.choice(COMMON_PASSWORDS)
    if kind == 1:
        return rng.choice(DICTIONARY_WORDS) + str(rng.randint(0, 99))
    if kind == 2:
        return "".join(rng.choice(string.digits) for _ in range(rng.randint(4, 7)))
    if kind == 3:
        return "".join(rng.choice(string.ascii_lowercase) for _ in range(rng.randint(4, 7)))
    if kind == 4:
        return rng.choice(DICTIONARY_WORDS).capitalize() + str(rng.randint(1950, 2025))[:rng.randint(0, 4)]
    return "".join(rng.choice(string.ascii_lowercase + string.digits) for _ in range(rng.randint(5, 7)))


def _medium(rng: random.Random) -> str:
    kind = rng.randint(0, 4)
    if kind == 0:
        return rng.choice(DICTIONARY_WORDS) + str(rng.randint(100, 99999))
    if kind == 1:
        return "".join(rng.choice(string.ascii_lowercase + string.digits)
                       for _ in range(rng.randint(8, 12)))
    if kind == 2:
        w = rng.choice(DICTIONARY_WORDS).capitalize()
        return w + str(rng.randint(1950, 2025)) + rng.choice("!.?*")
    if kind == 3:
        return rng.choice(DICTIONARY_WORDS) + rng.choice(DICTIONARY_WORDS) + str(rng.randint(0, 99))
    return "".join(rng.choice(string.ascii_letters) for _ in range(rng.randint(8, 10)))


def _strong(rng: random.Random) -> str:
    kind = rng.randint(0, 2)
    if kind == 0:
        return "".join(rng.choice(_ALL_CHARS) for _ in range(rng.randint(12, 20)))
    if kind == 1:
        words = [rng.choice(PASSPHRASE_WORDS) for _ in range(rng.randint(4, 5))]
        return rng.choice("-_.").join(words) + str(rng.randint(0, 99))
    chars = [rng.choice(string.ascii_lowercase) for _ in range(rng.randint(10, 14))]
    for _ in range(3):
        chars[rng.randrange(len(chars))] = rng.choice(string.ascii_uppercase)
    chars += [rng.choice(string.digits), rng.choice("!@#$%&*")]
    rng.shuffle(chars)
    return "".join(chars)


def generate_fallback_dataset(n: int = 30000, seed: int = 42) -> pd.DataFrame:
    """Mesterséges, kiegyensúlyozott, címkézett jelszóadathalmaz."""
    rng = random.Random(seed)
    makers = {0: _weak, 1: _medium, 2: _strong}
    rows = []
    per_class = n // 3
    for label, maker in makers.items():
        for _ in range(per_class):
            rows.append((maker(rng), label))
    df = pd.DataFrame(rows, columns=["password", "strength"])
    df = df.drop_duplicates(subset="password").sample(frac=1.0, random_state=seed).reset_index(drop=True)
    df.attrs["source"] = "beépített tartalék (generált) adat"
    df.attrs["skipped_rows"] = 0
    return df


def load_dataset(path: str | Path | None, max_rows: int | None = None, seed: int = 42) -> pd.DataFrame:
    """Kaggle CSV, ha létezik; különben a tartalék adat."""
    if path and Path(path).exists():
        return load_kaggle_csv(path, max_rows=max_rows, seed=seed)
    return generate_fallback_dataset(seed=seed)
