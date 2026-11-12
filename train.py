"""Modellek tanítása és összehasonlítása parancssorból.

Használat:
    python train.py                         # data/data.csv, ha létezik; különben tartalék adat
    python train.py --data utvonal/data.csv --max-rows 200000
    python train.py --fallback              # mindenképp a generált tartalék adattal

Kimenet:
    models/best_model.joblib   – a legjobb (makro F1) modell
    reports/metrics.json       – minden mérőszám
    reports/*.png              – összehasonlító ábrák
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from jelszoero.data import generate_fallback_dataset, load_kaggle_csv  # noqa: E402
from jelszoero.ml_model import train_and_compare  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Jelszóerősség-modellek tanítása")
    parser.add_argument("--data", default=str(ROOT / "data" / "data.csv"),
                        help="a Kaggle data.csv elérési útja (alap: data/data.csv)")
    parser.add_argument("--max-rows", type=int, default=200_000,
                        help="legfeljebb ennyi sort használ (rétegzett minta); 0 = mind")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--cv", type=int, default=5,
                        help="keresztvalidáció foldjainak száma; 0 = kikapcsolva")
    parser.add_argument("--fallback", action="store_true",
                        help="a beépített generált adattal tanít")
    args = parser.parse_args()

    if not args.fallback and Path(args.data).exists():
        print(f"Adat betöltése: {args.data}")
        df = load_kaggle_csv(args.data, max_rows=args.max_rows or None, seed=args.seed)
        print(f"  beolvasva: {len(df)} egyedi jelszó, kihagyott hibás sor: {df.attrs.get('skipped_rows', 0)}")
    else:
        if not args.fallback:
            print(f"Nem található: {args.data}")
        print("A beépített, generált tartalék adattal tanítok.")
        df = generate_fallback_dataset(seed=args.seed)

    summary = train_and_compare(df, test_size=args.test_size, seed=args.seed, progress=print,
                                cv_folds=args.cv)

    print("\nÖsszefoglaló (teszthalmaz):")
    print(f"{'Modell':45} {'Pontosság':>10} {'Makro F1':>10} {'CV F1 (átlag ± szórás)':>24}")
    for m in summary["models"] + [summary["rule_based"]]:
        cv = (f"{m['cv_f1_mean']:.4f} ± {m['cv_f1_std']:.4f}"
              if m.get("cv_f1_mean") is not None else "–")
        print(f"{m['name']:45} {m['accuracy']:10.4f} {m['f1']:10.4f} {cv:>24}")
    print(f"\nLegjobb modell: {summary['best_model']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
