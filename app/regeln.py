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


def berechne_ausgleich(salden):
    """Schlägt Überweisungen vor, die alle Salden auf null bringen.

    Regel: Wer am meisten schuldet, überweist an die Person, die am meisten
    bekommt — und zwar den kleineren der beiden Beträge. Das wiederholt sich,
    bis niemand mehr etwas schuldet.

    Das Ergebnis ist nicht immer die kleinstmögliche Anzahl Überweisungen,
    aber immer eine kleine. Dafür lässt es sich in zwei Sätzen erklären, und
    genau das ist hier wichtiger.

    Gibt eine Liste von (von_person, an_person, cent) zurück.
    """
    # Kopien, damit die übergebenen Salden unverändert bleiben.
    schuldner = sorted(
        [(person, -saldo) for person, saldo in salden.items() if saldo < 0],
        key=lambda eintrag: eintrag[1],
        reverse=True,
    )
    glaeubiger = sorted(
        [(person, saldo) for person, saldo in salden.items() if saldo > 0],
        key=lambda eintrag: eintrag[1],
        reverse=True,
    )

    ueberweisungen = []

    while schuldner and glaeubiger:
        schuldner_person, schuld = schuldner.pop(0)
        glaeubiger_person, guthaben = glaeubiger.pop(0)

        betrag = min(schuld, guthaben)
        ueberweisungen.append((schuldner_person, glaeubiger_person, betrag))

        # Was übrig bleibt, kommt zurück in die Liste — an die richtige Stelle.
        if schuld > betrag:
            schuldner.append((schuldner_person, schuld - betrag))
            schuldner.sort(key=lambda eintrag: eintrag[1], reverse=True)
        if guthaben > betrag:
            glaeubiger.append((glaeubiger_person, guthaben - betrag))
            glaeubiger.sort(key=lambda eintrag: eintrag[1], reverse=True)

    return ueberweisungen
