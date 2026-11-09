"""Szabályalapú jelszóerősség-értékelés.

Az értékelés alapja az **effektív entrópia** (bitben): azt becsüli, hány
próbálkozásra lenne szüksége egy okos támadónak. Egy teljesen véletlen
jelszó entrópiája ``hossz * log2(karakterkészlet)``, de az emberek által
választott jelszavakban gyakran vannak kitalálható minták (szótári szavak,
``1234``-szerű sorozatok, ``qwerty`` billentyűzetminták, évszámok,
ismétlődések). Ezeket a modul felismeri, és a jelszó adott szakaszát a
mintának megfelelő, jóval kisebb bitszámmal veszi figyelembe.

A megközelítés a Dropbox által publikált *zxcvbn* algoritmus egyszerűsített,
saját megvalósítása.
"""

from __future__ import annotations

import math
import re
import string
import unicodedata
from dataclasses import dataclass, field

from . import LEVEL_NAMES
from .wordlists import COMMON_PASSWORDS, DICTIONARY_WORDS, KEYBOARD_ROWS, PASSPHRASE_WORDS

# ---------------------------------------------------------------------------
# Segédadatok
# ---------------------------------------------------------------------------

LEET_MAP = {
    "4": "a", "@": "a", "3": "e", "1": "i", "!": "i", "0": "o",
    "$": "s", "5": "s", "7": "t", "+": "t", "8": "b", "9": "g",
}

# rang (0 = leggyakoribb) a gyorsabb kereséshez
_COMMON_RANK: dict[str, int] = {}
for _i, _pw in enumerate(COMMON_PASSWORDS):
    _COMMON_RANK.setdefault(_pw, _i)

def _plain(word: str) -> str:
    norm = unicodedata.normalize("NFKD", word.lower())
    return "".join(c for c in norm if not unicodedata.combining(c))


_DICT: set[str] = {_plain(w) for w in DICTIONARY_WORDS + PASSPHRASE_WORDS} | {
    _plain(p) for p in COMMON_PASSWORDS if p.isalpha()}
_DICT_BITS = math.log2(max(len(_DICT), 2))

SPECIAL_CHARS = set(string.punctuation + " ")

# Szintek határai (bit)
WEAK_LIMIT = 36.0
STRONG_LIMIT = 60.0
MIN_LENGTH = 8
RECOMMENDED_LENGTH = 12

# Támadási forgatókönyvek: próbálkozás / másodperc
ATTACK_SCENARIOS = {
    "online": 100 / 3600,      # korlátozott online támadás (100 próba/óra)
    "offline": 1e10,           # offline, gyors hash, GPU-farm (10 milliárd/s)
}


# ---------------------------------------------------------------------------
# Adatszerkezetek
# ---------------------------------------------------------------------------

@dataclass
class Match:
    """Egy felismert minta a jelszóban."""

    kind: str        # pl. "szótári szó", "sorozat", "ismétlés"
    start: int
    end: int         # kizáró index
    token: str
    bits: float      # ennyi bitnyi "nehézséget" képvisel a szakasz

    @property
    def length(self) -> int:
        return self.end - self.start


@dataclass
class Check:
    """Egy ellenőrzőlista-elem a felületen."""

    label: str
    passed: bool


@dataclass
class RuleResult:
    """A szabályalapú értékelés teljes eredménye."""

    password_length: int
    level: int
    level_name: str
    score: int                       # 0–100
    entropy_bits: float              # effektív entrópia
    naive_entropy_bits: float        # hossz * log2(karakterkészlet)
    pool_size: int
    crack_times: dict[str, float]    # forgatókönyv -> másodperc
    crack_times_text: dict[str, str]
    matches: list[Match] = field(default_factory=list)
    checks: list[Check] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Segédfüggvények
# ---------------------------------------------------------------------------

def strip_accents(text: str) -> str:
    """Ékezetek eltávolítása (``ő`` -> ``o``), hogy a szótárkeresés működjön."""
    norm = unicodedata.normalize("NFKD", text)
    return "".join(c for c in norm if not unicodedata.combining(c))


def deleet(text: str) -> str:
    """Leetspeak visszafejtése (``p@ssw0rd`` -> ``password``)."""
    return "".join(LEET_MAP.get(c, c) for c in text)


def normalize(text: str) -> str:
    return deleet(strip_accents(text.lower()))


def charset_pool(password: str) -> int:
    """A jelszóban használt karakterosztályok alapján becsült készletméret."""
    pool = 0
    if any(c in string.ascii_lowercase for c in password):
        pool += 26
    if any(c in string.ascii_uppercase for c in password):
        pool += 26
    if any(c.isdigit() for c in password):
        pool += 10
    if any(c in SPECIAL_CHARS for c in password):
        pool += 33
    if any(ord(c) > 127 for c in password):
        pool += 32   # ékezetes és egyéb nem ASCII karakterek
    return max(pool, 1)


def format_duration(seconds: float) -> str:
    """Másodperc -> olvasható magyar szöveg."""
    if seconds < 1:
        return "azonnal"
    units = [
        ("év", 365.25 * 24 * 3600),
        ("nap", 24 * 3600),
        ("óra", 3600),
        ("perc", 60),
        ("másodperc", 1),
    ]
    if seconds >= 365.25 * 24 * 3600 * 1e6:
        return "több millió év"
    if seconds >= 365.25 * 24 * 3600 * 1000:
        return "több ezer év"
    if seconds >= 365.25 * 24 * 3600 * 100:
        return "évszázadok"
    for name, size in units:
        if seconds >= size:
            value = round(seconds / size)
            return f"kb. {value} {name}"
    return "azonnal"


def _case_bits(token: str) -> float:
    """A kis-/nagybetű variációk extra bitjei egy szótári szónál."""
    if token.islower() or not any(c.isalpha() for c in token):
        return 0.0
    if token.isupper() or (token[0].isupper() and token[1:].islower()):
        return 1.0
    uppers = sum(c.isupper() for c in token)
    return float(min(uppers, len(token)))


# ---------------------------------------------------------------------------
# Mintafelismerők
# ---------------------------------------------------------------------------

def find_dictionary_words(password: str) -> list[Match]:
    """Szótári és gyakori jelszó-szavak keresése (leet- és ékezetfüggetlenül)."""
    matches: list[Match] = []
    norm = normalize(password)
    n = len(password)
    for i in range(n):
        for j in range(i + 4, n + 1):           # legalább 4 karakteres szavak
            word = norm[i:j]
            if word in _DICT or word in _COMMON_RANK:
                token = password[i:j]
                if word in _COMMON_RANK:
                    base = math.log2(_COMMON_RANK[word] + 2)
                else:
                    base = _DICT_BITS
                leet_subs = sum(1 for c in token if c in LEET_MAP)
                bits = base + _case_bits(token) + (1.0 if leet_subs else 0.0)
                matches.append(Match("szótári szó", i, j, token, bits))
    return matches


def find_sequences(password: str) -> list[Match]:
    """Növekvő/csökkenő sorozatok (``abcd``, ``4321``) keresése."""
    matches: list[Match] = []
    low = password.lower()
    n = len(low)
    i = 0
    while i < n - 2:
        j = i + 1
        delta = ord(low[j]) - ord(low[i])
        if delta in (1, -1) and (low[i].isalnum()):
            while j + 1 < n and ord(low[j + 1]) - ord(low[j]) == delta and low[j + 1].isalnum():
                j += 1
            length = j - i + 1
            if length >= 3:
                space = 10 if low[i].isdigit() else 26
                bits = math.log2(space) + math.log2(length) + 1
                matches.append(Match("sorozat", i, j + 1, password[i:j + 1], bits))
                i = j + 1
                continue
        i += 1
    return matches


def find_repeats(password: str) -> list[Match]:
    """Ismétlődő karakterek (``aaaa``) és részek (``abcabc``) keresése."""
    matches: list[Match] = []
    for m in re.finditer(r"(.)\1{2,}", password):
        token = m.group(0)
        bits = math.log2(charset_pool(token[0])) + math.log2(len(token))
        matches.append(Match("ismétlés", m.start(), m.end(), token, bits))
    for m in re.finditer(r"(.{2,}?)\1+", password):
        chunk = m.group(1)
        if len(set(chunk)) == 1:
            continue   # azt az előző minta már kezeli
        count = len(m.group(0)) // len(chunk)
        bits = len(chunk) * math.log2(charset_pool(chunk)) + math.log2(count)
        matches.append(Match("ismétlés", m.start(), m.end(), m.group(0), bits))
    return matches


def find_keyboard_patterns(password: str) -> list[Match]:
    """Billentyűzetsorok (``qwerty``, ``asdf``, ``yxcv``) keresése."""
    matches: list[Match] = []
    low = password.lower()
    n = len(low)
    rows = KEYBOARD_ROWS + [r[::-1] for r in KEYBOARD_ROWS]
    for i in range(n):
        best_end = 0
        for j in range(i + 4, n + 1):
            if any(low[i:j] in row for row in rows):
                best_end = j
        if best_end:
            length = best_end - i
            bits = math.log2(len(KEYBOARD_ROWS) * 10) + math.log2(length) + 1
            matches.append(Match("billentyűzetminta", i, best_end, password[i:best_end], bits))
    return matches


def find_dates(password: str) -> list[Match]:
    """Évszámok (1900–2039) és dátumok (pl. 19990415, 150499) keresése."""
    matches: list[Match] = []
    for m in re.finditer(r"(?<!\d)(19\d{2}|20[0-3]\d)(?!\d)", password):
        matches.append(Match("évszám", m.start(), m.end(), m.group(0), math.log2(140)))
    # nyolcjegyű dátum: ééééhhnn vagy nnhhéééé
    for m in re.finditer(r"(?<!\d)\d{8}(?!\d)", password):
        s = m.group(0)
        ymd = (1900 <= int(s[:4]) <= 2039 and 1 <= int(s[4:6]) <= 12 and 1 <= int(s[6:]) <= 31)
        dmy = (1 <= int(s[:2]) <= 31 and 1 <= int(s[2:4]) <= 12 and 1900 <= int(s[4:]) <= 2039)
        if ymd or dmy:
            matches.append(Match("dátum", m.start(), m.end(), s, math.log2(365 * 140)))
    # hatjegyű dátum: ééhhnn / nnhhéé
    for m in re.finditer(r"(?<!\d)\d{6}(?!\d)", password):
        s = m.group(0)
        a, b, c = int(s[:2]), int(s[2:4]), int(s[4:])
        if (1 <= b <= 12) and ((1 <= c <= 31) or (1 <= a <= 31)):
            matches.append(Match("dátum", m.start(), m.end(), s, math.log2(365 * 100)))
    return matches


def find_personal_info(password: str, personal: list[str]) -> list[Match]:
    """A felhasználó személyes adatainak (név, dátum) keresése a jelszóban."""
    matches: list[Match] = []
    norm = normalize(password)
    for item in personal:
        variants = {normalize(item)}
        digits = "".join(c for c in item if c.isdigit())
        if digits:
            variants.add(normalize(digits))   # pl. "1999.04.15" -> "19990415"
        for variant in variants:
            if len(variant) < 3:
                continue
            start = norm.find(variant)
            while start != -1:
                end = start + len(variant)
                matches.append(Match("személyes adat", start, end, password[start:end], 1.0))
                start = norm.find(variant, start + 1)
    return matches


def find_all_matches(password: str, personal: list[str] | None = None) -> list[Match]:
    matches = (
        find_dictionary_words(password)
        + find_sequences(password)
        + find_repeats(password)
        + find_keyboard_patterns(password)
        + find_dates(password)
    )
    if personal:
        matches += find_personal_info(password, personal)
    return matches


def select_matches(password: str, matches: list[Match]) -> list[Match]:
    """Nem átfedő minták kiválasztása mohó módon, a legnagyobb bitmegtakarítás szerint."""
    char_bits = math.log2(charset_pool(password))

    def saving(m: Match) -> float:
        return m.length * char_bits - m.bits

    chosen: list[Match] = []
    used = [False] * len(password)
    for m in sorted(matches, key=saving, reverse=True):
        if saving(m) <= 0:
            continue
        if any(used[m.start:m.end]):
            continue
        chosen.append(m)
        for k in range(m.start, m.end):
            used[k] = True
    return sorted(chosen, key=lambda m: m.start)


# ---------------------------------------------------------------------------
# Fő értékelő függvény
# ---------------------------------------------------------------------------

def estimate_entropy(password: str, personal: list[str] | None = None) -> tuple[float, float, list[Match]]:
    """Visszaadja: (effektív entrópia, naiv entrópia, felhasznált minták)."""
    if not password:
        return 0.0, 0.0, []
    pool = charset_pool(password)
    char_bits = math.log2(pool)
    naive = len(password) * char_bits

    norm_full = normalize(password)
    if norm_full in _COMMON_RANK or password.lower() in _COMMON_RANK:
        rank = _COMMON_RANK.get(password.lower(), _COMMON_RANK.get(norm_full, 0))
        bits = math.log2(rank + 2) + _case_bits(password)
        return bits, naive, [Match("gyakori jelszó", 0, len(password), password, bits)]

    chosen = select_matches(password, find_all_matches(password, personal))
    covered = sum(m.length for m in chosen)
    entropy = sum(m.bits for m in chosen) + (len(password) - covered) * char_bits
    # minden minta után a támadónak "ki kell találnia" a szerkezetet is
    if chosen:
        entropy += math.log2(len(chosen) + 1)
    return min(entropy, naive), naive, chosen


def classify_entropy(entropy: float, length: int) -> int:
    if length < MIN_LENGTH or entropy < WEAK_LIMIT:
        return 0
    if entropy < STRONG_LIMIT:
        return 1
    return 2


def evaluate(password: str, personal: list[str] | None = None) -> RuleResult:
    """Egy jelszó teljes szabályalapú értékelése."""
    entropy, naive, matches = estimate_entropy(password, personal)
    level = classify_entropy(entropy, len(password)) if password else 0
    score = int(round(min(100.0, entropy / 90.0 * 100.0)))

    guesses = 2 ** max(entropy - 1, 0)   # átlagosan a keresési tér fele
    crack = {name: guesses / rate for name, rate in ATTACK_SCENARIOS.items()}
    crack_text = {name: format_duration(sec) for name, sec in crack.items()}

    kinds = {m.kind for m in matches}
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in SPECIAL_CHARS or ord(c) > 127 and not c.isalpha() for c in password)
    is_common = "gyakori jelszó" in kinds

    checks = [
        Check(f"Legalább {RECOMMENDED_LENGTH} karakter", len(password) >= RECOMMENDED_LENGTH),
        Check("Kisbetű", has_lower),
        Check("Nagybetű", has_upper),
        Check("Számjegy", has_digit),
        Check("Speciális karakter", has_special),
        Check("Nem gyakori jelszó", bool(password) and not is_common),
        Check("Nincs szótári szó", bool(password) and "szótári szó" not in kinds and not is_common),
        Check("Nincs sorozat vagy billentyűzetminta",
              bool(password) and not ({"sorozat", "billentyűzetminta"} & kinds)),
        Check("Nincs ismétlődés", bool(password) and "ismétlés" not in kinds),
        Check("Nincs évszám vagy dátum", bool(password) and not ({"évszám", "dátum"} & kinds)),
        Check("Nincs személyes adat", bool(password) and "személyes adat" not in kinds),
    ]

    warnings: list[str] = []
    suggestions: list[str] = []
    if not password:
        suggestions.append("Írj be egy jelszót az értékeléshez.")
    else:
        if is_common:
            warnings.append("Ez a jelszó a leggyakoribb jelszavak között szerepel – a támadók elsőként próbálják.")
        if len(password) < MIN_LENGTH:
            warnings.append(f"Túl rövid: legalább {MIN_LENGTH}, inkább {RECOMMENDED_LENGTH}+ karakter ajánlott.")
        elif len(password) < RECOMMENDED_LENGTH:
            suggestions.append(f"Növeld a hosszt legalább {RECOMMENDED_LENGTH} karakterre – ez a leghatékonyabb lépés.")
        dict_words = [m.token for m in matches if m.kind == "szótári szó"]
        if level == 2 and dict_words:
            # erős jelszónál (pl. jelmondat) nem soroljuk fel egyenként a szavakat
            suggestions.append(f"{len(dict_words)} szótári szót tartalmaz, de a hossza és a szavak "
                               "száma miatt a becsült entrópia így is magas.")
        for m in matches:
            if m.kind == "szótári szó" and level == 2:
                continue
            if m.kind == "szótári szó":
                extra = (" – a betűcsere (pl. a→@) nem nyújt érdemi védelmet"
                         if any(c in LEET_MAP for c in m.token) else "")
                warnings.append(f"Szótári szó: „{m.token}”{extra}.")
            elif m.kind == "sorozat":
                warnings.append(f"Kitalálható sorozat: „{m.token}”.")
            elif m.kind == "billentyűzetminta":
                warnings.append(f"Billentyűzetminta: „{m.token}”.")
            elif m.kind == "ismétlés":
                warnings.append(f"Ismétlődés: „{m.token}”.")
            elif m.kind in ("évszám", "dátum"):
                warnings.append(f"{m.kind.capitalize()}: „{m.token}” – a személyes dátumok könnyen kitalálhatók.")
            elif m.kind == "személyes adat":
                warnings.append(f"Személyes adat: „{m.token}” – aki ismer téged, elsőként ezt próbálja.")
        missing = [name for name, ok in (("nagybetű", has_upper), ("számjegy", has_digit),
                                         ("speciális karakter", has_special)) if not ok]
        if missing and level < 2:
            suggestions.append("Használj többféle karaktert is: " + ", ".join(missing) + ".")
        if level < 2:
            suggestions.append("Jó választás egy 5–6 véletlenszerűen (nem te) választott szóból álló jelmondat – használd a generátort.")
            suggestions.append("Ne használd újra ugyanazt a jelszót több oldalon; egy jelszókezelő sokat segít.")
        else:
            suggestions.append("Erős jelszó. Tárold jelszókezelőben, és ne használd máshol.")

    return RuleResult(
        password_length=len(password),
        level=level,
        level_name=LEVEL_NAMES[level],
        score=score,
        entropy_bits=round(entropy, 1),
        naive_entropy_bits=round(naive, 1),
        pool_size=charset_pool(password) if password else 0,
        crack_times=crack,
        crack_times_text=crack_text,
        matches=matches,
        checks=checks,
        warnings=list(dict.fromkeys(warnings)),
        suggestions=suggestions,
    )
