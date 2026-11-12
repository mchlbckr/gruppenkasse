"""Gruppenkasse — erste lauffähige Version.

Stand Sitzung 3: Alles liegt noch im Arbeitsspeicher. Wird die Anwendung neu
gestartet, sind die Ausgaben weg. Das ist Absicht — die Datenbank kommt in
Sitzung 4.
"""

from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Gruppenkasse")
templates = Jinja2Templates(directory="app/templates")

# --- Die Daten der Kasse -----------------------------------------------------
# Noch fest eingetragen. Eine Kasse, feste Teilnehmende.

KASSENNAME = "WG Hansaring"
PERSONEN = ["Lena", "Tim", "Jonas", "Mira", "Ben"]

# Jede Ausgabe ist ein Dictionary. Die Liste wächst, während die Anwendung läuft.
ausgaben = [
    {"titel": "Großeinkauf", "cent": 8640, "bezahlt_von": "Tim", "beteiligte": PERSONEN},
    {"titel": "Kino", "cent": 3600, "bezahlt_von": "Mira", "beteiligte": ["Mira", "Lena", "Ben"]},
]


# --- Die fachlichen Regeln ---------------------------------------------------

def teile_auf(cent, anzahl_beteiligte):
    """Teilt einen Betrag gleichmäßig auf.

    Regel: Geht der Betrag nicht glatt auf, bekommen die ersten Beteiligten
    den zusätzlichen Cent. Die Summe der Anteile ergibt immer genau den Betrag.
    """
    grundanteil = cent // anzahl_beteiligte
    rest = cent - grundanteil * anzahl_beteiligte

    anteile = []
    for position in range(anzahl_beteiligte):
        if position < rest:
            anteile.append(grundanteil + 1)
        else:
            anteile.append(grundanteil)
    return anteile


def berechne_salden(personen, alle_ausgaben):
    """Saldo je Person: was sie bezahlt hat, minus ihre Anteile.

    Ein positiver Saldo heißt: Diese Person hat mehr ausgelegt, als sie
    verbraucht hat, bekommt also Geld zurück.
    """
    salden = {}
    for person in personen:
        salden[person] = 0

    for ausgabe in alle_ausgaben:
        salden[ausgabe["bezahlt_von"]] += ausgabe["cent"]

        anteile = teile_auf(ausgabe["cent"], len(ausgabe["beteiligte"]))
        for position, person in enumerate(ausgabe["beteiligte"]):
            salden[person] -= anteile[position]

    return salden


# --- Die Seiten --------------------------------------------------------------

@app.get("/")
def kasse_anzeigen(request: Request):
    return templates.TemplateResponse(
        "kasse.html",
        {
            "request": request,
            "kassenname": KASSENNAME,
            "personen": PERSONEN,
            "ausgaben": ausgaben,
            "salden": berechne_salden(PERSONEN, ausgaben),
        },
    )


@app.post("/ausgabe")
def ausgabe_hinzufuegen(
    titel: str = Form(...),
    betrag: str = Form(...),
    bezahlt_von: str = Form(...),
):
    # Der Betrag kommt als Text aus dem Formular, etwa "12,50".
    # Intern rechnen wir in ganzen Cent — niemals mit Kommazahlen.
    betrag = betrag.replace(",", ".")
    cent = round(float(betrag) * 100)

    ausgaben.append(
        {
            "titel": titel,
            "cent": cent,
            "bezahlt_von": bezahlt_von,
            "beteiligte": PERSONEN,
        }
    )
    return RedirectResponse("/", status_code=303)
