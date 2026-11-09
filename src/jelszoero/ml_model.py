"""Gépi tanuló modellek tanítása, összehasonlítása, mentése és használata.

Minden modell egy scikit-learn ``Pipeline``, amely **nyers jelszavakat**
kap bemenetként – így a felületnek nem kell tudnia, melyik modell milyen
jellemzőket használ.

Összehasonlított modellek:

* Döntési fa (kézi jellemzők) – egyszerű, jól értelmezhető kiindulópont
* Logisztikus regresszió (kézi jellemzők)
* Random Forest (kézi jellemzők)
* Logisztikus regresszió (karakter 1–3-gram TF-IDF)
* Alapmodell: döntési fa, amely kizárólag a jelszó hosszát látja – ezzel
  ellenőrizzük, mennyit "ér" a többi jellemző az adott címkézéshez képest

Ezek mellett a **szabályalapú értékelő** is lefut ugyanazon a teszthalmazon,
így a két megközelítés azonos mérőszámokkal összevethető.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler
from sklearn.tree import DecisionTreeClassifier

from . import LEVEL_NAMES
from .features import FEATURE_NAMES, feature_matrix
from .rules import evaluate

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"
DEFAULT_MODEL_PATH = MODELS_DIR / "best_model.joblib"
RULE_BASED_NAME = "Szabályalapú (entrópia + minták)"
BASELINE_NAME = "Alapmodell: döntési fa (csak hossz)"

ProgressCallback = Callable[[str], None]


def _features(passwords):
    """Modul szintű függvény, hogy a pipeline joblibbel menthető legyen."""
    return feature_matrix(passwords)


def _length_only(passwords):
    """Egyetlen jellemző: a jelszó hossza (alapmodellhez)."""
    return np.array([[len(str(p))] for p in passwords], dtype=float)


def build_models(seed: int = 42) -> dict[str, Pipeline]:
    """A modellek sorrendje egyben a holtversenyek feloldási sorrendje is."""
    feat = lambda: FunctionTransformer(_features)  # noqa: E731
    return {
        "Random Forest (jellemzők)": Pipeline([
            ("jellemzok", feat()),
            ("modell", RandomForestClassifier(
                n_estimators=150, min_samples_leaf=2, n_jobs=-1, random_state=seed)),
        ]),
        "Döntési fa (jellemzők)": Pipeline([
            ("jellemzok", feat()),
            ("modell", DecisionTreeClassifier(max_depth=8, random_state=seed)),
        ]),
        "Logisztikus regresszió (jellemzők)": Pipeline([
            ("jellemzok", feat()),
            ("skalazas", StandardScaler()),
            ("modell", LogisticRegression(max_iter=2000)),
        ]),
        "Logisztikus regresszió (TF-IDF n-gram)": Pipeline([
            ("tfidf", TfidfVectorizer(analyzer="char", ngram_range=(1, 3),
                                      lowercase=False, min_df=2, max_features=60000,
                                      sublinear_tf=True)),
            ("modell", LogisticRegression(max_iter=2000)),
        ]),
        BASELINE_NAME: Pipeline([
            ("hossz", FunctionTransformer(_length_only)),
            ("modell", DecisionTreeClassifier(max_depth=3, random_state=seed)),
        ]),
    }


@dataclass
class ModelResult:
    name: str
    accuracy: float
    precision: float
    recall: float
    f1: float
    train_seconds: float
    predict_ms_per_1000: float
    confusion: list[list[int]]
    report: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return self.__dict__.copy()


def _score(name: str, y_true, y_pred, train_s: float, pred_s: float, n: int) -> ModelResult:
    return ModelResult(
        name=name,
        accuracy=float(accuracy_score(y_true, y_pred)),
        precision=float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        recall=float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
        f1=float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        train_seconds=round(train_s, 2),
        predict_ms_per_1000=round(pred_s / max(n, 1) * 1000 * 1000, 2),
        confusion=confusion_matrix(y_true, y_pred, labels=[0, 1, 2]).tolist(),
        report=classification_report(
            y_true, y_pred, labels=[0, 1, 2],
            target_names=[LEVEL_NAMES[i] for i in range(3)],
            output_dict=True, zero_division=0),
    )


def train_and_compare(df, test_size: float = 0.2, seed: int = 42,
                      progress: ProgressCallback | None = None,
                      models_dir: Path = MODELS_DIR,
                      reports_dir: Path = REPORTS_DIR) -> dict:
    """Az összes modell tanítása és kiértékelése, a legjobb mentése.

    Visszatérés: összefoglaló szótár (ezt menti ``reports/metrics.json``-ba is).
    """
    log = progress or (lambda msg: None)
    models_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    X = df["password"].astype(str).to_numpy()
    y = df["strength"].astype(int).to_numpy()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=seed, stratify=y)
    log(f"Adat: {len(X)} jelszó (tanító: {len(X_train)}, teszt: {len(X_test)})")

    results: list[ModelResult] = []
    fitted: dict[str, Pipeline] = {}
    for name, pipe in build_models(seed).items():
        log(f"Tanítás: {name} …")
        t0 = time.perf_counter()
        pipe.fit(X_train, y_train)
        train_s = time.perf_counter() - t0
        t0 = time.perf_counter()
        y_pred = pipe.predict(X_test)
        pred_s = time.perf_counter() - t0
        res = _score(name, y_test, y_pred, train_s, pred_s, len(X_test))
        results.append(res)
        fitted[name] = pipe
        log(f"  pontosság={res.accuracy:.4f}  F1={res.f1:.4f}  ({train_s:.1f} s)")

    log("Kiértékelés: szabályalapú módszer …")
    t0 = time.perf_counter()
    y_rule = np.array([evaluate(p).level for p in X_test])
    rule_s = time.perf_counter() - t0
    rule_res = _score(RULE_BASED_NAME, y_test, y_rule, 0.0, rule_s, len(X_test))
    log(f"  pontosság={rule_res.accuracy:.4f}  F1={rule_res.f1:.4f}")

    # a "csak hossz" alapmodell viszonyítási pont, nem választjuk ki
    candidates = [r for r in results if r.name != BASELINE_NAME]
    best = max(candidates, key=lambda r: round(r.f1, 4))
    log(f"Legjobb modell: {best.name} (F1={best.f1:.4f})")

    bundle = {
        "name": best.name,
        "pipeline": fitted[best.name],
        "metrics": best.as_dict(),
        "trained_at": datetime.now().isoformat(timespec="seconds"),
        "data_source": df.attrs.get("source", "ismeretlen"),
        "n_samples": int(len(X)),
        "labels": LEVEL_NAMES,
    }
    model_path = models_dir / "best_model.joblib"
    joblib.dump(bundle, model_path, compress=3)
    log(f"Modell mentve: {model_path}")

    rf = fitted.get("Random Forest (jellemzők)")
    importances = None
    if rf is not None:
        imp = rf.named_steps["modell"].feature_importances_
        importances = sorted(zip(FEATURE_NAMES, map(float, imp)), key=lambda t: -t[1])

    summary = {
        "trained_at": bundle["trained_at"],
        "data_source": bundle["data_source"],
        "n_samples": int(len(X)),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "class_distribution": {LEVEL_NAMES[int(k)]: int(v)
                               for k, v in zip(*np.unique(y, return_counts=True))},
        "best_model": best.name,
        "models": [r.as_dict() for r in results],
        "rule_based": rule_res.as_dict(),
        "feature_importances": importances,
    }
    with (reports_dir / "metrics.json").open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)

    try:
        from .plots import save_all_plots
        save_all_plots(summary, reports_dir)
        log(f"Ábrák mentve: {reports_dir}")
    except Exception as exc:  # az ábra hiánya ne akassza meg a tanítást
        log(f"Figyelmeztetés: az ábrák mentése nem sikerült ({exc})")

    return summary


# ---------------------------------------------------------------------------
# Betöltés és előrejelzés
# ---------------------------------------------------------------------------

def load_model(path: str | Path = DEFAULT_MODEL_PATH) -> dict | None:
    path = Path(path)
    if not path.exists():
        return None
    try:
        return joblib.load(path)
    except Exception as exc:  # pl. eltérő scikit-learn verzióval mentett modell
        print(f"A modell nem tölthető be ({exc}). Tanítsd újra: python train.py")
        return None


def predict(bundle: dict, password: str) -> tuple[int, list[float]]:
    """Visszaadja: (osztály, [P(gyenge), P(közepes), P(erős)])."""
    pipe = bundle["pipeline"]
    proba = pipe.predict_proba([password])[0]
    classes = list(pipe.classes_)
    full = [float(proba[classes.index(c)]) if c in classes else 0.0 for c in (0, 1, 2)]
    return int(np.argmax(full)), full


def load_metrics(reports_dir: Path = REPORTS_DIR) -> dict | None:
    path = reports_dir / "metrics.json"
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)
