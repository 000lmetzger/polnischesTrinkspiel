import argparse
import csv
import random
import statistics
from dataclasses import dataclass, field

ZIEL = 71
ANZAHL_SPIELER = 8

MERKMALE = [
    "maedel",
    "bruder",
    "schwester",
    "gerades_alter",
    "unter_21",
    "acht_im_geburtsjahr",
    "brille_oder_linsen",
    "jeans",
    "hat_10_euro",
]

KENNZAHLEN = ["schluecke", "kleidung", "kuesse", "gesungen",
              "zuege", "zurueck_auf_start", "ausgesetzt"]
SPALTEN = KENNZAHLEN + ["schl_runde"]


@dataclass
class Spieler:
    platz: int
    merkmale: dict
    pos: int = 0
    aussetzen: bool = False
    gewonnen: bool = False
    schluecke: int = 0
    kleidung: int = 0
    kuesse: int = 0
    gesungen: int = 0
    zuege: int = 0
    zurueck_auf_start: int = 0
    ausgesetzt: int = 0


class Partie:
    def __init__(self, rng):
        self.rng = rng
        self.spieler = [
            Spieler(i, {m: rng.random() < 0.5 for m in MERKMALE})
            for i in range(ANZAHL_SPIELER)
        ]
        self.vorbei = False
        self.runden = 0
        self.letzter_wurf = 0

    def w(self):
        return self.rng.randint(1, 6)

    def trink(self, s, n=1):
        s.schluecke += n

    def andere(self, s):
        return [p for p in self.spieler if p is not s]

    def zufaellig_anderer(self, s):
        return self.rng.choice(self.andere(s))

    def rechts(self, s):
        return self.spieler[(s.platz + 1) % ANZAHL_SPIELER]

    def links(self, s):
        return self.spieler[(s.platz - 1) % ANZAHL_SPIELER]

    def versetzen(self, s, pos):
        pos = max(pos, 0)
        if pos == 0 and s.pos != 0:
            s.zurueck_auf_start += 1
        s.pos = pos

    def kuss(self, a, b):
        a.kuesse += 1
        b.kuesse += 1

    def spielen(self):
        while not self.vorbei:
            self.runden += 1
            for s in self.spieler:
                if s.aussetzen:
                    s.aussetzen = False
                    s.ausgesetzt += 1
                    continue
                self.zug(s)
                if self.vorbei:
                    break

    def zug(self, s):
        nochmal = True
        while nochmal and not self.vorbei:
            s.zuege += 1
            self.letzter_wurf = self.w()
            nochmal = self.landen(s, s.pos + self.letzter_wurf)

    def landen(self, s, pos):
        if pos > ZIEL:
            pos = 2 * ZIEL - pos
        pos = max(pos, 0)
        if pos == 0 and s.pos != 0:
            s.zurueck_auf_start += 1
        s.pos = pos
        if pos == ZIEL:
            s.gewonnen = True
            self.vorbei = True
            return False
        aktion = FELDER.get(pos)
        return bool(aktion(self, s)) if aktion else False


def alle_trinken(P, s, n=1):
    for p in P.spieler:
        P.trink(p, n)


def merkmal_trinkt(name, wert=True, n=1):
    def f(P, s):
        for p in P.spieler:
            if p.merkmale[name] == wert:
                P.trink(p, n)
    return f


def alle_wuerfeln_trinken(augen):
    def f(P, s):
        for p in P.spieler:
            if P.w() == augen:
                P.trink(p)
    return f


def alle_singen(P, s):
    for p in P.spieler:
        p.gesungen += 1


def f2(P, s):
    P.trink(s); P.trink(P.links(s)); P.trink(P.rechts(s))


def f3(P, s):
    return P.landen(s, s.pos - 2)


def f5(P, s):
    P.trink(s); return P.landen(s, 32)


def f6(P, s):
    P.trink(s)


def f7(P, s):
    for p in P.andere(s):
        P.trink(p)


def f9(P, s):
    P.trink(P.zufaellig_anderer(s))


def f11(P, s):
    P.trink(P.rechts(s))


def f12(P, s):
    P.trink(P.zufaellig_anderer(s), 2)


def f13(P, s):
    P.trink(s, P.w()); return P.landen(s, 0)


def f14(P, s):
    positionen = [p.pos for p in P.spieler]
    lo, hi = min(positionen), max(positionen)
    for p in P.spieler:
        if p.pos in (lo, hi):
            P.trink(p)


def f15(P, s):
    maedels = [p for p in P.andere(s) if p.merkmale["maedel"]]
    if maedels:
        P.trink(P.rng.choice(maedels))


def f16(P, s):
    P.trink(s); P.trink(P.zufaellig_anderer(s), 2)


def f17(P, s):
    P.trink(s); s.aussetzen = True


def f20(P, s):
    P.trink(s); return True


def f21(P, s):
    return P.landen(s, 0)


def f22(P, s):
    P.trink(s, P.letzter_wurf)


def f24(P, s):
    if P.rng.random() < 0.5:
        P.trink(s, 3)
    else:
        return P.landen(s, s.pos - 4)


def f29(P, s):
    P.trink(s, 5); return P.landen(s, 9)


def f30(P, s):
    for p in P.spieler:
        if not p.merkmale["hat_10_euro"]:
            P.trink(p)


def f31(P, s):
    if P.w() % 2 == 0:
        P.trink(s)
    else:
        for p in P.andere(s):
            P.trink(p)


def f32(P, s):
    P.trink(s, 3)
    anderes = [p for p in P.andere(s) if p.merkmale["maedel"] != s.merkmale["maedel"]]
    P.kuss(s, P.rng.choice(anderes) if anderes else P.zufaellig_anderer(s))


def ausziehen(P, s):
    P.trink(s); s.kleidung += 1


def f34(P, s):
    P.trink(s); P.versetzen(P.zufaellig_anderer(s), 6)


def f35(P, s):
    return P.landen(s, 6)


def f36(P, s):
    lo = min(p.pos for p in P.spieler)
    for p in P.spieler:
        if p.pos == lo:
            P.trink(p)
    if lo < s.pos:
        return P.landen(s, lo)


def f37(P, s):
    for p in P.spieler:
        if p.pos > s.pos:
            P.trink(p)


def f40(P, s):
    P.trink(s, P.w())


def f41(P, s):
    P.trink(P.rng.choice(P.spieler))


def f44(P, s):
    P.trink(s)
    linker = P.links(s)
    P.trink(P.rng.choice([p for p in P.spieler if p is not linker]))


def f45(P, s):
    P.trink(s); return P.landen(s, s.pos + 2)


def f46(P, s):
    if P.rng.random() < 0.5:
        alle_trinken(P, s)
    else:
        P.trink(s)


def f47(P, s):
    P.trink(s, 2); P.kuss(s, P.zufaellig_anderer(s))


def f49(P, s):
    P.landen(s, 28); return True


def f51(P, s):
    a, b = P.rng.sample(P.andere(s), 2)
    P.kuss(a, b); P.trink(a, 3); P.trink(b, 3)


def f53(P, s):
    P.trink(P.links(s)); P.trink(P.rechts(s))


def f56(P, s):
    P.trink(s); return P.landen(s, 18)


def f59(P, s):
    for p in P.spieler:
        if P.w() == 1:
            P.trink(p); P.versetzen(p, 0)


def f62(P, s):
    return P.landen(s, s.pos - sum(P.w() for _ in range(3)))


def f65(P, s):
    for p in P.andere(s):
        P.versetzen(p, p.pos - 1)
    return P.landen(s, 64)


def f66(P, s):
    return P.landen(s, 32)


def f67(P, s):
    for p in P.spieler:
        P.trink(p, 3); p.kleidung += 1


def f69(P, s):
    return P.landen(s, s.pos - sum(P.w() for _ in range(5)))


def f70(P, s):
    P.trink(s); return P.landen(s, 0)


FELDER = {
    1: alle_trinken, 2: f2, 3: f3, 4: alle_singen, 5: f5, 6: f6, 7: f7,
    9: f9, 10: merkmal_trinkt("maedel", False), 11: f11, 12: f12, 13: f13,
    14: f14, 15: f15, 16: f16, 17: f17, 19: merkmal_trinkt("maedel"),
    20: f20, 21: f21, 22: f22, 23: merkmal_trinkt("bruder"), 24: f24,
    25: f6, 26: merkmal_trinkt("gerades_alter"),
    27: merkmal_trinkt("gerades_alter", False), 29: f29, 30: f30, 31: f31,
    32: f32, 33: ausziehen, 34: f34, 35: f35, 36: f36, 37: f37, 39: ausziehen,
    40: f40, 41: f41, 42: alle_wuerfeln_trinken(1),
    43: merkmal_trinkt("schwester"), 44: f44, 45: f45, 46: f46, 47: f47,
    49: f49, 50: ausziehen, 51: f51, 52: merkmal_trinkt("unter_21", n=2),
    53: f53, 54: alle_trinken, 55: alle_wuerfeln_trinken(6), 56: f56,
    57: merkmal_trinkt("acht_im_geburtsjahr"), 59: f59, 60: alle_singen,
    61: merkmal_trinkt("brille_oder_linsen", False), 62: f62,
    63: merkmal_trinkt("jeans"), 64: alle_trinken, 65: f65, 66: f66, 67: f67,
    69: f69, 70: f70,
}


def simulieren(n, seed=None, csv_pfad="ergebnisse_spieler.csv"):
    rng = random.Random(seed)
    zeilen = []
    for nr in range(1, n + 1):
        P = Partie(rng)
        P.spielen()
        for s in P.spieler:
            z = {"partie": nr, "runden": P.runden, "platz": s.platz,
                 "gewonnen": s.gewonnen}
            z.update(s.merkmale)
            z.update({k: getattr(s, k) for k in KENNZAHLEN})
            z["schl_runde"] = round(s.schluecke / P.runden, 4)
            zeilen.append(z)

    if csv_pfad:
        with open(csv_pfad, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(zeilen[0]), delimiter=";")
            w.writeheader()
            w.writerows(zeilen)
    return zeilen


def mittel(zeilen, k):
    return statistics.fmean(z[k] for z in zeilen) if zeilen else float("nan")


TABELLE = [
    ("zuege", "Züge gespielt"),
    ("schluecke", "Schlücke getrunken"),
    ("kleidung", "Kleidungsstücke ausgezogen"),
    ("kuesse", "Anzahl Küsse"),
    ("gesungen", "Anzahl gesungen"),
    ("zurueck_auf_start", "Zurück auf Start"),
]

MERKMAL_NAMEN = {
    "unter_21": ("Unter 21", "21 oder älter"),
    "schwester": ("Schwester", "Keine Schwester"),
    "bruder": ("Bruder", "Kein Bruder"),
    "acht_im_geburtsjahr": ("Acht im Geburtsjahr", "Keine Acht im Geburtsjahr"),
    "gerades_alter": ("Gerades Alter", "Ungerades Alter"),
    "maedel": ("Frau", "Mann"),
    "brille_oder_linsen": ("Brille oder Linsen", "Keine Brille oder Linsen"),
    "jeans": ("Jeans", "Keine Jeans"),
    "hat_10_euro": ("Hat 10€", "Hat keine 10€"),
}


def auswerten(zeilen):
    runden = [z["runden"] for z in zeilen if z["platz"] == 0]
    print("Partielänge (Runden, eine Runde = jeder Spieler einmal dran)")
    q = statistics.quantiles(runden, n=10) if len(runden) > 1 else [runden[0]] * 9
    print(f"  Ø {statistics.fmean(runden):.1f}   Median {statistics.median(runden):.0f}"
          f"   10%-Quantil {q[0]:.0f}   90%-Quantil {q[8]:.0f}   Min {min(runden)}   Max {max(runden)}")

    print("\nPro Spieler und Partie (alle Spieler)")
    print(f"  {'Kennzahl':<28}{'Ø':>10}{'Median':>10}{'Max':>10}")
    for k, name in TABELLE:
        werte = [z[k] for z in zeilen]
        print(f"  {name:<28}{statistics.fmean(werte):>10.2f}{statistics.median(werte):>10.1f}"
              f"{max(werte):>10}")

    print("\nDifferenz je Merkmal (Ø Spieler mit Merkmal minus Ø Spieler ohne Merkmal)")
    print(f"  {'Merkmal':<28}{'Schlücke':>10}")
    diffs = []
    for m in MERKMALE:
        name_ja, name_nein = MERKMAL_NAMEN[m]
        ja = mittel([z for z in zeilen if z[m]], "schluecke")
        nein = mittel([z for z in zeilen if not z[m]], "schluecke")
        diffs.append((name_ja, ja - nein))
        diffs.append((name_nein, nein - ja))
    for name, d in sorted(diffs, key=lambda x: x[1], reverse=True):
        print(f"  {name:<28}{d:>+10.2f}")


def main():
    ap = argparse.ArgumentParser(description="Komplettes Trinkspiel mit 8 Spielern simulieren")
    ap.add_argument("n", nargs="?", type=int, default=2000, help="Anzahl Partien (Standard 2000)")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--csv", default="ergebnisse_spieler.csv",
                    help="CSV-Datei für alle Spieler-Konten ('' = nicht speichern)")
    args = ap.parse_args()

    zeilen = simulieren(args.n, args.seed, args.csv)
    auswerten(zeilen)


if __name__ == "__main__":
    main()
