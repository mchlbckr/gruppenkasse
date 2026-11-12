"""Gruppenkasse — die Seiten der Anwendung.

Stand Sitzung 4: Die Daten liegen jetzt in einer SQLite-Datenbank. Es gibt
beliebig viele Kassen, jede erreichbar über ihren eigenen Link.
"""

from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import datenbank, wechselkurse
from app.regeln import berechne_ausgleich, berechne_salden

HIER = Path(__file__).parent

app = FastAPI(title="Gruppenkasse")
app.mount("/static", StaticFiles(directory=HIER / "static"), name="static")
templates = Jinja2Templates(directory=HIER / "templates")


def euro(cent):
    """Formatiert Cent als deutschen Geldbetrag: 123456 -> "1.234,56 €"."""
    vorzeichen = "−" if cent < 0 else ""
    ganze, rest = divmod(abs(int(cent)), 100)
    mit_punkten = f"{ganze:,}".replace(",", ".")
    return f"{vorzeichen}{mit_punkten},{rest:02d} €"


templates.env.filters["euro"] = euro


@app.on_event("startup")
def beim_start():
    datenbank.initialisiere()


# --- Startseite: eine Kasse anlegen ------------------------------------------

@app.get("/")
def startseite(request: Request):
    return templates.TemplateResponse("start.html", {"request": request})


@app.post("/kasse")
def kasse_anlegen(name: str = Form(...), personen: str = Form(...)):
    # Die Namen kommen als eine Zeile: "Lena, Tim, Jonas"
    namen = [teil.strip() for teil in personen.split(",") if teil.strip()]
    if len(namen) < 2:
        raise HTTPException(status_code=400, detail="Mindestens zwei Personen")

    token = datenbank.lege_kasse_an(name, namen)
    return RedirectResponse(f"/k/{token}", status_code=303)


# --- Die Kasse selbst --------------------------------------------------------

@app.get("/k/{token}")
def kasse_anzeigen(request: Request, token: str):
    kasse = datenbank.hole_kasse(token)
    if kasse is None:
        raise HTTPException(status_code=404, detail="Diese Kasse gibt es nicht")

    personen = datenbank.hole_personen(kasse["id"])
    ausgaben = datenbank.hole_ausgaben(kasse["id"])

    # Für die Anzeige brauchen wir zu jeder Person-ID den Namen.
    namen = {person["id"]: person["name"] for person in personen}

    salden = berechne_salden([person["id"] for person in personen], ausgaben)
    ausgleich = berechne_ausgleich(salden)

    return templates.TemplateResponse(
        "kasse.html",
        {
            "request": request,
            "kasse": kasse,
            "personen": personen,
            "namen": namen,
            "ausgaben": ausgaben,
            "salden": salden,
            "ausgleich": ausgleich,
        },
    )


@app.post("/k/{token}/ausgabe")
async def ausgabe_hinzufuegen(request: Request, token: str):
    kasse = datenbank.hole_kasse(token)
    if kasse is None:
        raise HTTPException(status_code=404, detail="Diese Kasse gibt es nicht")

    formular = await request.form()

    titel = formular["titel"]
    bezahlt_von = int(formular["bezahlt_von"])

    # Der Betrag kommt als Text, etwa "12,50". Intern rechnen wir in Cent.
    betrag = str(formular["betrag"]).replace(",", ".")
    eingegebene_cent = round(float(betrag) * 100)

    waehrung = str(formular.get("waehrung", kasse["waehrung"])).upper()

    # In der Währung der Kasse? Dann ist nichts umzurechnen.
    if waehrung == kasse["waehrung"]:
        cent = eingegebene_cent
        original_waehrung = None
        original_cent = None
        kurs = None
    else:
        try:
            kurs = wechselkurse.hole_kurs(waehrung, kasse["waehrung"])
        except wechselkurse.KursNichtVerfuegbar as fehler:
            # Wichtig: Der Fehler des fremden Dienstes darf unsere Anwendung
            # nicht abstürzen lassen. Die Person soll erfahren, was los ist.
            raise HTTPException(status_code=502, detail=str(fehler))

        cent = round(eingegebene_cent * kurs)
        original_waehrung = waehrung
        original_cent = eingegebene_cent

    # Angehakte Personen. Ist niemand angehakt, sind alle beteiligt.
    beteiligte = [int(wert) for wert in formular.getlist("beteiligte")]
    if not beteiligte:
        beteiligte = [person["id"] for person in datenbank.hole_personen(kasse["id"])]

    datenbank.lege_ausgabe_an(
        kasse["id"],
        titel,
        cent,
        bezahlt_von,
        beteiligte,
        original_waehrung=original_waehrung,
        original_cent=original_cent,
        kurs=kurs,
    )
    return RedirectResponse(f"/k/{token}", status_code=303)


# --- Die eigene Schnittstelle ------------------------------------------------
# Dieselben Daten, aber als JSON statt als Seite. Damit kann ein anderes
# Programm die Kasse auslesen. Die Dokumentation dazu erzeugt FastAPI selbst,
# zu sehen unter /docs.

@app.get("/api/k/{token}", tags=["Kasse"])
def kasse_als_json(token: str):
    """Gibt eine Kasse mit Personen, Ausgaben und Salden zurück."""
    kasse = datenbank.hole_kasse(token)
    if kasse is None:
        raise HTTPException(status_code=404, detail="Diese Kasse gibt es nicht")

    personen = datenbank.hole_personen(kasse["id"])
    ausgaben = datenbank.hole_ausgaben(kasse["id"])
    salden = berechne_salden([person["id"] for person in personen], ausgaben)

    return {
        "name": kasse["name"],
        "waehrung": kasse["waehrung"],
        "personen": [
            {
                "id": person["id"],
                "name": person["name"],
                "saldo_cent": salden[person["id"]],
            }
            for person in personen
        ],
        "ausgaben": ausgaben,
    }


@app.get("/api/kurs", tags=["Kurse"])
def kurs_abfragen(von: str, nach: str):
    """Aktueller Umrechnungskurs zwischen zwei Währungen."""
    try:
        return {"von": von.upper(), "nach": nach.upper(), "kurs": wechselkurse.hole_kurs(von, nach)}
    except wechselkurse.KursNichtVerfuegbar as fehler:
        raise HTTPException(status_code=502, detail=str(fehler))
