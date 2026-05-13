# Szyfr Cadenus — kryptoanaliza (Dawid Olko)

> Projekt nr 16 z listy tematów. Temat: „Szyfr Cadenus. Atak metodą genetyczną
> lub memetyczną lub analityczną”.

Kompletna implementacja **szyfru Cadenus** (angielski alfabet 25-literowy
z W=V oraz niemiecki alfabet 30-literowy z Ä Ö Ü ß) wraz z **atakiem
heurystycznym typu memetycznego**: dwufazowy hill-climbing z losowymi
restartami (shotgun) + greedy-optymalizacja przesunięć wierszy (lokalne
przeszukanie wewnątrz pętli ewolucyjnej).

Atak operuje **wyłącznie na kryptotekście** — nie ma żadnej wiedzy o kluczu
ani tekście jawnym. Funkcja oceny (fitness) bazuje na log-prawdopodobieństwach
quadgramów języka.

---

## 1. Spis plików

| Plik                     | Rola                                                                                                                                                                             |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `cadenus_cipher.py`      | Moduł szyfru: `clean_text`, `generate_random_key`, `encrypt`, `decrypt`, `decrypt_components`, `decrypt_indices`. **Brak jakiejkolwiek logiki ataku.**                           |
| `cadenus_attack_Olko.py` | Główny program z atakiem. Wczytuje kryptotekst z pliku, drukuje wynik, opcjonalnie zapisuje do pliku. Z modułu szyfru importuje **tylko** `decrypt_indices` oraz stałe alfabetu. |
| `build_ngrams.py`        | Skrypt do **wygenerowania** statystyk quadgramów z korpusów w `corpora/`. Uruchamia się raz; potem wystarczają same pliki `*_quadgrams.txt`.                                     |
| `english_quadgrams.txt`  | Statystyki języka angielskiego (~53 tys. quadgramów, korpus ≈ 1,5 mln znaków: _Pride and Prejudice_ + _Moby Dick_).                                                              |
| `german_quadgrams.txt`   | Statystyki języka niemieckiego (~40 tys. quadgramów, korpus ≈ 1,2 mln znaków: _Buddenbrooks_).                                                                                   |
| `ciphertext_english.txt` | Przykładowy kryptotekst angielski (długość 800, klucz losowy długości 8).                                                                                                        |
| `ciphertext_german.txt`  | Przykładowy kryptotekst niemiecki (długość 800, klucz losowy długości 8).                                                                                                        |
| `make_sample.py`         | Generator powyższych dwóch przykładów (bierze fragmenty korpusu, szyfruje **losowym** kluczem).                                                                                  |
| `solutions.txt`          | Plik weryfikacyjny — prawdziwy klucz i początek tekstu jawnego dla obu przykładów. **Atak go nie czyta** — służy tylko Tobie do sprawdzenia poprawności.                         |
| `test_attack.py`         | Program testowy: liczy procent sukcesów i średni czas dla różnych konfiguracji `(N klucza, długość tekstu, liczba restartów)`. Wyniki przykładowe w komentarzu na dole pliku.    |
| `corpora/`               | Korpusy źródłowe dla `build_ngrams.py` (Project Gutenberg, public domain). Niepotrzebne do działania ataku — wystarczą same pliki `*_quadgrams.txt`.                             |
| `start.sh`, `start.bat`  | Skrypty startowe (Linux/macOS i Windows). Przekazują argumenty bezpośrednio do programu ataku.                                                                                   |

---

## 2. Wymagania

- Python 3.8+ (testowane na 3.11 i 3.13).
- **Brak zewnętrznych bibliotek** — używa wyłącznie standardowej biblioteki
  Pythona (`random`, `math`, `os`, `sys`, `time`, `collections`).
- Działa na macOS, Linux i Windows.

---

## 3. Szybki start

```bash
# atak na przykładowy kryptotekst angielski
./start.sh
# albo równoważnie:
python3 cadenus_attack_Olko.py
```

```bash
# atak na niemiecki przykład, znana długość klucza N=8, 25 restartów
./start.sh ciphertext_german.txt -l de -k 8 -r 25
```

```bat
REM Windows
start.bat ciphertext_english.txt -l en -k 8 -r 25
```

Po skończeniu program drukuje:

- czas pracy,
- znaleziony klucz (w formie słowa, a jeśli nie da się jednoznacznie
  zrekonstruować słowa — w formie `słowo|order=[...]`),
- końcowy fitness,
- pierwsze 300 znaków odszyfrowanego tekstu.

Możesz porównać wynik z `solutions.txt` (zawiera prawdziwy klucz i
początek tekstu jawnego dla przykładów).

### Argumenty programu ataku

| Flaga                         | Znaczenie                                      | Domyślnie                       |
| ----------------------------- | ---------------------------------------------- | ------------------------------- | ---- |
| (pierwszy argument bez flagi) | ścieżka do pliku z kryptotekstem               | `ciphertext_english.txt`        |
| `-l en                        | de`                                            | język statystyk (`en` lub `de`) | `en` |
| `-k N`                        | znana długość klucza (jeśli brak — odgadywana) | brak                            |
| `-r RESTARTY`                 | liczba losowych restartów hill-climbing        | `25`                            |
| `-o PATH`                     | zapisz pełny wynik do pliku                    | brak                            |
| `-h, --help`                  | pokaż docstring programu                       | —                               |

---

## 4. Jak działa szyfr Cadenus

Wariant zgodny z opisem ze strony **mattomatti.com/pl/mcipher**, z
zastrzeżeniem że spacje są **usuwane** (zgodnie z uwagą w treści projektu).

**Alfabet angielski (25-literowy):** `ABCDEFGHIJKLMNOPQRSTUVXYZ` — litera `W`
jest traktowana jako `V`.

**Alfabet niemiecki (30-literowy):** `ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜß` —
nie jest redukowany do 25 liter.

**Klucz** to słowo długości `N` (typowo 6–12). Każda litera klucza ma w
alfabecie pozycję 0..|alfabet|-1.

**Szyfrowanie** (jeden blok długości `|alfabet| * N`):

1. Wpisz blok do siatki **|alfabet| wierszy × N kolumn**, czytając po wierszach
   (pierwsze N liter to pierwszy wiersz itd.).
2. **Krok 1 — przesunięcie wierszy:** dla każdej kolumny `i` weź pozycję
   `i`-tej litery klucza w alfabecie i przesuń tę kolumnę cyklicznie w górę
   o tyle pozycji.
3. **Krok 2 — permutacja kolumn:** ułóż kolumny w kolejności alfabetycznej
   liter klucza (kolumna oznaczona literą bliską `A` idzie pierwsza —
   klasyka szyfrów kolumnowych).
4. Odczytaj siatkę wiersz po wierszu — to kryptotekst dla bloku.

Tekst dłuższy od jednego bloku jest dzielony na bloki długości `|alfabet| * N`.
Jeśli długość nie jest wielokrotnością `|alfabet| * N`, ostatni blok jest dopełniony
losowymi literami alfabetu (minimalnie).
Deszyfrowanie zgłasza błąd, gdy długość kryptotekstu nie pasuje do `|alfabet| * N`.
W pozostałych przypadkach wykonuje operacje odwrotne w odwrotnej kolejności.

**Reprezentacja klucza w kodzie:** klucz jest matematycznie równoważny parze
`(order, shifts)`, gdzie:

- `order` — permutacja kolumn (lista długości N, wartości 0..N-1),
- `shifts` — wektor przesunięć wierszy (lista długości N, wartości 0..|alfabet|-1).

Pełny moduł szyfru obsługuje obie reprezentacje: `decrypt(cipher, "GLNXFDEV")`
oraz `decrypt_components(cipher, [5,6,4,0,1,2,7,3], [6,11,13,22,5,3,4,21])`
dają identyczny wynik.

---

## 5. Jak działa atak

### Pomysł

W szyfrze Cadenus klucz to **dwa nieco niezależne komponenty**: permutacja
kolumn `order` (`N!` wariantów) i wektor przesunięć `shifts` (`|alfabet|^N`
wariantów). Jeśli `order` jest poprawne, każdy `shifts[c]` można dobrać
**niezależnie** od pozostałych — wystarczy przejrzeć |alfabet| możliwości. Ta
obserwacja jest sercem ataku.

### Algorytm (memetyczny shotgun hill-climbing)

Dla każdej kandydującej długości klucza `N` wykonujemy `R` restartów; w
każdym restarcie:

1. **Faza 1** — losowa permutacja `order`, hill-climbing po `order` (mała
   zmiana = swap dwóch pozycji). **Każdą** kandydującą permutację
   ewaluujemy uruchamiając mały _coordinate descent_ po `shifts` (greedy
   `optimize_shifts_greedy`: dla każdej kolumny próbujemy wszystkie |alfabet|
   możliwych przesunięć i wybieramy najlepsze; powtarzamy aż brak poprawy).
   To czyni metodę **memetyczną** — ewolucyjne przeszukanie globalne z
   lokalnym dopasowaniem na każdym kroku.

   Dla wydajności fitness jest liczony na indeksach liter, z tablicy quadgramów
   o rozmiarze `|alfabet|^4` (bez wycinania fragmentów stringa).

2. **Faza 2** — gdy hill-climbing utyka, jeszcze raz dokładnie dostraja
   shifty w 4 przebiegach po `N` kolumnach.

Rezultat: znajdujemy `(order, shifts)` z najwyższym fitnessem ze wszystkich
restartów.

### Dlaczego N (długość klucza) zwykle odgadnie się samoczynnie

Długość kryptotekstu jest **wielokrotnością `|alfabet| * N`** (dopełniona przy
szyfrowaniu). Dla typowych długości 300–1500 znaków zostaje 1–4 sensownych
kandydatów `N` z zakresu 4..12. Program próbuje je w kolejności od
najdłuższych (zgodnie z wymaganiem prowadzącego, że klucz powinien mieć
**przynajmniej 8 liter**).

### Funkcja fitness

```
score(text) = Σ log10 P(quadgram)
```

z wygładzeniem log10(0.01 / total) dla quadgramów niewystępujących w
korpusie. Tekst „czytelny” daje średnio około `-3.05` na quadgram; tekst
losowy około `-4.7`. Jako warunek wczesnego zakończenia hill-climba używamy
progu `-3.05 * (len(text) - 3)`.

### Spełnione zalecenia z punktów 9 i 10 wykładu

- **9a — najmniejsza możliwa zmiana podstawowa:** swap dwóch pozycji w
  `order` zmienia kolejność dwóch kolumn (zwykle kilka procent fitness),
  a wewnętrzny coordinate descent po shiftach wykonuje mikro-zmiany
  pojedynczych kolumn.
- **9b — możliwość dotarcia do dowolnego klucza:** swap-y permutacji
  generują pełną grupę symetryczną `S_N`, a wewnętrzny greedy po shiftach
  pokrywa pełny zakres 0..|alfabet|-1 dla każdej kolumny. Łącznie pokrywamy całą
  przestrzeń kluczy. Dodatkowo `random.shuffle` w restartach losuje pełnym
  rozkładem.
- **10 — dziedziczenie informacji w ramach hill-climba:** każda zaakceptowana
  zmiana zachowuje wszystkie pozostałe „geny” (tylko 2 pozycje permutacji są
  zamieniane), a coordinate descent po shiftach przekazuje cały stan między
  iteracjami.

---

## 6. Z jakimi parametrami działa

Pomiary na MacBook M-class, Python 3.11, jeden proces, **klucz losowy**:

| Język | N (klucz) | Długość tekstu | Restartów | % sukcesów | Średni czas |
| ----- | --------- | -------------- | --------- | ---------- | ----------- |
| EN    | 6         | 300            | 8         | ~100%      | ~5 s        |
| EN    | 8         | 400            | 10        | ~90%       | ~20 s       |
| EN    | 8         | 600            | 10        | ~100%      | ~25 s       |
| EN    | 10        | 500            | 12        | ~70%       | ~75 s       |
| EN    | 10        | 750            | 12        | ~100%      | ~80 s       |
| EN    | 12        | 900            | 15        | ~90%       | ~3,5 min    |
| DE    | 6         | 300            | 8         | ~100%      | ~5 s        |
| DE    | 8         | 400            | 10        | ~80%       | ~22 s       |
| DE    | 8         | 600            | 10        | ~100%      | ~25 s       |
| DE    | 10        | 750            | 12        | ~90%       | ~90 s       |

(Dokładne wyniki Twojego sprzętu uzyskasz uruchamiając `python3 test_attack.py`.)

**Krótki wniosek:** dla N=8 wystarczy ok. 400 znaków po angielsku i ok.
500–600 po niemiecku. Dla N=10 potrzeba 700+ znaków, dla N=12 — 900+.
Główny czynnik to **długość tekstu**, nie sama długość klucza.

---

## 7. Mapa wymagań prowadzącego → realizacja w projekcie

Tę sekcję możesz pokazać prowadzącemu, żeby od razu zobaczył co zostało
zrobione:

| Wymaganie                                                                                       | Gdzie spełnione                                                                                                       |
| ----------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Funkcja szyfrująca, deszyfrująca, atak                                                          | `cadenus_cipher.py` (encrypt, decrypt), `cadenus_attack_Olko.py` (attack)                                             |
| `clean_text` osobno, **NIE wywoływane** z encrypt/decrypt                                       | `cadenus_cipher.py` — funkcja niezależna, encrypt/decrypt zakłada że tekst jest już oczyszczony                       |
| Klucz w przykładach **losowy** (a nie ustalony z góry)                                          | `make_sample.py` używa `generate_random_key` (losowy `random.sample`); `test_attack.py` losuje klucz dla każdej próby |
| Spacje **usuwane** (mimo że mattomatti używa ze spacjami)                                       | `clean_text` zostawia tylko litery                                                                                    |
| Atak czyta kryptotekst z **pliku tekstowego**, wynik na ekran (i opcjonalnie do pliku)          | `cadenus_attack_Olko.py` — pierwszy argument to ścieżka do pliku, flaga `-o` zapisuje                                 |
| Komentarz na początku głównego programu (autor, szyfr, metody, długości kluczy, czasy, wnioski) | docstring na początku `cadenus_attack_Olko.py`                                                                        |
| Atak importuje z modułu szyfru **tylko** funkcję deszyfrowania i (może) stałe                   | importowane: `decrypt_indices`, `ALPHABETS`                                                                           |
| Plik statystyk n-gramów + opcjonalny skrypt do jego budowy                                      | `english_quadgrams.txt`, `german_quadgrams.txt` + `build_ngrams.py`                                                   |
| Dwa przykładowe kryptoteksty: angielski + drugi język                                           | `ciphertext_english.txt`, `ciphertext_german.txt`                                                                     |
| Drugi język **nie polski**, tekst literacki (nie „lorem ipsum”)                                 | niemiecki, fragment _Buddenbrooks_ Tomasza Manna (z Project Gutenberg)                                                |
| Program testowy: % sukcesów, czas, minimalna długość                                            | `test_attack.py`                                                                                                      |
| Wyniki testów w komentarzu w `test_attack.py`, krótki wniosek na początku głównego programu     | komentarz na dole `test_attack.py`, sekcja w docstringu `cadenus_attack_Olko.py`                                      |
| Nazwa szyfru i nazwisko studenta w nazwie pliku/folderu                                         | nazwa repozytorium `CadenusCipher-Cryptanalysis-Python`, plik `cadenus_attack_Olko.py`                                |
| Kryptotekst ≥ 100, lepiej 150+                                                                  | przykłady mają 800 znaków, atak działa od ~300                                                                        |
| Tekst jawny w literackim angielskim (nie lorem ipsum)                                           | użyte fragmenty _Pride and Prejudice_ i _Moby Dick_ (angielski) oraz _Buddenbrooks_ (niemiecki)                       |
| Minimum importów (tylko niezbędne dla wydajności)                                               | wyłącznie `random`, `math`, `os`, `sys`, `time`, `collections` (stdlib)                                               |
| Nie produkować wielu małych bibliotek                                                           | tylko jeden moduł (`cadenus_cipher.py`) i jeden program ataku; reszta to skrypty pomocnicze                           |

### Zmiany po uwagach prowadzącego

- Klucz nie jest czyszczony ani modyfikowany w żadnej funkcji szyfru.
- Język niemiecki używa pełnego alfabetu 30-literowego (A-Z + Ä Ö Ü ß),
  bez redukcji do 25 liter.
- Szyfrowanie dopelnia brakujaca dlugosc losowymi literami alfabetu,
  a deszyfrowanie zglasza blad, gdy dlugosc nie pasuje do `|alfabet| * N`.
- Po zmianie alfabetu niemieckiego należy przebudować statystyki i przykłady:
  `python3 build_ngrams.py` oraz `python3 make_sample.py`.

### Kwestia „drugi język ma mieć 35+ liter”

Jeśli prowadzący oczekuje 35+ liter, to obecny niemiecki (30) nie spełnia
tego wymogu. W projekcie jednak niemiecki nie jest redukowany do 25 liter,
co było główną poprawką zaleconą przez prowadzącego.

---

## 8. Jak ręcznie sprawdzić poprawność szyfrowania

```bash
python3 cadenus_cipher.py
```

Wykonuje sanity-check: szyfruje krótki tekst losowym kluczem, deszyfruje i
weryfikuje że wynik jest identyczny z tekstem wejściowym.

## 9. Jak wygenerować nowy kryptotekst do testów

```bash
python3 make_sample.py
```

Nadpisuje `ciphertext_english.txt`, `ciphertext_german.txt` oraz
`solutions.txt` — z **nowym losowym** kluczem dla każdego z plików.

## 10. Pełna instrukcja dla rozmowy z prowadzącym

Prowadzący w treści zadania napisał wprost:

> „Przed rozpoczęciem pracy nad projektem na poważnie (ale lepiej po
> napisaniu funkcji szyfrowania, deszyfrowania i generacji klucza) — proszę
> porozmawiać ze mną, i doprecyzować jak szyfr działa! W niektórych
> zagadnieniach możliwe kilka wariantów działania.”

**Co powiedzieć / o co zapytać:**

1. **Wariant szyfru** — implementacja zgodna z opisem na
   _mattomatti.com/pl/mcipher_, z modyfikacją: spacje są **usuwane** (jak
   wprost wymaga zadanie). Alfabet angielski 25-literowy z W=V, niemiecki
   30-literowy z Ä Ö Ü ß. Bloki długości `|alfabet| * N`. Najpierw
   przesunięcie wierszy (kolumna `i` o pozycję `i`-tej litery klucza),
   potem permutacja kolumn (alfabetyczna kolejność liter klucza).
   Deszyfrowanie odwrotne. → **Pytanie: czy ta interpretacja jest zgodna
   z tym, czego oczekujesz?**

2. **Klucze** — generowane funkcją `generate_random_key` (losowy `sample`
   bez powtórzeń liter z odpowiedniego alfabetu). Długości N = 6, 8, 10, 12
   testowane. Klucze są **losowe** zarówno przy tworzeniu przykładowych
   kryptotekstów (`make_sample.py`), jak i przy każdej próbie testowej
   (`test_attack.py`). → **Punkt 1 z listy spełniony.**

3. **Drugi język** — niemiecki (Buddenbrooks Tomasza Manna). Alfabet
   niemiecki ma 30 liter (A-Z + Ä Ö Ü ß) i nie jest redukowany do 25 liter.
   → **Pytanie: czy taka interpretacja jest OK, czy chcesz coś innego?**

4. **Atak** — memetyczny shotgun hill-climbing (zob. sekcja 5). Spełnia
   wymagania punktów 9 i 10 wykładu (mała zmiana podstawowa, dziedziczenie
   stanu). Nie jest to **algorytm analityczny** (analityczny byłby
   wymagany do oceny 5.0). Aktualnie atak rozwiązuje klucze N=6..12 dla
   tekstów 300..900 znaków w sensownym czasie. → **Pytanie: czy heurystyka
   spełnia wymagania na 4.5, czy oczekujesz dodatkowych usprawnień?**

5. **Co spełnia punkty „obowiązkowe” z opisu projektu** — patrz sekcja 7
   tego README, mapa wymagań → realizacja. W szczególności:
   - `clean_text` jest osobne i **nie** jest wołane z `encrypt`/`decrypt`
     (punkt 2 z listy);
   - kryptotekst > 100 znaków (punkty: 800 w przykładach) (punkt 3);
   - w fitness ngramy dopasowane do alfabetu (punkt 4);
   - tekst jawny to literacki angielski/niemiecki (punkt 5);
   - atak korzysta tylko z `decrypt_indices` i stałych z modułu szyfru —
     **żadnej wiedzy o prawdziwym kluczu**.

6. **Czego brakuje do oceny 5.0** — algorytm analityczny (np. dopasowanie
   częstości w pojedynczych kolumnach, analiza wzorców kolizji). Aktualne
   rozwiązanie to silna heurystyka memetyczna z lokalnym przeszukiwaniem.
   → **Pytanie: czy zachęcasz do podejścia analitycznego, czy memetyka jest
   wystarczająca na 4.5?**

---

## 11. Licencja

MIT — patrz plik [`LICENSE`](LICENSE).

---

## 12. Szybkie komendy testowe (5 linii)

Poniższe linie możesz wkleić do konsoli po kolei, żeby szybko sprawdzić, czy wszystko działa.

```bash
python3 cadenus_cipher.py
python3 cadenus_attack_Olko.py ciphertext_english.txt -l en -k 8 -r 2
python3 cadenus_attack_Olko.py ciphertext_german.txt -l de -k 8 -r 2
python3 make_sample.py
python3 cadenus_attack_Olko.py ciphertext_english.txt -l en -k 8 -r 6 -o wynik.txt
```

Co robią te komendy:

1. **Self-test szyfru** — szyfruje i deszyfruje krótki tekst; na końcu powinno być `OK`.
2. **Szybki atak (EN)** — krótki test ataku na gotowym angielskim kryptotekście (2 restarty).
3. **Szybki atak (DE)** — to samo dla niemieckiego kryptotekstu (2 restarty).
4. **Nowe próbki** — generuje świeże `ciphertext_*.txt` i `solutions.txt` (nadpisuje pliki).
5. **Dłuższy atak + zapis** — więcej restartów i zapis wyniku do `wynik.txt`.
