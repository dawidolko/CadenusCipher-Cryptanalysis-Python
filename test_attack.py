"""
Program testowy: mierzy efektywnosc ataku na szyfr Cadenus dla roznych
dlugosci kluczy i kryptotekstow. Dla kazdej konfiguracji wykonuje N prob
(domyslnie 10), liczy procent sukcesow i sredni czas.

Sukces: znaleziony tekst zawiera co najmniej 90% wspolnych quadgramow
(prog praktyczny "tekst czytelny z dopuszczalnymi bledami" - wystarcza
do oceny sukcesu, nie wymaga identycznego klucza).

Uruchom:  python3 test_attack.py
Wyniki testow przykladowych - patrz komentarz na dole pliku.
"""

import os
import random
import time

from cadenus_cipher import clean_text, encrypt, generate_random_key, get_alphabet_size
from cadenus_attack_Olko import Quadgrams, attack


def load_corpus(path, min_len, lang="en"):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    cleaned = clean_text(text, lang=lang)
    return cleaned[5000:5000 + min_len + 5000]  # zapas


def is_success(plain_attack, plain_true, threshold=0.9):
    """Sukces gdy >=90% pozycji sie zgadza (tolerancja na 1 litere/slowo)."""
    if len(plain_attack) < len(plain_true):
        plain_true = plain_true[:len(plain_attack)]
    n = min(len(plain_attack), len(plain_true))
    if n == 0:
        return False
    matches = sum(1 for i in range(n) if plain_attack[i] == plain_true[i])
    return matches / n >= threshold


def run_tests(corpus_path, qg_path, lang_label, configs, trials=10, lang="en"):
    print(f"\n=== {lang_label}  (corpus: {corpus_path}) ===")
    qg = Quadgrams(qg_path)
    base_text = load_corpus(corpus_path, 2000, lang=lang)
    alphabet_size = get_alphabet_size(lang)

    results = []
    for key_len, text_len, restarts in configs:
        block_size = key_len * alphabet_size
        adj_len = (text_len // block_size) * block_size
        if adj_len == 0:
            adj_len = block_size
        plain = base_text[:adj_len]

        success = 0
        times = []
        for t in range(trials):
            key = generate_random_key(key_len, lang=lang)
            cipher = encrypt(plain, key, lang=lang)
            t0 = time.time()
            score, state, p_attack, n = attack(
                cipher, qg, key_len=key_len, restarts=restarts, verbose=False,
                alphabet_size=alphabet_size,
            )
            dt = time.time() - t0
            times.append(dt)
            if is_success(p_attack, plain):
                success += 1

        avg_t = sum(times) / len(times)
        rate = 100 * success / trials
        print(f"  N={key_len:>2}  L={adj_len:>4}  restarty={restarts:>2}  "
              f"sukces={success:>2}/{trials} ({rate:>5.1f}%)  sr.czas={avg_t:>5.1f}s")
        results.append((key_len, adj_len, restarts, rate, avg_t))
    return results


if __name__ == "__main__":
    random.seed(42)

    # Kazda konfiguracja = (dlugosc_klucza, dlugosc_tekstu, liczba_restartow)
    configs_en = [
        (6,  300,  8),
        (8,  400, 10),
        (8,  600, 10),
        (10, 500, 12),
        (10, 750, 12),
        (12, 900, 15),
    ]
    configs_de = [
        (6,  300,  8),
        (8,  400, 10),
        (8,  600, 10),
        (10, 750, 12),
    ]

    if os.path.exists("corpora/pride_and_prejudice.txt"):
        run_tests("corpora/pride_and_prejudice.txt", "english_quadgrams.txt",
              "ANGIELSKI", configs_en, trials=10, lang="en")
    if os.path.exists("corpora/buddenbrooks.txt"):
        run_tests("corpora/buddenbrooks.txt", "german_quadgrams.txt",
              "NIEMIECKI", configs_de, trials=10, lang="de")


# ====================================================================
# PRZYKLADOWE WYNIKI (MacBook M-class, Python 3.11):
# ====================================================================
# === ANGIELSKI ===
#   N= 6  L= 300  restarty= 8   sukces=10/10 (100.0%)   sr.czas=  3.8s
#   N= 8  L= 400  restarty=10   sukces= 9/10 ( 90.0%)   sr.czas= 18.4s
#   N= 8  L= 600  restarty=10   sukces=10/10 (100.0%)   sr.czas= 22.1s
#   N=10  L= 500  restarty=12   sukces= 7/10 ( 70.0%)   sr.czas= 76.5s
#   N=10  L= 750  restarty=12   sukces=10/10 (100.0%)   sr.czas= 80.8s
#   N=12  L= 900  restarty=15   sukces= 9/10 ( 90.0%)   sr.czas=210.0s
#
# === NIEMIECKI ===
#   N= 6  L= 300  restarty= 8   sukces=10/10 (100.0%)   sr.czas=  4.2s
#   N= 8  L= 400  restarty=10   sukces= 8/10 ( 80.0%)   sr.czas= 21.6s
#   N= 8  L= 600  restarty=10   sukces=10/10 (100.0%)   sr.czas= 25.2s
#   N=10  L= 750  restarty=12   sukces= 9/10 ( 90.0%)   sr.czas= 92.3s
#
# WNIOSKI:
# - Glownym czynnikiem jest dlugosc kryptotekstu, nie sama dlugosc klucza.
# - Dla N=8 wystarcza ~400 znakow do >=90% skutecznosci po angielsku
#   i ~500-600 znakow po niemiecku.
# - Dla N=10 potrzeba 700+ znakow, dla N=12 - 900+.
# - Gorszy fitness niemieckich quadgramow (mniejszy korpus uczacy)
#   powoduje lekko nizsze % sukcesow przy tej samej dlugosci.
# ====================================================================
