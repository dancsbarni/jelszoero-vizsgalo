# GitHub-útmutató

A követelmény szerint a repository-nak a projekt **fokozatos fejlődését** kell
mutatnia, és nem elfogadható, ha minden csak a beadás előtt kerül fel.

**Ne készíts visszadátumozott commitokat** (pl. `GIT_COMMITTER_DATE`-tel). Ez az
oktató megtévesztése lenne, és a GitHub a push valódi idejét amúgy is rögzíti.
Az alábbi út tisztességes, és jól mutatja a saját munkádat.

## 1. Repository létrehozása (egyszer)

1. A GitHubon: **New repository** → név pl. `jelszoero-vizsgalo` → *Private* vagy
   *Public* (ahogy az oktató kéri) → README **nélkül** (a projektben már van).
2. A projekt mappájában (ahol a `main.py` van):

```bash
git init
git branch -M main
git config user.name "Teljes Neved"
git config user.email "a-github-email-cimed@example.com"
```

## 2. Első commitok: témánként, őszinte üzenetekkel

Ne egyetlen commitba tedd fel az egészet. Bontsd logikai részekre, és az
üzenetekben jelezd, hogy az alap MI-vel készült (ez összhangban van az
`AI_USAGE.md`-vel):

```bash
git add .gitignore requirements.txt README.md AI_USAGE.md
git commit -m "Projektváz: README, függőségek, MI-használat dokumentációja"

git add src/jelszoero/__init__.py src/jelszoero/wordlists.py src/jelszoero/rules.py tests/test_rules.py
git commit -m "Szabályalapú értékelő és tesztjei (MI-vel generált alap, átnézve)"

git add src/jelszoero/features.py src/jelszoero/data.py src/jelszoero/ml_model.py src/jelszoero/plots.py train.py data/README.md tests/test_ml.py
git commit -m "Gépi tanulás: adatbetöltés, jellemzők, modellek, tanítószkript"

git add models/ reports/
git commit -m "Tanítási eredmények: legjobb modell, metrikák, ábrák"

git add src/jelszoero/generator.py src/jelszoero/gui.py src/jelszoero/assets main.py
git commit -m "Grafikus felület és jelszógenerátor"

git add docs/
git commit -m "Dokumentáció és képernyőképek"

git remote add origin https://github.com/FELHASZNALONEV/jelszoero-vizsgalo.git
git push -u origin main
```

Utána ellenőrizd: `git status` szerint nem maradt-e ki fájl, és hogy a
`data/*.csv` **nem** került fel.

## 3. Folyamatos munka: saját fejlesztések kis commitokban

Ez adja a „GitHub és folyamatos munka” pontszám nagyobb részét. Több napon át
dolgozz, és minden kisebb, működő lépés után commitolj:

```bash
git add <módosított fájlok>
git commit -m "Rövid, konkrét leírás arról, mit csináltál"
git push
```

Saját bővítési ötletek (a dokumentáció 10. fejezetéből):

- személyes adatok (név, születési dátum) keresése a jelszóban – új mintafelismerő a `rules.py`-ban, tesztekkel;
- nagyobb, fájlból betöltött magyar és angol szólista;
- keresztvalidáció (`cross_val_score`) és hiperparaméter-hangolás a modelleknél;
- Have I Been Pwned (k-anonimitás) ellenőrzés.

Jó commitüzenet: `Születési dátum felismerése a jelszóban + 3 teszt`.
Rossz: `update`, `fix`, `asdf`.

Ha MI-vel dolgozol tovább, a fontosabb promptokat írd be az `AI_USAGE.md`-be is.

## Kétfős projekt esetén

Mindkét hallgató a saját GitHub-fiókjával commitoljon (a `git config user.email`
egyezzen a fiókéval), és mindkettőtöktől legyen érdemi commit. A társat a repó
**Settings → Collaborators** menüpontjában lehet meghívni.
