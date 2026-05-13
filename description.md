# Opis projektu „dla laika” — Szyfr Cadenus

Ten plik tłumaczy projekt **bez żargonu**. Czytaj po kolei.

---

## Co my w ogóle robimy?

Wyobraź sobie taki scenariusz:

1. Ktoś wziął tekst (np. fragment książki) i **zaszyfrował** go.
2. Dostajemy w ręce tylko **bełkot** (np. `TTHINGEANNAFAUITEESSPLTERCT...`).
3. Naszym zadaniem jest **zgadnąć tekst oryginalny** — bez znajomości klucza.

To wszystko. Cała reszta to szczegóły jak to ugryźć.

**Szyfr Cadenus** to konkretna metoda mieszania liter — opisana ponad 100
lat temu, używana w łamigłówkach kryptograficznych. Nie jest super
skomplikowany, ale wystarczająco, żeby „na oko” nie dało się tego odczytać.

---

## Co siedzi w każdym pliku?

Wyobraź sobie projekt jak warsztat. Każde narzędzie ma jedno zadanie:

| Plik                         | Co robi (po ludzku)                                                                                                                                                                                            |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`cadenus_cipher.py`**      | „Maszyna do szyfrowania i odszyfrowywania”. Jak kalkulator: dajesz tekst + klucz, dostajesz zaszyfrowany tekst. Albo odwrotnie.                                                                                |
| **`cadenus_attack_Olko.py`** | „Detektyw”. Dostaje sam zaszyfrowany tekst i próbuje **zgadnąć** klucz oraz odczytać oryginał.                                                                                                                 |
| **`make_sample.py`**         | „Generator zagadek”. Bierze fragment książki, losuje klucz i tworzy zaszyfrowany tekst do testowania detektywa.                                                                                                |
| **`build_ngrams.py`**        | „Słownik statystyczny”. Przegląda książki i liczy, jakie 4-literowe sekwencje (np. `THER`, `IONS`) występują często w angielskim/niemieckim. Potrzebne, żeby detektyw wiedział, jak wygląda „prawdziwy” tekst. |
| **`test_attack.py`**         | „Egzaminator”. Uruchamia detektywa wiele razy z różnymi kluczami i mierzy, jak często mu się udaje.                                                                                                            |
| `english_quadgrams.txt`      | Plik ze statystykami angielskiego (gotowy, nie trzeba budować od nowa).                                                                                                                                        |
| `german_quadgrams.txt`       | To samo dla niemieckiego.                                                                                                                                                                                      |
| `ciphertext_english.txt`     | Przykładowy zaszyfrowany tekst angielski — gotowa zagadka do złamania.                                                                                                                                         |
| `ciphertext_german.txt`      | To samo, niemiecki.                                                                                                                                                                                            |
| `solutions.txt`              | „Klucz odpowiedzi” — tu jest prawdziwy klucz i początek oryginalnego tekstu. **Detektyw tego nie czyta.** Ty czytasz, żeby sprawdzić, czy się udało.                                                           |
| `corpora/`                   | Książki do nauki statystyk (Pride and Prejudice, Moby Dick, Buddenbrooks).                                                                                                                                     |
| `start.sh`, `start.bat`      | Skróty uruchamiające detektywa (Linux/Mac vs Windows).                                                                                                                                                         |

---

## Jak działa szyfr Cadenus — na palcach

Wyobraź sobie kartkę papieru w kratkę:

1. Wybieramy **klucz** — słowo, np. `SECRET` (6 liter).
2. Bierzemy oryginalny tekst i wpisujemy go do tabelki **|alfabet| wierszy × 6 kolumn**
   (bo klucz ma 6 liter), pisząc wiersz po wierszu.
3. Każdą kolumnę **przesuwamy w górę** o tyle pól, jaką pozycję w alfabecie
   ma odpowiadająca jej litera klucza. Np. kolumna pod literą `S` przesuwa
   się o 18 pól (S = 19. litera, ale liczymy od 0, więc 18).
4. Potem kolumny **przestawiamy alfabetycznie** wg liter klucza — kolumna
   z literą bliską A idzie pierwsza.
5. Czytamy tabelkę wiersz po wierszu — to jest zaszyfrowany tekst.

Deszyfrowanie to dokładnie te same kroki, ale w odwrotną stronę.
Jeśli długość tekstu nie pasuje do rozmiaru bloku, szyfrowanie dopelnia go
losowymi literami alfabetu, a deszyfrowanie zgłasza błąd.

**Kluczowy fakt**: rozmiar alfabetu zalezy od jezyka.

- Angielski ma 25 liter, bo `W` traktujemy jako `V` (taka jest definicja Cadenusa).
- Niemiecki ma 30 liter: `A-Z` oraz `Ä Ö Ü ß` (bez redukcji do 25 liter).

---

## Jak detektyw zgaduje klucz?

To jest najciekawsza część. Nie ma jak przejrzeć wszystkich możliwych
kluczy (dla klucza długości 8 to ponad 40 miliardów kombinacji). Dlatego
robimy **„grę gorąco-zimno”**:

1. Detektyw **losuje** jakiś klucz (totalnie z czapy).
2. Próbuje nim odszyfrować tekst — wychodzi bełkot.
3. Sprawdza, **jak bardzo bełkot** jest bełkotem — używa do tego statystyk
   z książek. Liczy, ile w wyniku jest typowych angielskich sekwencji jak
   `THER`, `THAT`, `IONS`. Im więcej — tym lepiej.
4. **Zmienia klucz odrobinę** (np. zamienia dwie litery miejscami) i znów
   sprawdza.
5. Jeśli nowy klucz daje „mniej bełkotu” — zostawia go. Jeśli gorzej —
   wraca do poprzedniego.
6. Powtarza tysiące razy. Powoli klucz „pełznie” w stronę właściwego.
7. Jeśli utknie i nic nie pomaga — zaczyna od nowa z nowym losowym kluczem
   (to jest „shotgun” — strzelamy w wiele miejsc).

To się nazywa **hill-climbing** (wspinaczka po wzgórzu) — wyobraź sobie,
że wchodzisz na górę po ciemku: dotykasz nogą ziemi wokół, idziesz tam
gdzie wyżej, i tak aż dojdziesz na szczyt.

Dla wydajności fitness liczymy na indeksach liter (tablica quadgramów),
bez wycinania 4-literowych fragmentów stringa.

**Skąd wiemy że dobry klucz jest dobry?** Bo daje wynik typu
`PRIDEANDPREJUDICE` zamiast `XYZQVKWPLMQRT`.

---

## Jak to przetestować — krok po kroku

Wszystkie komendy uruchamiaj **z głównego folderu projektu**.

### Test 1: Szyfrowanie i deszyfrowanie działa poprawnie

To podstawowy sprawdzian: zaszyfruj coś i sprawdź, czy po odszyfrowaniu
wraca to samo.

```bash
python3 cadenus_cipher.py
```

**Co się stanie:** Program zaszyfruje krótki tekst losowym kluczem,
deszyfruje go i wypisze wynik. Jeśli na końcu zobaczysz `OK`, to znaczy
że maszyna szyfrująca działa.

**Czego oczekujesz:**

```
Klucz: YHPKCRQZ
Tekst jawny (200): ITVASTHEBESTOFTIMES...
Kryptotekst (200): TMTTVTTIOEEGVGOEMOE...
Po deszyfrowaniu (200): ITVASTHEBESTOFTIMES...
OK
```

(Klucz będzie inny przy każdym uruchomieniu, bo jest losowy.)

---

### Test 2: Atak na gotowy angielski przykład

Najszybszy sposób, żeby zobaczyć detektywa w akcji.

```bash
python3 cadenus_attack_Olko.py ciphertext_english.txt -l en -k 8 -r 6
```

Co znaczą flagi:

- `ciphertext_english.txt` — plik z zagadką do złamania
- `-l en` — język angielski (program używa angielskich statystyk)
- `-k 8` — z góry mówimy detektywowi że klucz ma 8 liter (przyspiesza go)
- `-r 6` — niech spróbuje 6 razy z różnymi losowymi startami

**Co się stanie:** Przez około **1 minutę** zobaczysz:

- linijki typu `restart 1/6 N=8 score=-3315.2 key=...` — to detektyw
  raportuje wyniki kolejnych prób (im wyższy score, tym lepiej, czyli
  `-3315` jest lepsze niż `-4500`)
- na końcu sekcję `WYNIK` z odszyfrowanym tekstem

**Czego oczekujesz:** ostatecznie zobaczysz fragment **Pride and Prejudice**:

```
Tekst (300): ANDDESPITETHEABILITYVHICHMISSAUSTENHASSHOVNINVORKING
              OUTTHESTORYIFORONESHOULDPUTPRIDEANDPREJUDICE...
```

(Litera `V` to `W` zamienione przez szyfr — pamiętaj, alfabet ma 25 liter.)

**Jak sprawdzić czy się udało:** zobacz plik `solutions.txt`. Jeśli
początek odszyfrowanego tekstu zgadza się z tym co tam jest — sukces.

---

### Test 3: Atak na niemiecki przykład

```bash
python3 cadenus_attack_Olko.py ciphertext_german.txt -l de -k 8 -r 6
```

To samo co wyżej, ale po niemiecku. Po około minucie powinno wyjść:

```
Tekst (300): ...NERVOSENBEVEGUNGIMSESSELVORELLGEBLUMTERSEIDE...
```

To fragment **Buddenbrooks** Tomasza Manna.

---

### Test 4: Detektyw nie zna długości klucza

W realnym scenariuszu nie wiemy ile liter ma klucz. Pomińmy `-k`:

```bash
python3 cadenus_attack_Olko.py ciphertext_english.txt -l en -r 6
```

**Co się stanie:** Program sam wykombinuje, jakie długości klucza są
możliwe (na podstawie długości tekstu — musi być wielokrotnością `|alfabet|*N`)
i wypróbuje każdą z nich. Potrwa dłużej (kilka minut), bo musi przejść
przez kilka kandydatów.

---

### Test 5: Wygenerowanie własnej zagadki

Chcesz zrobić nową zagadkę z innym losowym kluczem?

```bash
python3 make_sample.py
```

**Co się stanie:** Nadpisze pliki `ciphertext_english.txt`,
`ciphertext_german.txt` i `solutions.txt`. Każde uruchomienie da inny
losowy klucz.

**Czego oczekujesz:**

```
== ENG ==
Klucz angielski (N=8): GLNXFDEV
Dlugosc kryptotekstu: 800
== DE ==
Klucz niemiecki (N=8): ABKTOMFV
Dlugosc kryptotekstu: 800
Zapisano solutions.txt z weryfikacja.
```

Potem możesz uruchomić atak (Test 2 lub 3) na świeżej zagadce.

---

### Test 6: Zapis wyniku do pliku

Jeśli chcesz mieć wynik na stałe:

```bash
python3 cadenus_attack_Olko.py ciphertext_english.txt -l en -k 8 -r 6 -o wynik.txt
```

Po zakończeniu w `wynik.txt` znajdziesz znaleziony klucz, fitness oraz
**cały** odszyfrowany tekst.

---

### Test 7: Skrypty startowe (zamiast `python3 ...`)

Dokładnie to samo co wyżej, ale krócej:

**Linux/Mac:**

```bash
./start.sh ciphertext_english.txt -l en -k 8 -r 6
```

**Windows:**

```bat
start.bat ciphertext_english.txt -l en -k 8 -r 6
```

---

### Test 8: Egzamin detektywa (długi)

Jak dobry jest nasz detektyw? Niech rozwiąże 10 zagadek z każdej
konfiguracji i policzymy procent sukcesów:

```bash
python3 test_attack.py
```

**UWAGA:** to potrwa **kilkadziesiąt minut do paru godzin** (w zależności
od komputera), bo testuje wiele kombinacji. Możesz przerwać Ctrl+C w
dowolnym momencie — wyniki wcześniejszych konfiguracji już zobaczysz na
ekranie.

**Czego oczekujesz** (po każdej konfiguracji jedna linijka):

```
N= 8  L= 400  restarty=10  sukces= 9/10 ( 90.0%)  sr.czas= 18.4s
```

Czyli: dla klucza długości 8, tekstu 400 znaków, 10 restartów —
udało się 9 razy na 10, średnio po 18 sekundach.

---

## Co znaczą te „dziwne” wartości?

### Score / fitness

To liczba ujemna typu `-3315` lub `-4700`. **Im bliższa zera, tym lepiej.**

- Tekst losowy ma fitness około `-4700`.
- Tekst poprawnie odszyfrowany — około `-3300`.
- Cokolwiek powyżej `-3400` to praktycznie na pewno dobry wynik.

To jest miara: „jak bardzo to wygląda jak prawdziwy angielski”.

### Klucz `RAYZQAFH|order=[2,3,1,5,6,7,4,0]`

Czasami klucz wyświetla się dziwnie. To znaczy że detektyw znalazł
matematycznie poprawny klucz, ale **nie da się go zapisać jako jedno
słowo** (różne słowa-klucze mogą dawać ten sam efekt). Nie martw się —
ważne jest że **odszyfrowany tekst się zgadza**.

### N

Długość klucza (np. N=8 to klucz z 8 liter).

### L

Długość kryptotekstu w znakach (np. L=800).

---

## Co od czego zależy?

```
[Książki w corpora/]
       ↓
[build_ngrams.py]   ← uruchom RAZ żeby zbudować statystyki
       ↓
[english_quadgrams.txt, german_quadgrams.txt]
       ↓
       ├──→ [make_sample.py] ──→ [ciphertext_*.txt + solutions.txt]
       │           ↑                       ↓
       │    używa cadenus_cipher.py        ↓
       │                                   ↓
       └────→ [cadenus_attack_Olko.py] ←───┘
                       ↑
              używa cadenus_cipher.py
              (tylko do deszyfrowania)
```

**Zasada:** żeby uruchomić atak (główny program), potrzebujesz tylko
trzech rzeczy:

1. plik z kryptotekstem (`ciphertext_english.txt` jest gotowy),
2. plik statystyk (`english_quadgrams.txt` jest gotowy),
3. moduł szyfru (`cadenus_cipher.py` musi być w tym samym folderze).

Resztą się nie przejmuj — działa od ręki.

---

## Najczęstsze pytania

**„Detektyw nie znalazł rozwiązania, co robić?”**
Daj mu więcej restartów: `-r 30` zamiast `-r 6`. Albo użyj dłuższego
tekstu (krótkie teksty są trudniejsze).

**„Klucz wyszedł inny niż w `solutions.txt`, to źle?”**
Nie! Sprawdź **odszyfrowany tekst**. Jeśli jest taki sam jak prawdziwy
oryginał — jest dobrze. Różne klucze mogą dawać ten sam wynik.

**„Czemu w tekście są same duże litery i `V` zamiast `W`?”**
W angielskim Cadenus używa alfabetu 25-literowego — `W` jest mapowane na `V`.
W niemieckim alfabet ma 30 liter i nie ma redukcji do 25.

**„Czy klucz jest czyszczony albo modyfikowany?”**
Nie. Klucz jest używany dokładnie tak, jak go podasz (nie ma czyszczenia ani
zamiany znaków w kluczu). To była jedna z uwag prowadzącego.

**„Czemu nie ma spacji w tekście?”**
Bo zadanie wymaga, żeby spacje były usunięte przed szyfrowaniem.
Czytelność cierpi, ale to standard w kryptoanalizie szyfrów blokowych.

**„Czemu test_attack.py trwa tak długo?”**
Bo robi dziesiątki ataków po kolei. Możesz w pliku `test_attack.py`
zmniejszyć `trials=10` na np. `trials=3` — będzie 3x szybszy.

**„Czy mogę przerwać atak w połowie?”**
Tak — Ctrl+C. Stracisz aktualny postęp.

---

## TL;DR — najszybszy sposób żeby coś zobaczyć

```bash
# 1. wygeneruj świeżą zagadkę z losowym kluczem
python3 make_sample.py

# 2. zobacz prawdziwy klucz (do późniejszego porównania)
cat solutions.txt

# 3. każ detektywowi ją złamać (1-2 minuty)
python3 cadenus_attack_Olko.py ciphertext_english.txt -l en -k 8 -r 6

# 4. porównaj odszyfrowany tekst z tym, co jest w solutions.txt
```

Jeśli odszyfrowany tekst zaczyna się tak samo jak `english plain[:200]`
w `solutions.txt` — projekt działa. Koniec.
