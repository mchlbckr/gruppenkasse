"""Wechselkurse von einer fremden Schnittstelle holen.

Das ist die erste fremde API im Projekt. Daran lässt sich alles zeigen, was
beim Anbinden fremder Dienste wichtig ist: Dokumentation lesen, Schlüssel
sicher aufbewahren, mit Fehlern rechnen, nicht bei jedem Aufruf neu fragen.

Es gibt zwei Wege:

1. Mit Schlüssel über exchangerate-api.com. Der Schlüssel steht in der
   Umgebungsvariablen EXCHANGE_API_KEY — niemals im Code.
2. Ohne Schlüssel über frankfurter.dev (Kurse der EZB). Das ist die
   Rückfallvariante, damit die Anwendung auch ohne Zugang funktioniert.
"""

import os
from datetime import date

import httpx
from dotenv import load_dotenv

load_dotenv()

SCHLUESSEL = os.getenv("EXCHANGE_API_KEY", "").strip()

# Einmal geholte Kurse merken wir uns für den Tag. Sonst fragen wir bei jedem
# Formular neu an und laufen in das Anfragelimit des Anbieters.
_gemerkte_kurse = {}


class KursNichtVerfuegbar(Exception):
    """Der Kurs konnte nicht geholt werden — mit einem Grund im Klartext."""


def hole_kurs(von_waehrung, nach_waehrung):
    """Wie viel ist eine Einheit von_waehrung in nach_waehrung wert?

    Gibt eine Kommazahl zurück. Diese Zahl wird beim Erfassen der Ausgabe
    gespeichert, damit spätere Kursänderungen alte Ausgaben nicht verändern.
    """
    von_waehrung = von_waehrung.upper()
    nach_waehrung = nach_waehrung.upper()

    if von_waehrung == nach_waehrung:
        return 1.0

    merkmal = (von_waehrung, nach_waehrung, date.today())
    if merkmal in _gemerkte_kurse:
        return _gemerkte_kurse[merkmal]

    if SCHLUESSEL:
        kurs = _hole_mit_schluessel(von_waehrung, nach_waehrung)
    else:
        kurs = _hole_ohne_schluessel(von_waehrung, nach_waehrung)

    _gemerkte_kurse[merkmal] = kurs
    return kurs


def _hole_mit_schluessel(von_waehrung, nach_waehrung):
    adresse = (
        f"https://v6.exchangerate-api.com/v6/{SCHLUESSEL}"
        f"/pair/{von_waehrung}/{nach_waehrung}"
    )
    daten = _frage_an(adresse)

    if daten.get("result") != "success":
        # Typische Fälle: Schlüssel abgelaufen, Schlüssel falsch, Währung
        # unbekannt. Der Anbieter schreibt den Grund in die Antwort.
        raise KursNichtVerfuegbar(
            f"Der Kursdienst meldet: {daten.get('error-type', 'unbekannter Fehler')}"
        )

    return float(daten["conversion_rate"])


def _hole_ohne_schluessel(von_waehrung, nach_waehrung):
    adresse = (
        f"https://api.frankfurter.dev/v1/latest"
        f"?base={von_waehrung}&symbols={nach_waehrung}"
    )
    daten = _frage_an(adresse)

    kurse = daten.get("rates", {})
    if nach_waehrung not in kurse:
        raise KursNichtVerfuegbar(
            f"Für {von_waehrung} nach {nach_waehrung} gibt es keinen Kurs"
        )

    return float(kurse[nach_waehrung])


def _frage_an(adresse):
    """Eine Anfrage stellen und die Antwort als Daten zurückgeben.

    Hier passieren die Dinge, an die man beim ersten Mal nicht denkt:
    Der Dienst kann langsam sein, nicht erreichbar sein, oder mit einem
    Fehlercode antworten. Alles drei darf die eigene Anwendung nicht umbringen.
    """
    try:
        antwort = httpx.get(adresse, timeout=5.0)
    except httpx.RequestError as fehler:
        raise KursNichtVerfuegbar(f"Der Kursdienst ist nicht erreichbar: {fehler}")

    if antwort.status_code == 401 or antwort.status_code == 403:
        raise KursNichtVerfuegbar(
            "Der Schlüssel wird nicht akzeptiert (Status "
            f"{antwort.status_code}). Steht EXCHANGE_API_KEY in der .env?"
        )

    if antwort.status_code == 429:
        raise KursNichtVerfuegbar("Zu viele Anfragen — das Limit ist erreicht")

    if antwort.status_code != 200:
        raise KursNichtVerfuegbar(f"Unerwartete Antwort: Status {antwort.status_code}")

    return antwort.json()
