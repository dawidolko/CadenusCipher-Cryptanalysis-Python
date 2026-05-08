"""
Skrypt pomocniczy: tworzy 2 przykladowe kryptoteksty.
- ciphertext_english.txt  (angielski, klucz losowy dlugosci 8)
- ciphertext_german.txt   (niemiecki, klucz losowy dlugosci 8)
Tekst jawny brany jest z korpusow w katalogu corpora/, oczyszczony i obciety
do okolo 800 znakow (wystarczy do sprawnego ataku).

Uruchom: python3 make_sample.py
Wynik zapisuje rowniez plik solutions.txt z prawdziwymi kluczami i tekstami,
zeby mozna bylo zweryfikowac wynik ataku.
"""

import random
from cadenus_cipher import clean_text, encrypt, generate_random_key, get_alphabet_size


def make_sample(corpus_path, out_path, key_len=8, target_len=800, lang="en"):
    with open(corpus_path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    cleaned = clean_text(text, lang=lang)
    # Wybieramy fragment, ktory zaczyna sie po naglowku Gutenberga (ok. 5000 znakow)
    start = 5000
    block_size = key_len * get_alphabet_size(lang)
    # zaokraglamy do pelnych blokow (ok. target_len znakow)
    n_blocks = max(1, target_len // block_size)
    length = n_blocks * block_size
    plain = cleaned[start:start + length]

    key = generate_random_key(key_len, lang=lang)
    cipher = encrypt(plain, key, lang=lang)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(cipher)

    return key, plain, cipher


if __name__ == "__main__":
    random.seed()  # losowy klucz - zgodnie z wymaganiami

    print("== ENG ==")
    k_en, p_en, c_en = make_sample(
        "corpora/pride_and_prejudice.txt", "ciphertext_english.txt",
        key_len=8, target_len=800,
        lang="en",
    )
    print(f"Klucz angielski (N={len(k_en)}): {k_en}")
    print(f"Dlugosc kryptotekstu: {len(c_en)}")

    print()
    print("== DE ==")
    k_de, p_de, c_de = make_sample(
        "corpora/buddenbrooks.txt", "ciphertext_german.txt",
        key_len=8, target_len=800,
        lang="de",
    )
    print(f"Klucz niemiecki (N={len(k_de)}): {k_de}")
    print(f"Dlugosc kryptotekstu: {len(c_de)}")

    with open("solutions.txt", "w", encoding="utf-8") as f:
        f.write("# Plik weryfikacyjny - pokazuje prawdziwe klucze i poczatki tekstow.\n")
        f.write("# Atak NIE czyta tego pliku!\n\n")
        f.write(f"english key: {k_en}\n")
        f.write(f"english plain[:200]: {p_en[:200]}\n\n")
        f.write(f"german  key: {k_de}\n")
        f.write(f"german  plain[:200]: {p_de[:200]}\n")
    print("\nZapisano solutions.txt z weryfikacja.")
