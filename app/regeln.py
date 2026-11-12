"""Die fachlichen Regeln der Gruppenkasse.

Hier steht, was die Anwendung inhaltlich tut. Absichtlich getrennt von der
Datenbank und von den Seiten: Diese Funktionen kennen weder HTTP noch SQL,
nur Zahlen und Listen. Deshalb kann man sie auch leicht testen.

Alle Beträge sind ganze Zahlen in Cent. Niemals Kommazahlen — sonst fehlen
am Ende Cent, und niemand findet heraus, warum.
"""


def teile_auf(cent, anzahl_beteiligte):
    """Teilt einen Betrag gleichmäßig auf mehrere Personen auf.

    Regel: Geht der Betrag nicht glatt auf, bekommen die ersten Beteiligten
    je einen Cent mehr. Die Summe der Anteile ergibt immer genau den Betrag.

    Beispiel: 8640 Cent auf 5 Personen -> [1728, 1728, 1728, 1728, 1728]
              1000 Cent auf 3 Personen -> [334, 333, 333]
    """
    if anzahl_beteiligte <= 0:
        raise ValueError("Eine Ausgabe braucht mindestens eine beteiligte Person")

    grundanteil = cent // anzahl_beteiligte
    rest = cent - grundanteil * anzahl_beteiligte

    anteile = []
    for position in range(anzahl_beteiligte):
        if position < rest:
            anteile.append(grundanteil + 1)
        else:
            anteile.append(grundanteil)
    return anteile


def berechne_salden(personen_ids, ausgaben):
    """Saldo je Person: was sie bezahlt hat, minus die Summe ihrer Anteile.

    Ein positiver Saldo bedeutet: Diese Person hat mehr ausgelegt, als sie
    verbraucht hat, und bekommt Geld zurück. Die Summe aller Salden ist
    immer null.
    """
    salden = {}
    for person_id in personen_ids:
        salden[person_id] = 0

    for ausgabe in ausgaben:
        salden[ausgabe["bezahlt_von"]] += ausgabe["cent"]

        anteile = teile_auf(ausgabe["cent"], len(ausgabe["beteiligte"]))
        for position, person_id in enumerate(ausgabe["beteiligte"]):
            salden[person_id] -= anteile[position]

    return salden
