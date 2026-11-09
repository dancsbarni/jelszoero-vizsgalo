"""Jelszóerősség-vizsgáló csomag.

Modulok:
    wordlists     – gyakori jelszavak és szótárszavak listái
    rules         – szabályalapú (entrópia + mintafelismerés) értékelés
    features      – jellemzőkinyerés a gépi tanuláshoz
    ml_model      – modellek tanítása, mentése, betöltése, előrejelzés
    data          – adatbetöltés (Kaggle CSV) és tartalék adatgenerálás
    generator     – erős jelszó és jelmondat generálása
    gui           – Tkinter grafikus felület
"""

__version__ = "1.0.0"

LEVEL_NAMES = {0: "Gyenge", 1: "Közepes", 2: "Erős"}
LEVEL_COLORS = {0: "#C2541C", 1: "#AD7C06", 2: "#2D7A4B"}
