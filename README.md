# CadenusCipher-Cryptanalysis-Python

Projekt zawiera implementacje szyfru Cadenus (alfabet 25-literowy) oraz
atak heurystyczny oparty o quadgramy i shotgun hill-climbing. Sa tu tez
narzedzia do budowy statystyk n-gramow, generowania przykladowych
kryptotekstow i prostych testow skutecznosci.

## Pliki i role

- cadenus_cipher.py
  - clean_text(), generate_random_key(), encrypt(), decrypt()
  - Brak logiki ataku; tylko szyfrowanie/deszyfrowanie i narzedzia.
- cadenus_attack_Olko.py
  - Glowny program ataku. Czyta kryptotekst z pliku, uruchamia atak,
    drukuje wynik i opcjonalnie zapisuje do pliku.
- build_ngrams.py
  - Buduje statystyki quadgramow z korpusow w corpora/.
- make_sample.py
  - Tworzy przykladowe kryptoteksty i plik solutions.txt do weryfikacji.
- test_attack.py
  - Proste testy: procent sukcesow, czas, minimalna dlugosc tekstu.
- english_quadgrams.txt / german_quadgrams.txt
  - Statystyki quadgramow do funkcji fitness.
- ciphertext_english.txt / ciphertext_german.txt
  - Przykladowe kryptoteksty (angielski + drugi jezyk).
- corpora/
  - Korpusy zrodlowe do statystyk.
- solutions.txt
  - Wynik pomocniczy z make_sample.py (atak go nie czyta).

## Jak to dziala (skrot)

1. Dlugosc kryptotekstu musi byc wielokrotnoscia 25 \* key_length.
2. Atak reprezentuje klucz jako:
   - order: permutacja kolumn
   - shifts: przesuniecia wierszy (0..24)
3. Hill-climbing z restartami szuka dobrego order, a dla kazdego
   kandydata greedy-optymalizuje shifts.
4. Fitness = suma log-prawdopodobienstw quadgramow tekstu po deszyfrowaniu.

## Uruchomienie

Atak (domyslnie ciphertext_english.txt):

    python3 cadenus_attack_Olko.py

Parametry:

    -l en|de     jezyk (domyslnie en)
    -k N         dlugosc klucza (opcjonalnie; inaczej zgadywana)
    -r RESTARTS  liczba restartow (domyslnie 25)
    -o PATH      zapis wyniku do pliku

Skrypty pomocnicze:

    python3 build_ngrams.py     # buduje quadgramy z corpora/
    python3 make_sample.py      # generuje przykladowe kryptoteksty
    python3 test_attack.py      # uruchamia testy skutecznosci

Skrypty startowe:

    ./start.sh [args]
    start.bat [args]

## Uwagi zgodne z wymaganiami

- clean_text jest osobne i NIE jest wywolywane z encrypt/decrypt.
- Klucze przykladów sa losowe (make_sample.py, test_attack.py).
- Atak dziala tylko na kryptotekscie i nie uzywa szyfrowania.
- Kryptoteksty sa oddzielnymi plikami tekstowymi.
- Uzyty alfabet ma 25 liter (W->V), diakrytyki sa mapowane.
