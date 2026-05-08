"""
Skrypt pomocniczy: buduje pliki statystyk quadgramow z korpusow w katalogu
`corpora/`. Wynik to pliki english_quadgrams.txt i german_quadgrams.txt.

Format pliku: jedna linia "QUAD COUNT" na quadgram. Atak czyta plik i sam
przeliczy liczniki na log-prawdopodobienstwa.

Wazne: tekst jest oczyszczany TA SAMA funkcja co dla szyfrowania
(clean_text z cadenus_cipher) - dzieki temu statystyki sa zgodne z
alfabetem odpowiednim dla jezyka.
"""

import os
import sys
from collections import Counter

from cadenus_cipher import clean_text


def build(corpus_paths, out_path, n=4, lang="en"):
    counter = Counter()
    total_chars = 0
    for p in corpus_paths:
        if not os.path.exists(p):
            print(f"Pomijam (brak pliku): {p}")
            continue
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        cleaned = clean_text(text, lang=lang)
        total_chars += len(cleaned)
        for i in range(len(cleaned) - n + 1):
            counter[cleaned[i:i + n]] += 1
        print(f"  {p}: {len(cleaned)} znakow po oczyszczeniu")

    print(f"Lacznie: {total_chars} znakow, {len(counter)} unikalnych {n}-gramow")

    with open(out_path, "w", encoding="utf-8") as f:
        for quad, c in counter.most_common():
            f.write(f"{quad} {c}\n")
    print(f"Zapisano: {out_path}")


if __name__ == "__main__":
    print("== Angielski ==")
    build(
        ["corpora/pride_and_prejudice.txt", "corpora/moby_dick.txt"],
        "english_quadgrams.txt",
        n=4,
        lang="en",
    )
    print()
    print("== Niemiecki ==")
    build(
        ["corpora/buddenbrooks.txt"],
        "german_quadgrams.txt",
        n=4,
        lang="de",
    )
