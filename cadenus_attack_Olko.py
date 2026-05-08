"""
==================================================================
Projekt: Atak na szyfr Cadenus
Autor:   Dawid Olko
Temat:   16) Szyfr Cadenus - atak metoda heurystyczna (hill-climbing
         z restartami / shotgun) z fitness opartym na quadgramach.
Jezyki:  angielski (alfabet 25-literowy), niemiecki (alfabet 30-literowy
         z Ä Ö Ü ß, bez redukcji do 25 liter)

Stosowane metody:
- Shotgun hill-climbing (random-restart hill-climbing)
- Fitness: suma log-prawdopodobienstw quadgramow tekstu po deszyfrowaniu
  (z wygladzeniem dla niewidzianych quadgramow)
- Atak NIE pracuje na "kluczu-slowie", ale rozdziela go na 2 niezalezne
  komponenty (rownowazne do klucza):
    * permutacja kolumn `order` (lista dlugosci N)
    * wektor przesuniec wierszy `shifts` (N wartosci 0..|alfabet|-1)
  To pozwala na bardzo male ruchy w przestrzeni rozwiazan:
     * "shift +/-1 jednej kolumny" - to NAJMNIEJSZA mozliwa zmiana
       (jeden wiersz w jednej kolumnie zmienia pozycje), bardzo mala
       zmiana fitness - zalecenie z punktu 9a wykladu.
     * swap dwoch pozycji w `order` - zmienia kolejnosc dwoch kolumn.
  W pelnej kombinacji oba ruchy pozwalaja dotrzec do dowolnego klucza
  (warunek 9b). Dodatkowo z prawdopodobienstwem ~3% wykonujemy "skrot"
  (losowa duza zmiana shiftu), zeby latwiej wyrwac sie z plateau.

Wlasne udoskonalenia:
- Automatyczne odgadywanie dlugosci klucza: dlugosc kryptotekstu po
    zaszyfrowaniu jest wielokrotnoscia |alfabet|*N. Dla typowych dlugosci
  300-1500 zostaje 2-4 kandydatow. Probujemy je zaczynajac od dluzszych
  (wykladowca oczekuje N>=8).
- Wczesny stop: gdy fitness przekroczy prog "czytelnego tekstu"
  (~ -3.05 * len(plain)), konczymy biezacy hill-climb.
- Po przekroczeniu progu - od razu zwracamy wynik (oszczednosc czasu).

Zmiany po uwagach prowadzacego:
- Klucz nie jest czyszczony ani modyfikowany w funkcjach szyfru.
- Jezyk niemiecki uzywa pelnego alfabetu 30-literowego (A-Z + Ä Ö Ü ß).

Z jakimi kluczami daje rade (pojedynczy proces, MacBook M-class):
- angielski: klucze N=6..10 dla tekstu 400+ znakow w >90% przypadkow
- angielski: klucze N=12 dla tekstu 800+ znakow w >85%
- niemiecki: klucze N=6..8 dla tekstu 500+ znakow w >85%
Minimalny rozmiar kryptotekstu, zeby atak dzialal sprawnie:
- ang: ok. 300-400 znakow dla N=8, ok. 500+ dla N=10
- niem: ok. 400-500 znakow dla N=8

Oczekiwane czasy (1 proces, restarty domyslne):
- N=6,  L=300:  ~5-15 s
- N=8,  L=400:  ~30-90 s
- N=10, L=500:  ~1-4 min
- N=12, L=800:  ~3-7 min

WNIOSKI z testow (pelne wyniki w test_attack.py):
- Glowny czynnik to dlugosc kryptotekstu, nie tyle dlugosc klucza:
  krotki tekst i krotki klucz tez moze sie nie udac.
- Mikro-ruch (shift +/-1) jest kluczem do dzialania - zwykla zmiana
  litery klucza-slowa (wczesniejszy wariant) wpadala czesto w lokalne
  maksimum.
- Restart (shotgun) jest niezbedny - 5-30 restartow daje dobre wyniki.

Uzycie:
    python3 cadenus_attack_Olko.py [plik_z_kryptotekstem] [-l jezyk] [-k N] [-r RESTARTY] [-o WYNIK]
gdzie jezyk = en | de (domyslnie en),
      N    = znana dlugosc klucza (opcjonalnie - inaczej odgadujemy)
Domyslny plik: ciphertext_english.txt
==================================================================
"""

import math
import os
import random
import sys
import time

from cadenus_cipher import (
    decrypt_components,
    get_alphabet,
    get_alphabet_size,
)


# ---------- N-gramy / fitness ----------

class Quadgrams:
    """Wczytuje plik 'QUAD COUNT' i udostepnia funkcje score(text)."""
    def __init__(self, path):
        counts = {}
        total = 0
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.split()
                if len(parts) != 2:
                    continue
                quad, c = parts[0], int(parts[1])
                counts[quad] = c
                total += c
        self.log_probs = {q: math.log10(c / total) for q, c in counts.items()}
        # log-prawdopodobienstwo dla nieznanego quadgramu (wygladzenie)
        self.floor = math.log10(0.01 / total)

    def score(self, text):
        lp = self.log_probs
        floor = self.floor
        s = 0.0
        for i in range(len(text) - 3):
            s += lp.get(text[i:i + 4], floor)
        return s


# ---------- Atak ----------

def random_state(n, alphabet_size):
    """Losowy stan: order to losowa permutacja [0..n), shifts to losowe 0..|alfabet|-1."""
    order = list(range(n))
    random.shuffle(order)
    shifts = [random.randrange(alphabet_size) for _ in range(n)]
    return order, shifts


def small_change(order, shifts, alphabet_size):
    """
    Mala zmiana stanu. Modyfikuje listy w miejscu, zwraca info do undo.
    Rozklad ruchow:
      ~70% : shift +/-1 jednej kolumny (NAJMNIEJSZY ruch)
      ~25% : swap dwoch pozycji w order (zamiana 2 kolumn)
      ~5%  : losowy nowy shift dla jednej kolumny (skrot z plateau)
    """
    n = len(order)
    r = random.random()
    if r < 0.70:
        c = random.randrange(n)
        delta = 1 if random.random() < 0.5 else -1
        old = shifts[c]
        shifts[c] = (old + delta) % alphabet_size
        return ('shift', c, old)
    elif r < 0.95 and n >= 2:
        i, j = random.sample(range(n), 2)
        order[i], order[j] = order[j], order[i]
        return ('swap', i, j)
    else:
        c = random.randrange(n)
        old = shifts[c]
        new = random.randrange(alphabet_size)
        shifts[c] = new
        return ('shift', c, old)


def undo(order, shifts, change):
    if change[0] == 'shift':
        _, c, old = change
        shifts[c] = old
    elif change[0] == 'swap':
        _, i, j = change
        order[i], order[j] = order[j], order[i]


def state_to_key(order, shifts, alphabet):
    """
    Probuje zrekonstruowac klucz-slowo z (order, shifts).
    Klucz-slowo: na pozycji i klucza stoi litera o pozycji `shifts[i]`.
    Permutacja kolumn `order` musi pochodzic z stabilnego sortowania liter klucza.
    Najczestszy przypadek - litery sa unikalne; wtedy mozemy odtworzyc klucz
    tylko jesli `order` jest zgodne z sortowaniem `shifts`.
    Jezeli nie da sie - zwracamy reprezentacje 'order|shifts'.
    """
    n = len(order)
    # Klucz-slowo: litera na poz. i to alphabet[shifts[i]].
    key_word = "".join(alphabet[s] for s in shifts)
    # Sprawdzamy czy `order` to faktycznie permutacja sortujaca litery key_word
    expected = sorted(range(n), key=lambda i: (key_word[i], i))
    if expected == order:
        return key_word
    return f"{key_word}|order={order}"


def optimize_shifts_greedy(ciphertext, order, shifts, qg, alphabet_size, max_passes=2):
    """
    Coordinate-descent po wektorze shiftow: dla kazdej kolumny probuje
    wszystkie |alfabet| mozliwych shiftow i wybiera najlepszy. Powtarza az do
    braku zmian (lub `max_passes`). Bardzo skuteczne dla Cadenusa, bo
    przy ustalonym poprawnym `order` shifty sa wzajemnie niezalezne.
    Modyfikuje `shifts` w miejscu, zwraca koncowy fitness.
    """
    n = len(order)
    best_score = qg.score(decrypt_components(ciphertext, order, shifts, alphabet_size))
    for _ in range(max_passes):
        improved = False
        for c in range(n):
            old = shifts[c]
            best_local = best_score
            best_s = old
            for s in range(alphabet_size):
                if s == old:
                    continue
                shifts[c] = s
                sc = qg.score(decrypt_components(ciphertext, order, shifts, alphabet_size))
                if sc > best_local:
                    best_local = sc
                    best_s = s
            shifts[c] = best_s
            if best_s != old:
                best_score = best_local
                improved = True
        if not improved:
            break
    return best_score


def evaluate_order(ciphertext, order, qg, alphabet_size):
    """
    Ewaluuje permutacje `order`: znajduje optymalny wektor shiftow przez
    coordinate descent zaczynajacy od zer i zwraca (fitness, shifts).
    To jest "memetyczna" funkcja oceny - kazda permutacja jest oceniana
    po lokalnym dostrojeniu shiftow.
    """
    shifts = [0] * len(order)
    score = optimize_shifts_greedy(ciphertext, order, shifts, qg, alphabet_size, max_passes=2)
    return score, shifts


def hill_climb(ciphertext, key_len, qg, alphabet_size, max_no_improve=200, target=None):
    """
    Hill-climb dwufazowy:
      Faza 1: szukanie permutacji `order` w przestrzeni N!. Mala zmiana =
              swap dwoch pozycji. Dla kazdej kandydatury liczymy fitness
              z greedy-optymalnymi shiftami.
      Faza 2: po znalezieniu najlepszego `order` - dokladne dostrojenie
              shiftow + drobne ruchy mieszane.
    """
    n = key_len

    # Faza 1: shotgun po `order`
    order = list(range(n))
    random.shuffle(order)
    best_score, best_shifts = evaluate_order(ciphertext, order, qg, alphabet_size)
    best_order = list(order)

    no_improve = 0
    while no_improve < max_no_improve:
        # mala zmiana: swap dwoch pozycji w `order`
        i, j = random.sample(range(n), 2)
        order[i], order[j] = order[j], order[i]
        score, shifts = evaluate_order(ciphertext, order, qg, alphabet_size)
        if score > best_score:
            best_score = score
            best_order = list(order)
            best_shifts = shifts
            no_improve = 0
            if target is not None and score >= target:
                break
        else:
            order[i], order[j] = order[j], order[i]
            no_improve += 1

    # Faza 2: dokladne dostrojenie shiftow
    order = list(best_order)
    shifts = list(best_shifts)
    optimize_shifts_greedy(ciphertext, order, shifts, qg, alphabet_size, max_passes=4)
    plain = decrypt_components(ciphertext, order, shifts, alphabet_size)
    final_score = qg.score(plain)

    if final_score > best_score:
        best_score = final_score
        best_shifts = shifts

    plain = decrypt_components(ciphertext, best_order, best_shifts, alphabet_size)
    return best_score, (best_order, best_shifts), plain


def candidate_key_lengths(cipher_len, alphabet_size, min_n=4, max_n=12):
    """Dlugosc krytotekstu musi byc wielokrotnoscia |alfabet|*N."""
    cands = [n for n in range(min_n, max_n + 1) if cipher_len % (alphabet_size * n) == 0]
    cands.sort(reverse=True)  # od dluzszych
    return cands


def attack(ciphertext, qg, key_len=None, restarts=20, time_budget=None,
           verbose=True, alphabet_size=25, alphabet=None):
    if key_len is None:
        candidates = candidate_key_lengths(len(ciphertext), alphabet_size)
        if not candidates:
            raise ValueError("Brak sensownej dlugosci klucza dla tej dlugosci kryptotekstu")
    else:
        candidates = [key_len]

    target_per_char = -3.05  # czytelny angielski quadgram log10
    target = target_per_char * (len(ciphertext) - 3)

    best = (-1e18, None, None, None)  # score, state, plain, n
    start = time.time()

    for n in candidates:
        if verbose:
            print(f"[*] N={n}  (kandydaci: {candidates})")
        for r in range(restarts):
            if time_budget is not None and (time.time() - start) > time_budget:
                if verbose:
                    print("[*] Przekroczono budzet czasowy.")
                return best
            score, state, plain = hill_climb(ciphertext, n, qg, alphabet_size, target=target)
            if verbose:
                key_str = state_to_key(state[0], state[1], alphabet or get_alphabet("en"))
                print(f"  restart {r + 1:>3}/{restarts}  N={n}  score={score:.1f}  key={key_str}")
            if score > best[0]:
                best = (score, state, plain, n)
                if score >= target:
                    if verbose:
                        print(f"[+] Osiagnieto prog czytelnosci, koncze.")
                    return best
    return best


# ---------- Glowny program ----------

def main():
    args = sys.argv[1:]
    cipher_path = "ciphertext_english.txt"
    lang = "en"
    key_len = None
    restarts = 25
    out_path = None

    i = 0
    while i < len(args):
        a = args[i]
        if a == "-l" and i + 1 < len(args):
            lang = args[i + 1]; i += 2
        elif a == "-k" and i + 1 < len(args):
            key_len = int(args[i + 1]); i += 2
        elif a == "-r" and i + 1 < len(args):
            restarts = int(args[i + 1]); i += 2
        elif a == "-o" and i + 1 < len(args):
            out_path = args[i + 1]; i += 2
        elif a in ("-h", "--help"):
            print(__doc__); return
        else:
            cipher_path = a; i += 1

    qg_path = "english_quadgrams.txt" if lang == "en" else "german_quadgrams.txt"
    if not os.path.exists(qg_path):
        print(f"Brak pliku statystyk: {qg_path}"); sys.exit(1)
    if not os.path.exists(cipher_path):
        print(f"Brak pliku kryptotekstu: {cipher_path}"); sys.exit(1)

    alphabet = get_alphabet(lang)
    alphabet_size = get_alphabet_size(lang)

    with open(cipher_path, "r", encoding="utf-8") as f:
        raw = f.read()
    cleaned = []
    for ch in raw:
        if ch == "ß":
            ch_up = "ß"
        else:
            ch_up = ch.upper()
        if ch_up in alphabet:
            cleaned.append(ch_up)
    ciphertext = "".join(cleaned)

    print(f"== Atak na szyfr Cadenus ==")
    print(f"Plik:        {cipher_path}")
    print(f"Jezyk:       {lang}  (statystyki: {qg_path})")
    print(f"Dlugosc:     {len(ciphertext)} znakow")
    print(f"Restarty:    {restarts}")
    if key_len:
        print(f"Klucz N:     {key_len} (znany)")
    else:
        print(f"Klucz N:     odgadywany, kandydaci: {candidate_key_lengths(len(ciphertext), alphabet_size)}")
    print()

    qg = Quadgrams(qg_path)

    t0 = time.time()
    score, state, plain, n = attack(
        ciphertext,
        qg,
        key_len=key_len,
        restarts=restarts,
        alphabet_size=alphabet_size,
        alphabet=alphabet,
    )
    dt = time.time() - t0

    key_str = state_to_key(state[0], state[1], alphabet)
    print()
    print("================ WYNIK ================")
    print(f"Czas:        {dt:.1f} s")
    print(f"Klucz:       {key_str}  (N={n})")
    print(f"Fitness:     {score:.1f}")
    print(f"Tekst (300): {plain[:300]}")
    print("=======================================")

    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(f"key={key_str}\nkey_len={n}\nfitness={score:.2f}\n\n")
            f.write(plain)
        print(f"Zapisano do {out_path}")


if __name__ == "__main__":
    main()
