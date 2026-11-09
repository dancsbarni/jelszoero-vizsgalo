# Adatkönyvtár

A modell tanításához a Kaggle **Password Strength Classifier Dataset** kell
(oszlopok: `password,strength`, ahol 0 = gyenge, 1 = közepes, 2 = erős;
kb. 670 000 jelszó).

## Honnan töltsd le

- **Eredeti forrás (Kaggle, regisztráció kell):**
  <https://www.kaggle.com/datasets/bhavikbb/password-strength-classifier-dataset>
  → `data.csv`
- **A mellékelt modell ebből a nyilvános GitHub-másolatból készült:**
  <https://github.com/Aslm-Fawzy/Password-Strength-Detection> → `password_data.csv`
  (ugyanaz a formátum és tartalom)

Másold a letöltött fájlt ide `data.csv` néven:

    data/data.csv

## Tanítás (a mellékelt eredmények reprodukálása)

    python train.py

Ez 200 000 soros rétegzett mintát használ, `seed=42`-vel, így a `reports/`
mappában lévő eredményekkel egyezőt kell kapnod. Más fájlnévvel:

    python train.py --data data/password_data.csv

Az adathalmaz kiszivárgott valódi jelszavakat tartalmaz, ezért nem része a
repository-nak (a `.gitignore` kizárja). Ha nincs CSV, a
`python train.py --fallback` a beépített, generált adattal tanít.
