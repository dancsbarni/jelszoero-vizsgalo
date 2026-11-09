"""A jelszóerősség-vizsgáló belépési pontja.

    python main.py                 # grafikus felület (Tkinter)
    python main.py --cli JELSZÓ    # gyors értékelés parancssorban
    python main.py --cli           # jelszó bekérése rejtett beírással
"""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))


def cli(password: str | None) -> int:
    from jelszoero import LEVEL_NAMES
    from jelszoero.ml_model import load_model, predict
    from jelszoero.rules import evaluate

    if password is None:
        password = getpass.getpass("Jelszó (nem jelenik meg): ")
    r = evaluate(password)
    print(f"Szabályalapú szint : {r.level_name} ({r.score}/100)")
    print(f"Effektív entrópia  : {r.entropy_bits} bit (naiv: {r.naive_entropy_bits} bit)")
    print(f"Feltörési idő      : online {r.crack_times_text['online']}, offline {r.crack_times_text['offline']}")
    model = load_model()
    if model:
        label, proba = predict(model, password)
        probs = ", ".join(f"{LEVEL_NAMES[i]} {p:.0%}" for i, p in enumerate(proba))
        print(f"ML-modell          : {LEVEL_NAMES[label]}  [{probs}]  ({model['name']})")
    else:
        print("ML-modell          : nincs betanítva (futtasd: python train.py)")
    for w in r.warnings:
        print("  ! " + w)
    for s in r.suggestions:
        print("  - " + s)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Jelszóerősség-vizsgáló")
    parser.add_argument("--cli", nargs="?", const="", default=None, metavar="JELSZÓ",
                        help="parancssori mód (jelszó nélkül rejtett bekérés)")
    args = parser.parse_args()
    try:
        if args.cli is not None:
            return cli(args.cli or None)
        from jelszoero.gui import run
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.startswith(("tkinter", "_tkinter")):
            print("A Tkinter nem érhető el ebben a Python-telepítésben.\n"
                  "  Windows / macOS: telepítsd újra a Pythont a python.org-ról, és hagyd bekapcsolva\n"
                  "                   a „tcl/tk and IDLE” opciót.\n"
                  "  Linux:           sudo apt install python3-tk\n"
                  "Parancssori mód: python main.py --cli")
        else:
            print(f"Hiányzó Python-csomag: {exc.name}\n"
                  "Telepítsd a függőségeket ebben a mappában:\n"
                  "    python -m pip install -r requirements.txt")
        return 1
    run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
