"""Beépített szólisták.

A ``COMMON_PASSWORDS`` lista a nyilvános kiszivárgás-statisztikákban
rendszeresen a legelsők között szereplő jelszavakat, illetve gyakori
magyar jelszavakat tartalmaz. A sorrend számít: minél előrébb van egy
jelszó, annál hamarabb próbálja ki egy támadó.

A ``DICTIONARY_WORDS`` gyakori angol és magyar szavakat tartalmaz, amelyek
jelszavak részeként (pl. ``Macska2024!``) is könnyen kitalálhatóvá teszik
azt. A ``PASSPHRASE_WORDS`` a jelmondat-generátor szókészlete.
"""

COMMON_PASSWORDS = [
    "123456", "password", "123456789", "12345678", "12345", "qwerty",
    "1234567", "111111", "1234567890", "123123", "abc123", "1234",
    "password1", "iloveyou", "1q2w3e4r", "000000", "qwerty123", "zaq12wsx",
    "dragon", "sunshine", "princess", "letmein", "654321", "monkey",
    "27653", "1qaz2wsx", "123321", "qwertyuiop", "superman", "asdfghjkl",
    "football", "baseball", "welcome", "admin", "login", "master",
    "hello", "freedom", "whatever", "qazwsx", "trustno1", "starwars",
    "passw0rd", "shadow", "michael", "jennifer", "charlie", "donald",
    "batman", "access", "666666", "121212", "7777777", "888888",
    "987654321", "555555", "999999", "112233", "123qwe", "qwe123",
    "pass", "test", "test123", "admin123", "root", "toor", "changeme",
    "secret", "love", "lovely", "flower", "hunter", "hunter2", "killer",
    "soccer", "hockey", "ranger", "buster", "thomas", "robert", "jordan",
    "harley", "pepper", "ginger", "daniel", "andrew", "computer",
    "internet", "samsung", "apple", "google", "chocolate", "summer",
    "winter", "spring", "autumn", "cookie", "maggie", "purple", "orange",
    "banana", "matrix", "mustang", "corvette", "ferrari", "porsche",
    "pokemon", "minecraft", "naruto", "liverpool", "chelsea", "arsenal",
    "barcelona", "realmadrid", "q1w2e3r4", "1q2w3e", "a1b2c3", "aaaaaa",
    "abcdef", "abcdefg", "abcd1234", "asdf", "asdf1234", "zxcvbnm",
    "qwertz", "qwertzuiop", "asdfgh", "yxcvbnm", "11111111", "12341234",
    "00000000", "p@ssw0rd", "p@ssword", "welcome1", "letmein1",
    # gyakori magyar jelszavak
    "jelszo", "jelszo123", "jelszó", "szeretlek", "szerelem", "macska",
    "kutya", "cica", "maci", "mackó", "nyuszi", "budapest", "magyar",
    "magyarorszag", "ferencvaros", "fradi", "ujpest", "debrecen", "szeged",
    "pecs", "gyor", "anyu", "apu", "mama", "papa", "csillag", "napsugar",
    "virag", "rozsa", "barack", "alma", "tavasz", "nyar", "osz", "tel",
    "kincsem", "edesem", "angyal", "titok", "titkos", "belepes", "admin1",
    "szia", "hello123", "laszlo", "istvan", "zoltan", "gabor", "peter",
    "andras", "attila", "tamas", "krisztina", "katalin", "erzsebet",
    "anna", "zsofia", "eszter", "csabi", "bence", "mate", "levente",
]

DICTIONARY_WORDS = [
    # angol
    "password", "admin", "welcome", "hello", "love", "dragon", "monkey",
    "master", "shadow", "sunshine", "princess", "football", "baseball",
    "soccer", "hockey", "summer", "winter", "spring", "autumn", "secret",
    "freedom", "computer", "internet", "orange", "purple", "banana",
    "cookie", "pepper", "ginger", "flower", "angel", "tiger", "lion",
    "eagle", "wolf", "bear", "horse", "dog", "cat", "fish", "bird",
    "house", "money", "music", "happy", "lucky", "magic", "star",
    "moon", "sun", "sky", "blue", "red", "green", "black", "white",
    "king", "queen", "prince", "game", "player", "super", "power",
    "user", "login", "test", "guest", "root", "apple", "google",
    "letmein", "qwerty", "iloveyou", "batman", "superman", "pokemon",
    # magyar
    "jelszo", "szeretlek", "szerelem", "macska", "kutya", "cica", "maci",
    "nyuszi", "budapest", "magyar", "csillag", "napsugar", "virag",
    "rozsa", "barack", "alma", "korte", "szilva", "tavasz", "nyar",
    "angyal", "titok", "titkos", "belepes", "haz", "auto", "kocsi",
    "foci", "fradi", "zene", "konyv", "iskola", "egyetem", "munka",
    "csalad", "anya", "apa", "testver", "barat", "baratno", "kedves",
    "edes", "kincs", "arany", "ezust", "piros", "kek", "zold", "fekete",
    "feher", "sarga", "nap", "hold", "ég", "tenger", "erdo", "folyo",
    "hegy", "viz", "tuz", "fold", "levego", "oroszlan", "tigris",
    "farkas", "medve", "lo", "sas", "galamb", "hal", "madar", "pillango",
    "csoki", "kave", "tea", "pizza", "sajt", "kenyer", "szamitogep",
    "laptop", "telefon", "jatek", "szoftver", "mernok", "hallgato",
]

PASSPHRASE_WORDS = [
    "alma", "ablak", "asztal", "bagoly", "barack", "bicikli", "bokor",
    "borsó", "csiga", "csillag", "dinnye", "dió", "domb", "eper", "erdő",
    "esernyő", "falevél", "felhő", "fenyő", "fóka", "füzet", "gomba",
    "gyertya", "habos", "hajó", "harang", "hattyú", "híd", "hold",
    "homok", "hópehely", "iránytű", "jácint", "jégcsap", "kabát",
    "kakas", "kalap", "kanál", "kapu", "kávé", "kemence", "kert",
    "kéreg", "kilincs", "kockás", "korcsolya", "kosár", "kötél",
    "kréta", "kulcs", "lámpa", "lepke", "levél", "liliom", "lomb",
    "malom", "manó", "mező", "mókus", "nyereg", "olló", "orgona",
    "ösvény", "paplan", "papír", "patak", "pillangó", "pipacs",
    "pohár", "rakéta", "répa", "rét", "rigó", "róka", "sajt", "sárkány",
    "sátor", "szamóca", "szánkó", "szekér", "szél", "szikla", "szivárvány",
    "tál", "tavasz", "tégla", "teknős", "tenger", "tócsa", "torony",
    "trombita", "tulipán", "tücsök", "uborka", "üveg", "vár", "vasaló",
    "vihar", "vitorla", "vödör", "zebra", "zokni", "zongora", "zsiráf",
]

# Billentyűzetsorok (angol QWERTY és magyar QWERTZ kiosztás)
KEYBOARD_ROWS = [
    "1234567890",
    "qwertyuiop",
    "qwertzuiop",
    "asdfghjkl",
    "zxcvbnm",
    "yxcvbnm",
    "1qaz2wsx3edc4rfv5tgb6yhn",
    "1q2w3e4r5t6y7u8i9o0p",
]
