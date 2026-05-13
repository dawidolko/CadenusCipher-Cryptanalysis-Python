"""
Modul szyfru Cadenus.
Autor: Dawid Olko

Zawiera funkcje pomocnicze: czyszczenie tekstu, generacja losowego klucza,
szyfrowanie i deszyfrowanie. Modul nie zawiera zadnej logiki ataku - jest
calkowicie odseparowany od kryptoanalizy (atak importuje stad jedynie
funkcje deszyfrowania i stale).

Opis dzialania szyfru (wariant na podstawie mattomatti.com):
- Dla jezyka angielskiego alfabet ma 25 liter: litera 'W' jest traktowana jako
    'V' (usuwana z tekstu jawnego/zamieniana na V).
- Dla jezyka niemieckiego alfabet jest rozszerzony do 30 liter (A-Z + Ä Ö Ü ß)
    i NIE jest redukowany do 25 liter.
- Klucz to slowo dlugosci N (litery roznych pozycji w alfabecie nie sa
  wymagane unikalne - dla uproszczenia generujemy klucze o unikalnych
  literach, co jest tez przyjete w klasycznym opisie).
- Tekst jawny dzielimy na bloki o dlugosci N*|alfabet|. Kazdy blok zapisujemy
    do tablicy |alfabet| wierszy x N kolumn, kolumna po kolumnie (czyli pierwsze N
    liter tekstu trafia do pierwszego wiersza, kolejne N do drugiego itd.).
- Krok 1 (przesuniecie wierszy): dla kazdej kolumny i (i = 0..N-1) bierzemy
    i-ta litere klucza i obliczamy jej pozycje w odpowiednim alfabecie.
    Kolumne przesuwamy cyklicznie w gore o tyle pozycji.
- Krok 2 (permutacja kolumn): kolumny ustawiamy zgodnie z kolejnoscia
  alfabetyczna liter klucza (jak w szyfrach kolumnowych - kolumna oznaczona
  litera bliska 'A' idzie pierwsza).
- Wynik czytamy wiersz po wierszu.

Deszyfrowanie wykonuje operacje odwrotne w odwrotnej kolejnosci.
"""

import random


# --- Stale ---

# Alfabety jezykowe.
ALPHABET_EN = "ABCDEFGHIJKLMNOPQRSTUVXYZ"  # 25 liter, W->V
ALPHABET_DE = "ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜß"  # 30 liter

ALPHABETS = {
    "en": ALPHABET_EN,
    "de": ALPHABET_DE,
}

LETTER_TO_INDEX = {k: {ch: i for i, ch in enumerate(a)} for k, a in ALPHABETS.items()}


def get_alphabet(lang="en"):
    return ALPHABETS.get(lang, ALPHABET_EN)


def get_alphabet_size(lang="en"):
    return len(get_alphabet(lang))


def clean_text(text, lang="en"):
    """
    Przygotowuje tekst do szyfrowania: usuwa wszystko poza literami,
    zamienia na duze litery. Dla angielskiego dodatkowo zamienia 'W' na 'V'.
    Funkcja jest calkowicie niezalezna od szyfrowania/deszyfrowania.
    """
    out = []
    if lang == "de":
        alphabet = ALPHABET_DE
        for ch in text:
            if ch in "äöü":
                ch = ch.upper()
            elif ch == "ß":
                ch = "ß"
            else:
                ch = ch.upper()
            if ch in alphabet:
                out.append(ch)
    else:
        for ch in text.upper():
            if ch == 'W':
                out.append('V')
            elif 'A' <= ch <= 'Z':
                out.append(ch)
    return "".join(out)


def generate_random_key(length, lang="en"):
    """Losuje klucz dlugosci `length` z liter alfabetu (bez powtorzen)."""
    alphabet = get_alphabet(lang)
    if length > len(alphabet):
        raise ValueError("Klucz nie moze byc dluzszy niz alfabet.")
    return "".join(random.sample(alphabet, length))


def _key_order(key):
    """
    Zwraca permutacje kolumn wynikajaca z porzadku alfabetycznego liter klucza.
    Wynik: lista pozycji w kluczu - order[i] mowi, z ktorej kolumny tekstu
    jawnego pochodzi i-ta kolumna kryptotekstu.
    Stabilne sortowanie (przy powtarzajacych sie literach).
    """
    indexed = sorted(range(len(key)), key=lambda i: (key[i], i))
    return indexed


def _shifts(key, lang="en"):
    """Lista przesuniec wierszy dla kolejnych kolumn = pozycje liter klucza."""
    letter_to_index = LETTER_TO_INDEX.get(lang, LETTER_TO_INDEX["en"])
    return [letter_to_index[ch] for ch in key]


def encrypt(plaintext, key, lang="en"):
    """
    Szyfruje przygotowany juz tekst (same litery alfabetu).
    Tekst musi byc oczyszczony - funkcja niczego nie usuwa.
    Jezeli dlugosc nie jest wielokrotnoscia N*|alfabet|, ostatni blok jest dopelniony
    losowymi literami alfabetu (dopelnienie jest minimalne).
    """
    n = len(key)
    alphabet_size = get_alphabet_size(lang)
    block_size = n * alphabet_size
    pad = (-len(plaintext)) % block_size
    alphabet = get_alphabet(lang)
    if pad:
        pad_text = "".join(random.choice(alphabet) for _ in range(pad))
        text = plaintext + pad_text
    else:
        text = plaintext

    shifts = _shifts(key, lang=lang)
    order = _key_order(key)

    out = []
    for b in range(0, len(text), block_size):
        block = text[b:b + block_size]
        # zapis do siatki: 25 wierszy, n kolumn, czytane wierszami
        grid = [list(block[r * n:(r + 1) * n]) for r in range(alphabet_size)]

        # 1) przesuniecie wierszy w kazdej kolumnie - cyklicznie do gory
        #    o `shifts[col]` pozycji
        new_grid = [[None] * n for _ in range(alphabet_size)]
        for col in range(n):
            s = shifts[col]
            for row in range(alphabet_size):
                new_grid[row][col] = grid[(row + s) % alphabet_size][col]

        # 2) permutacja kolumn: kolumna o najmniejszej literze klucza idzie pierwsza
        permuted = [[new_grid[r][order[c]] for c in range(n)] for r in range(alphabet_size)]

        # czytanie wierszami
        for row in permuted:
            out.extend(row)

    return "".join(out)


def decrypt_components(ciphertext, order, shifts, alphabet_size):
    """
    Glowna funkcja deszyfrowania - operuje na (order, shifts), czyli
    pelnej matematycznej reprezentacji klucza Cadenus:
        order  - permutacja kolumn (lista pozycji 0..N-1)
        shifts - przesuniecia wierszy (lista wartosci 0..|alfabet|-1)
    Klucz-slowo jest tylko skrotem zapisu pary (order, shifts), gdzie
    order = sortowanie alfabetyczne liter klucza, shifts = pozycje liter
    klucza w alfabecie.

    Tekst musi miec dlugosc bedaca wielokrotnoscia N*|alfabet|.
    """
    n = len(order)
    block_size = n * alphabet_size
    if len(ciphertext) % block_size != 0:
        raise ValueError("Dlugosc kryptotekstu musi byc wielokrotnoscia N*|alfabet|.")

    inv_order = [0] * n
    for new_col, old_col in enumerate(order):
        inv_order[old_col] = new_col

    out = [None] * len(ciphertext)
    for b in range(0, len(ciphertext), block_size):
        block = ciphertext[b:b + block_size]
        # Bezposrednia inwersja:
        #   szyfrowanie: out[r*n + c] = block_after_perm[r][c]
        #                            = grid[(r + shifts[order[c]]) % |alfabet|][order[c]]
        # Deszyfrowanie odwraca to:
        #   plain[(r + shifts[c]) % |alfabet| * n + c] = block[r*n + inv_order[c]]
        for r in range(alphabet_size):
            base = r * n
            for c in range(n):
                pr = (r + shifts[c]) % alphabet_size
                out[b + pr * n + c] = block[base + inv_order[c]]

    return "".join(out)


def decrypt_indices(cipher_idx, order, shifts, alphabet_size, inv_order=None):
    """
    Szybkie deszyfrowanie do listy indeksow liter (bez skladania stringa).
    Gdy podasz `inv_order`, unikamy ponownego liczenia inwersji permutacji.
    """
    if inv_order is None:
        if order is None:
            raise ValueError("Brak order dla deszyfrowania indeksow.")
        n = len(order)
        inv_order = [0] * n
        for new_col, old_col in enumerate(order):
            inv_order[old_col] = new_col
    else:
        n = len(inv_order)

    block_size = n * alphabet_size
    if len(cipher_idx) % block_size != 0:
        raise ValueError("Dlugosc kryptotekstu musi byc wielokrotnoscia N*|alfabet|.")

    out = [0] * len(cipher_idx)
    for b in range(0, len(cipher_idx), block_size):
        block = cipher_idx[b:b + block_size]
        for r in range(alphabet_size):
            base = r * n
            for c in range(n):
                pr = (r + shifts[c]) % alphabet_size
                out[b + pr * n + c] = block[base + inv_order[c]]

    return out


def decrypt(ciphertext, key, lang="en"):
    """Deszyfruje, przyjmujac klucz w postaci slowa (litery alfabetu)."""
    return decrypt_components(
        ciphertext,
        _key_order(key),
        _shifts(key, lang=lang),
        get_alphabet_size(lang),
    )


# --- Maly self-test gdy uruchamiane bezposrednio ---
if __name__ == "__main__":
    # przyklad - tylko sanity check, nie jest czescia projektu
    sample = clean_text(
        "It was the best of times, it was the worst of times, "
        "it was the age of wisdom, it was the age of foolishness."
    )
    # rozszerzamy tekst zeby byl wystarczajaco dlugi do przykladu z kluczem 8
    sample = (sample * 6)[:8 * get_alphabet_size("en") * 2]
    k = generate_random_key(8, lang="en")
    c = encrypt(sample, k, lang="en")
    d = decrypt(c, k, lang="en")
    assert d.startswith(sample[:200]), "Deszyfrowanie nie odwraca szyfrowania!"
    print("Klucz:", k)
    print("Tekst jawny (200):", sample[:200])
    print("Kryptotekst (200):", c[:200])
    print("Po deszyfrowaniu (200):", d[:200])
    print("OK")
