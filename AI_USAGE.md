# Mesterséges intelligencia használata

A projekt elkészítéséhez generatív MI-eszközt használtam. Ez a fájl leírja,
melyik eszközt, mire, milyen promptokkal, mit kaptam, és mit ellenőriztem vagy
módosítottam rajta.

## Eszköz

| | |
|---|---|
| Eszköz | **Claude** (Anthropic), a claude.ai felületén, fájl- és kódfuttatási hozzáféréssel |
| Időszak | 2026. november |
| Szerep | Ötletrangsorolás, a teljes kód első változatának megírása, tanítás futtatása, dokumentáció és ábrák elkészítése, követelmény-ellenőrzés |

**Őszintén:** a projekt első, működő változatát (kód, tesztek, ábrák, README,
Word-dokumentáció) lényegében teljes egészében az MI írta. A saját munkám a
témaválasztás, a döntések (lásd lent), az eredmények ellenőrzése és értelmezése,
valamint a későbbi saját módosítások, amelyek a GitHub commitjaiban követhetők.

## Fontosabb promptok és eredmények


### 1. A projekt elkészítése

> „A 19. jelszó erősség vizsgáló témából szeretném, ha elkészítenéd a projektet. Ha van kérdésed, a kezdés
> előtt tedd fel, aztán kezdj neki. Egy zip fájlt kérek, benne a projekttel.

Az MI kezdés előtt négy kérdést tett fel; a válaszaim (ezek az én döntéseim):

| Kérdés | Választásom |
|---|---|
| Felület | Tkinter asztali GUI |
| Értékelési módszer | Szabályalapú + gépi tanulás együtt |
| Tanítóadat | Kaggle *Password Strength Classifier* adathalmaz |
| Dokumentáció | Magyar README + Word-dokumentáció |

**Eredmény:** a teljes projekt: szabályalapú értékelő (`rules.py`), jellemzőkinyerés,
négy ML-modell és összehasonlításuk, Tkinter felület, generátor, 20 pytest-teszt,
ábrák, README és 15 oldalas Word-dokumentáció.

Az MI munka közben maga is ellenőrzött és javított:

- Futtatta a teszteket és a tanítást, a felületről képernyőképeket készített, és
  ezek alapján javította az elrendezést.
- Észrevette, hogy három modell 100%-os pontosságú, ezért utánanézett: kiderült,
  hogy az adathalmazban a címke **csak a jelszó hosszától** függ. Ezt egy csak a
  hosszt látó alapmodellel igazolta, és a dokumentációban külön elemezte.
- A Kaggle-adatot egy nyilvános GitHub-másolatból töltötte le (lásd
  [`data/README.md`](data/README.md)).


### 2. Követelmény-ellenőrzés és javítás

> „Ez alapján ellenőrizd, hogy mindennek megfelel-e a projekt. Ha valami nincs,
> azokat listázd ki.” (bemásolva: a tárgy projektkövetelményei)
>
> „Javítsd ki az 1., 2., 5. pontok szerint a projektet.”

**Eredmény:** a hiányok listája (MI-dokumentáció, GitHub-történet, saját munka,
prezentáció, apróságok). A javítás során elkészült ez a fájl, a `.gitignore`, a
GitHub-útmutató ([`docs/GITHUB_UTMUTATO.md`](docs/GITHUB_UTMUTATO.md)), az adatforrás
pontos megadása és egy MI-fejezet a dokumentációban. Az MI kifejezetten nem
készített visszadátumozott commitokat; a commit-történetet nekem kell valós
munkával felépítenem.

## Mit ellenőriztem és módosítottam én


- Saját gépen telepítettem és futtattam a programot és a teszteket (`python -m pytest`).
- Átnéztem és megértettem a `rules.py` entrópiaszámítását és a mohó mintakiválasztást.
- Saját jelszavakkal kipróbáltam, hogy a szabályalapú értékelés ésszerű-e.
- Ellenőriztem az adathalmazon, hogy a címke valóban csak a hossztól függ.
- Saját bővítés(ek): személyes adatok keresése, nagyobb szólista (a magyar szótárat én állítottam össze)

## Tanulságok

- Az MI gyorsan ad működő, jól strukturált kódot, de a kimenetet ellenőrizni kell:
  a 100%-os pontosság itt nem jó modellt, hanem hibás címkézést jelzett.
- A projekt minden lényeges részét meg kell értenem, mert a védésen magyaráznom és
  módosítanom kell tudni.

## Személyes adat felismerés

A funkció kódját Claude-tól kértem lépésenként, majd én építettem be a projektbe
három külön commitban, és a tesztekkel ellenőriztem a működését. Az átnézés
során kiderült, hogy a beillesztéskor kimaradt az évszám-figyelmeztetés; a hibát
én javítottam, és új tesztet írtam rá, hogy a jövőben ne fordulhasson elő.
Átnéztem a működését is: a név és a dátum a normalize() miatt ékezettől és
leetspeaktől függetlenül is felismerhető, a select_matches() pedig átfedésnél
a személyes adatot választja, mert az kevesebb bitet ér.