# Mesterséges intelligencia használata

A projekt fejlesztése során generatív mesterségesintelligencia-eszközt is alkalmaztunk, elsősorban szakmai támogatásként, ötleteléshez, egyes fejlesztési feladatok megoldásához és az elemzési folyamatok ellenőrzéséhez. Az eszköz használata mellett a projekt felépítésével, az alkalmazott módszerekkel, a technológiai döntésekkel és az eredmények értelmezésével kapcsolatos döntéseket közösen hoztuk meg.

## Eszköz

| Eszköz | **Claude** (Anthropic), a claude.ai felületén |
| Időszak | 2026. november |
| Felhasználási terület | Tervezési támogatás, kódfejlesztés, hibakeresés, tesztelés, adatelemzés és dokumentáció |

A fejlesztés során az MI-t elsősorban olyan feladatok támogatására használtuk, amelyeknél hasznos volt egy alternatív megközelítés vagy egy gyorsabb kiindulási megoldás. A kapott eredményeket a projekt követelményeihez igazítottuk, saját környezetben teszteltük, és szükség esetén módosítottuk.

## Fontosabb felhasználási területek

### 1. Tervezés és a projekt felépítése

A fejlesztés kezdetén a lehetséges projektötletek összehasonlításához és a választott téma megtervezéséhez vettük igénybe az MI segítségét.

A végleges megoldás kialakításakor az alábbi szempontok mellett döntöttünk:

| Terület | Választott megoldás |
| Felhasználói felület | Python és Tkinter alapú asztali alkalmazás |
| Értékelési módszer | Szabályalapú értékelés és gépi tanulás összehasonlítása |
| Tanítóadat | Kaggle *Password Strength Classifier* adathalmaz |
| Modellválasztás | Több különböző osztályozó összehasonlítása |
| Dokumentáció | Magyar nyelvű dokumentáció és fejlesztői leírás |

A tervezés során fontos szempont volt, hogy ne csupán egy jelszóellenőrző alkalmazás készüljön, hanem a két különböző értékelési módszer eredményeit is össze tudjuk hasonlítani.

### 2. Fejlesztés és hibakeresés

A fejlesztés során az MI segítségét vettük igénybe egyes Python-modulok kialakításához, a gépi tanulási modellek megvalósításához, valamint a grafikus felület fejlesztéséhez.

A projektben többek között az alábbi területeken használtuk fel:

- A szabályalapú jelszóértékelés és a mintafelismerés kialakítása.
- A gépi tanuláshoz szükséges jellemzők meghatározása és kinyerése.
- A Random Forest, döntési fa és logisztikus regressziós modellek megvalósítása.
- A Tkinter-alapú felhasználói felület kialakítása.
- A jelszó- és jelmondatgenerátor elkészítése.
- Az automatikus tesztek és a kiértékelő ábrák fejlesztése.

A kapott kódot nem tekintettük automatikusan végleges megoldásnak. A működést saját környezetben ellenőriztük, a hibákat javítottuk, és a projekt további fejlesztése során több funkciót is kiegészítettünk.

### 3. Eredmények ellenőrzése és elemzése

A projekt egyik legfontosabb eredménye a gépi tanulási modellek kiértékelése során született.

A tesztelés során feltűnt, hogy több modell is közel 100%-os pontosságot ért el. Ez felvetette annak lehetőségét, hogy az adathalmaz címkézése túl egyszerű összefüggést tartalmaz.

Ennek ellenőrzésére egy olyan alapmodellt is bevontunk az összehasonlításba, amely kizárólag a jelszó hosszát veszi figyelembe. Az eredmények alapján kiderült, hogy az adathalmazban a kategóriák meghatározása valójában teljes egészében a jelszó hosszától függ.

Ez fontos következtetés volt, mivel megmutatta, hogy a magas pontosság önmagában nem feltétlenül jelenti azt, hogy egy modell valóban a vizsgált probléma lényegét tanulta meg.

Az eredmények értelmezését, a szabályalapú és gépi tanulási módszer közötti különbségek vizsgálatát, valamint a következtetések dokumentálását külön feladatként kezeltük.

### 4. Saját fejlesztések és módosítások

A projekt továbbfejlesztése során több olyan módosítást is elvégeztünk, amelyek a kezdeti funkcionalitást bővítették.

Ezek közül kiemelendők:

- **Személyes adatok felismerése:** a névhez és születési dátumhoz kapcsolódó minták felismerésének beépítése a szabályalapú értékelőbe.
- **Szólisták bővítése:** a gyakori jelszavakat tartalmazó lista kiegészítése, valamint saját magyar nyelvű szólista összeállítása.
- **Keresztvalidáció:** az öt részre osztott keresztvalidáció beépítése a modellek stabilitásának vizsgálatához.
- **Hibajavítás és tesztelés:** a fejlesztés során felmerült hibák javítása és az érintett funkciók tesztekkel történő ellenőrzése.

A személyes adatok felismerésénél külön figyelmet fordítottunk arra, hogy a rendszer az ékezetek és bizonyos karakterhelyettesítések ellenére is képes legyen az egyezések felismerésére. Az átfedő minták kezelését is ellenőriztük, és a fejlesztés során egy hiányzó évszám-figyelmeztetést is javítottunk.

A saját módosítások és fejlesztési lépések a GitHub repository commit-történetében is nyomon követhetők.

## Mit ellenőriztünk a fejlesztés során?

A projekt megbízható működésének biztosítása érdekében az alábbi ellenőrzéseket végeztük el:

- A program telepítése és futtatása saját számítógépen.
- Az automatikus tesztek futtatása a `python -m pytest` paranccsal.
- A szabályalapú értékelés entrópiabecslésének és mintakiválasztási algoritmusának áttekintése.
- Különböző jelszavak vizsgálata a felismerési és értékelési eredmények ellenőrzéséhez.
- A Kaggle-adathalmaz címkézési logikájának vizsgálata.
- A gépi tanulási modellek eredményeinek összehasonlítása.
- A grafikus felület és a generátor működésének ellenőrzése.
