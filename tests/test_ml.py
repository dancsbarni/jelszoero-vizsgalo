"""Adatbetöltés, jellemzők, generátor és ML-folyamat tesztjei."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from jelszoero.data import generate_fallback_dataset, load_kaggle_csv  # noqa: E402
from jelszoero.features import FEATURE_NAMES, extract_features  # noqa: E402
from jelszoero.generator import generate_passphrase, generate_password  # noqa: E402
from jelszoero.ml_model import load_model, predict, train_and_compare  # noqa: E402
from jelszoero.rules import evaluate  # noqa: E402


def test_kaggle_csv_parser_is_robust(tmp_path):
    csv = tmp_path / "data.csv"
    csv.write_text(
        "password,strength\n"
        "kzde5577,1\n"
        "abc,def,0\n"            # vessző a jelszóban
        "rossz sor vessző nélkül\n"
        "valami,7\n"             # érvénytelen címke
        "\n"
        "Xk9#mQ2$vL7@pR4!,2\n"
        "kzde5577,1\n",          # duplikátum
        encoding="utf-8",
    )
    df = load_kaggle_csv(csv)
    assert list(df.columns) == ["password", "strength"]
    assert set(df["password"]) == {"kzde5577", "abc,def", "Xk9#mQ2$vL7@pR4!"}
    assert df.attrs["skipped_rows"] == 2


def test_features_length_matches_names():
    assert len(extract_features("Abc123!")) == len(FEATURE_NAMES)
    assert len(extract_features("")) == len(FEATURE_NAMES)


def test_generator_outputs_are_strong():
    for _ in range(20):
        pw = generate_password(16)
        assert len(pw) == 16
        assert any(c.isupper() for c in pw) and any(c.islower() for c in pw) and any(c.isdigit() for c in pw)
        assert evaluate(pw).level == 2
    assert evaluate(generate_passphrase(6)).level == 2


def test_training_pipeline_end_to_end(tmp_path):
    df = generate_fallback_dataset(n=1500, seed=1)
    summary = train_and_compare(df, models_dir=tmp_path / "m", reports_dir=tmp_path / "r")
    assert summary["best_model"]
    assert all(0 <= m["f1"] <= 1 for m in summary["models"])
    assert (tmp_path / "r" / "metrics.json").exists()
    assert (tmp_path / "r" / "model_comparison.png").exists()
    bundle = load_model(tmp_path / "m" / "best_model.joblib")
    label, proba = predict(bundle, "123456")
    assert label in (0, 1, 2) and abs(sum(proba) - 1) < 1e-6
    assert predict(bundle, "123456")[0] == 0

def test_cross_validation(tmp_path):
    df = generate_fallback_dataset(n=900, seed=2)
    summary = train_and_compare(df, models_dir=tmp_path / "m", reports_dir=tmp_path / "r",
                                cv_folds=3)
    for m in summary["models"]:
        assert 0 <= m["cv_f1_mean"] <= 1
        assert m["cv_f1_std"] >= 0
    assert summary["rule_based"]["cv_f1_mean"] is None