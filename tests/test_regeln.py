"""Tests für die fachlichen Regeln.

Diese Tests sind in Sitzung 6 entstanden, und zwar in dieser Reihenfolge:
erst die Fälle aufschreiben, die uns eingefallen sind — dann nachsehen, was
der Agent gebaut hat. Drei dieser Fälle sind beim ersten Versuch
durchgefallen.

Aufrufen mit:  pytest
"""

from app.regeln import berechne_ausgleich, berechne_salden, teile_auf


# --- teile_auf ---------------------------------------------------------------

def test_glatt_teilbarer_betrag():
    assert teile_auf(8640, 5) == [1728, 1728, 1728, 1728, 1728]


def test_krummer_betrag_die_ersten_bekommen_den_cent():
    # 10,00 € auf drei Personen: 3,34 + 3,33 + 3,33
    assert teile_auf(1000, 3) == [334, 333, 333]


def test_die_summe_der_anteile_ergibt_immer_den_betrag():
    # Das ist die eigentliche Zusicherung. Wenn sie bricht, verschwinden Cent.
    for betrag in range(0, 500):
        for anzahl in range(1, 9):
            assert sum(teile_auf(betrag, anzahl)) == betrag


def test_betrag_null():
    assert teile_auf(0, 3) == [0, 0, 0]


def test_ohne_beteiligte_gibt_es_einen_fehler():
    import pytest

    with pytest.raises(ValueError):
        teile_auf(1000, 0)


# --- berechne_salden ---------------------------------------------------------

def ausgabe(cent, bezahlt_von, beteiligte):
    return {"cent": cent, "bezahlt_von": bezahlt_von, "beteiligte": beteiligte}


def test_einfacher_fall():
    salden = berechne_salden([1, 2], [ausgabe(1000, 1, [1, 2])])
    assert salden == {1: 500, 2: -500}


def test_teilbeteiligung_wer_nicht_dabei_war_zahlt_nicht():
    # Drei Personen, aber nur zwei waren beim Kino.
    salden = berechne_salden([1, 2, 3], [ausgabe(1000, 1, [1, 2])])
    assert salden[3] == 0


def test_wer_nie_bezahlt_hat_steht_im_minus():
    salden = berechne_salden([1, 2, 3], [ausgabe(3000, 1, [1, 2, 3])])
    assert salden[2] == -1000
    assert salden[3] == -1000


def test_die_summe_aller_salden_ist_null():
    ausgaben = [
        ausgabe(8640, 1, [1, 2, 3, 4, 5]),
        ausgabe(3600, 4, [4, 1, 5]),
        ausgabe(1000, 3, [1, 2]),
        ausgabe(777, 2, [2, 3, 4]),
    ]
    salden = berechne_salden([1, 2, 3, 4, 5], ausgaben)
    assert sum(salden.values()) == 0


# --- berechne_ausgleich ------------------------------------------------------

def wende_an(salden, ueberweisungen):
    """Führt die vorgeschlagenen Überweisungen aus und gibt die neuen Salden."""
    neu = dict(salden)
    for von, nach, betrag in ueberweisungen:
        neu[von] += betrag
        neu[nach] -= betrag
    return neu


def test_ausgleich_bringt_alle_auf_null():
    salden = {1: -2928, 2: 6912, 3: -1728, 4: 672, 5: -2928}
    ergebnis = wende_an(salden, berechne_ausgleich(salden))
    assert all(saldo == 0 for saldo in ergebnis.values())


def test_ausgleich_bei_krummen_betraegen():
    salden = berechne_salden([1, 2, 3], [ausgabe(1000, 1, [1, 2, 3])])
    ergebnis = wende_an(salden, berechne_ausgleich(salden))
    assert all(saldo == 0 for saldo in ergebnis.values())


def test_ausgleich_niemand_schuldet_etwas():
    assert berechne_ausgleich({1: 0, 2: 0}) == []


def test_ausgleich_ueberweist_nie_an_sich_selbst():
    salden = {1: -1000, 2: 1000, 3: 0}
    for von, nach, _betrag in berechne_ausgleich(salden):
        assert von != nach


def test_ausgleich_ueberweist_keine_negativen_betraege():
    salden = {1: -4500, 2: 1500, 3: 1500, 4: 1500}
    for _von, _nach, betrag in berechne_ausgleich(salden):
        assert betrag > 0
