"""
Modul szyfru Cadenus.
Autor: Dawid Olko

Zawiera funkcje pomocnicze: czyszczenie tekstu, generacja losowego klucza,
szyfrowanie i deszyfrowanie. Modul nie zawiera zadnej logiki ataku - jest
calkowicie odseparowany od kryptoanalizy (atak importuje stad jedynie
funkcje deszyfrowania i stale).

Opis dzialania szyfru (wariant na podstawie mattomatti.com):
- Alfabet ma 25 liter: litera 'W' jest traktowana jako 'V' (usuwana z tekstu
  jawnego/zamieniana na V).
- Klucz to slowo dlugosci N (litery roznych pozycji w alfabecie nie sa
  wymagane unikalne - dla uproszczenia generujemy klucze o unikalnych
  literach, co jest tez przyjete w klasycznym opisie).
- Tekst jawny dzielimy na bloki o dlugosci N*25. Kazdy blok zapisujemy
  do tablicy 25 wierszy x N kolumn, kolumna po kolumnie (czyli pierwsze N
  liter tekstu trafia do pierwszego wiersza, kolejne N do drugiego itd.).
- Krok 1 (przesuniecie wierszy): dla kazdej kolumny i (i = 0..N-1) bierzemy
  i-ta litere klucza i obliczamy jej pozycje w 25-literowym alfabecie
  (A=0, B=1, ..., V=21, X=22, Y=23, Z=24). Kolumne przesuwamy cyklicznie w
  gore o tyle pozycji.
- Krok 2 (permutacja kolumn): kolumny ustawiamy zgodnie z kolejnoscia
  alfabetyczna liter klucza (jak w szyfrach kolumnowych - kolumna oznaczona
  litera bliska 'A' idzie pierwsza).
- Wynik czytamy wiersz po wierszu.

Deszyfrowanie wykonuje operacje odwrotne w odwrotnej kolejnosci.
"""

import random


# --- Stale ---

# Alfabet 25-literowy: W jest tozsame z V (klasyczny opis Cadenus).
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVXYZ"
ALPHABET_SIZE = 25  # zawsze 25
LETTER_TO_INDEX = {ch: i for i, ch in enumerate(ALPHABET)}


def clean_text(text):
    """
    Przygotowuje tekst do szyfrowania: usuwa wszystko poza literami,
    zamienia na duze litery, zamienia 'W' na 'V'.
    Funkcja jest calkowicie niezalezna od szyfrowania/deszyfrowania.
    """
    out = []
    for ch in text.upper():
        if ch == 'W':
            out.append('V')
        elif 'A' <= ch <= 'Z':
            out.append(ch)
        # litery z diakrytykami obslugujemy minimalnie - mapujemy popularne
        elif ch in "ÄÖÜ":
            out.append({'Ä': 'A', 'Ö': 'O', 'Ü': 'U'}[ch])
        elif ch == 'ß':
            out.append('S')
            out.append('S')
    return "".join(out)


def generate_random_key(length):
    """Losuje klucz dlugosci `length` z liter alfabetu (bez powtorzen)."""
    if length > ALPHABET_SIZE:
        raise ValueError("Klucz nie moze byc dluzszy niz alfabet (25).")
    return "".join(random.sample(ALPHABET, length))


def _key_order(key):
    """
    Zwraca permutacje kolumn wynikajaca z porzadku alfabetycznego liter klucza.
    Wynik: lista pozycji w kluczu - order[i] mowi, z ktorej kolumny tekstu
    jawnego pochodzi i-ta kolumna kryptotekstu.
    Stabilne sortowanie (przy powtarzajacych sie literach).
    """
    indexed = sorted(range(len(key)), key=lambda i: (key[i], i))
    return indexed


def _shifts(key):
    """Lista przesuniec wierszy dla kolejnych kolumn = pozycje liter klucza."""
    return [LETTER_TO_INDEX[ch] for ch in key]


def encrypt(plaintext, key):
    """
    Szyfruje przygotowany juz tekst (same litery alfabetu).
    Tekst musi byc oczyszczony - funkcja niczego nie usuwa.
    Jezeli dlugosc nie jest wielokrotnoscia N*25, ostatni blok jest dopelniony
    literami 'X' (wartosc nie ma duzego znaczenia dla ataku, dopelnienie i
    tak jest minimalne dla dluzszych tekstow).
    """
    n = len(key)
    block_size = n * ALPHABET_SIZE
    pad = (-len(plaintext)) % block_size
    text = plaintext + 'X' * pad

    shifts = _shifts(key)
    order = _key_order(key)

    out = []
    for b in range(0, len(text), block_size):
        block = text[b:b + block_size]
        # zapis do siatki: 25 wierszy, n kolumn, czytane wierszami
        grid = [list(block[r * n:(r + 1) * n]) for r in range(ALPHABET_SIZE)]

        # 1) przesuniecie wierszy w kazdej kolumnie - cyklicznie do gory
        #    o `shifts[col]` pozycji
        new_grid = [[None] * n for _ in range(ALPHABET_SIZE)]
        for col in range(n):
            s = shifts[col]
            for row in range(ALPHABET_SIZE):
                new_grid[row][col] = grid[(row + s) % ALPHABET_SIZE][col]

        # 2) permutacja kolumn: kolumna o najmniejszej literze klucza idzie pierwsza
        permuted = [[new_grid[r][order[c]] for c in range(n)] for r in range(ALPHABET_SIZE)]

        # czytanie wierszami
        for row in permuted:
            out.extend(row)

    return "".join(out)


def decrypt_components(ciphertext, order, shifts):
    """
    Glowna funkcja deszyfrowania - operuje na (order, shifts), czyli
    pelnej matematycznej reprezentacji klucza Cadenus:
        order  - permutacja kolumn (lista pozycji 0..N-1)
        shifts - przesuniecia wierszy (lista wartosci 0..24)
    Klucz-slowo jest tylko skrotem zapisu pary (order, shifts), gdzie
    order = sortowanie alfabetyczne liter klucza, shifts = pozycje liter
    klucza w alfabecie.

    Tekst musi miec dlugosc bedaca wielokrotnoscia N*25.
    """
    n = len(order)
    block_size = n * ALPHABET_SIZE
    if len(ciphertext) % block_size != 0:
        ciphertext = ciphertext[:len(ciphertext) - (len(ciphertext) % block_size)]

    inv_order = [0] * n
    for new_col, old_col in enumerate(order):
        inv_order[old_col] = new_col

    out = [None] * len(ciphertext)
    for b in range(0, len(ciphertext), block_size):
        block = ciphertext[b:b + block_size]
        # Bezposrednia inwersja:
        #   szyfrowanie: out[r*n + c] = block_after_perm[r][c]
        #                            = grid[(r + shifts[order[c]]) % 25][order[c]]
        # Deszyfrowanie odwraca to:
        #   plain[(r + shifts[c]) % 25 * n + c] = block[r*n + inv_order[c]]
        for r in range(ALPHABET_SIZE):
            base = r * n
            for c in range(n):
                pr = (r + shifts[c]) % ALPHABET_SIZE
                out[b + pr * n + c] = block[base + inv_order[c]]

    return "".join(out)


def decrypt(ciphertext, key):
    """Deszyfruje, przyjmujac klucz w postaci slowa (litery alfabetu)."""
    return decrypt_components(ciphertext, _key_order(key), _shifts(key))


# --- Maly self-test gdy uruchamiane bezposrednio ---
if __name__ == "__main__":
    # przyklad - tylko sanity check, nie jest czescia projektu
    sample = clean_text(
        "It was the best of times, it was the worst of times, "
        "it was the age of wisdom, it was the age of foolishness."
    )
    # rozszerzamy tekst zeby byl wystarczajaco dlugi do przykladu z kluczem 8
    sample = (sample * 6)[:8 * 25 * 2]
    k = generate_random_key(8)
    c = encrypt(sample, k)
    d = decrypt(c, k)
    assert d.startswith(sample[:200]), "Deszyfrowanie nie odwraca szyfrowania!"
    print("Klucz:", k)
    print("Tekst jawny (200):", sample[:200])
    print("Kryptotekst (200):", c[:200])
    print("Po deszyfrowaniu (200):", d[:200])
    print("OK")
