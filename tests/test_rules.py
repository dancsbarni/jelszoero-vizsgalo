"""A szabályalapú értékelő egységtesztjei.  Futtatás:  python -m pytest"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest  # noqa: E402

from jelszoero.rules import (  # noqa: E402
    charset_pool,
    deleet,
    evaluate,
    find_dates,
    find_keyboard_patterns,
    find_repeats,
    find_sequences,
    format_duration,
    strip_accents,
)


@pytest.mark.parametrize("pw", ["123456", "password", "qwerty", "jelszo", "P@ssw0rd", "szeretlek"])
def test_common_passwords_are_weak(pw):
    r = evaluate(pw)
    assert r.level == 0
    assert any(m.kind == "gyakori jelszó" for m in r.matches)


@pytest.mark.parametrize("pw", ["xK9#mQ2$vL7@pR4!", "Zr8&wq!3Lp#0vB6m", "kréta-zsiráf-malom-vihar-olló-eper42"])
def test_random_and_passphrases_are_strong(pw):
    assert evaluate(pw).level == 2


def test_short_password_is_always_weak():
    assert evaluate("Kd8!pz").level == 0


def test_empty_password():
    r = evaluate("")
    assert r.level == 0 and r.score == 0 and r.entropy_bits == 0


def test_patterns_reduce_entropy():
    r = evaluate("Macska2024!")
    assert r.entropy_bits < r.naive_entropy_bits / 2
    kinds = {m.kind for m in r.matches}
    assert "szótári szó" in kinds and "évszám" in kinds


def test_score_is_monotone_in_examples():
    order = ["123456", "Macska2024!", "Kutya_Repulo_77", "xK9#mQ2$vL7@pR4!"]
    scores = [evaluate(p).score for p in order]
    assert scores == sorted(scores)


def test_detectors():
    assert find_sequences("xxabcdxx")[0].token == "abcd"
    assert find_sequences("9876")[0].token == "9876"
    assert find_repeats("zzzzz")[0].token == "zzzzz"
    assert any(m.token == "abcabc" for m in find_repeats("abcabc"))
    assert find_keyboard_patterns("qwertz")[0].token == "qwertz"
    assert find_dates("anna1999")[0].token == "1999"
    assert any(m.kind == "dátum" for m in find_dates("x19990415"))


def test_helpers():
    assert deleet("p@ssw0rd") == "password"
    assert strip_accents("őrület") == "orulet"
    assert charset_pool("aA1!") == 26 + 26 + 10 + 33
    assert format_duration(0.1) == "azonnal"
    assert "perc" in format_duration(120)
    assert format_duration(1e20) == "több millió év"


def test_checklist_and_suggestions():
    r = evaluate("abc")
    assert any(not c.passed for c in r.checks)
    assert r.warnings and r.suggestions


def test_personal_info_detected():
    r = evaluate("Kovacs1999!", personal=["Kovács", "1999"])
    assert any(m.kind == "személyes adat" for m in r.matches)
    assert any("Személyes adat" in w for w in r.warnings)


def test_personal_info_lowers_entropy():
    pw = "Barnabas#Qx7"
    without = evaluate(pw).entropy_bits
    with_info = evaluate(pw, personal=["Barnabás"]).entropy_bits
    assert with_info < without


def test_personal_birth_date_with_separators():
    r = evaluate("anna19990415", personal=["1999.04.15"])
    assert any(m.kind == "személyes adat" for m in r.matches)


def test_no_personal_info_given():
    r = evaluate("Kovacs1999!")
    assert not any(m.kind == "személyes adat" for m in r.matches)
    

def test_year_warning_present():
    r = evaluate("Macska2024!")
    assert any("Évszám" in w for w in r.warnings)

def test_wordlist_files_are_loaded():
    from jelszoero.wordlists import COMMON_PASSWORDS
    assert len(COMMON_PASSWORDS) > 1000
    assert "starcraft" in COMMON_PASSWORDS
    assert not any(w.startswith("#") for w in COMMON_PASSWORDS)


def test_load_wordlist_missing_file():
    from jelszoero.wordlists import load_wordlist
    assert load_wordlist("nincs_ilyen_fajl.txt") == []


def test_own_dictionary_word_detected():
    r = evaluate("Balaton2024!")
    assert any(m.kind == "szótári szó" and m.token == "Balaton" for m in r.matches)