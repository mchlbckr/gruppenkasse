"""Zugriff auf die Datenbank.

Wir benutzen SQLite: Die ganze Datenbank ist eine einzige Datei neben der
Anwendung. Kein Server, keine Zugangsdaten, nichts zu installieren.
"""

import secrets
import sqlite3
from pathlib import Path

DATENBANK_DATEI = Path(__file__).parent.parent / "gruppenkasse.db"

# Das Datenmodell:
#
#   kassen  1 ──── n  personen
#      │
#      1
#      │
#      n
#   ausgaben  n ──── m  personen   (über die Tabelle beteiligungen)
#
# Die Verknüpfungstabelle "beteiligungen" ist nötig, weil an einer Ausgabe
# mehrere Personen beteiligt sein können und jede Person an mehreren Ausgaben.

SCHEMA = """
CREATE TABLE IF NOT EXISTS kassen (
    id        INTEGER PRIMARY KEY,
    token     TEXT NOT NULL UNIQUE,
    name      TEXT NOT NULL,
    waehrung  TEXT NOT NULL DEFAULT 'EUR'
);

CREATE TABLE IF NOT EXISTS personen (
    id       INTEGER PRIMARY KEY,
    kasse_id INTEGER NOT NULL REFERENCES kassen(id),
    name     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ausgaben (
    id                   INTEGER PRIMARY KEY,
    kasse_id             INTEGER NOT NULL REFERENCES kassen(id),
    titel                TEXT NOT NULL,
    cent                 INTEGER NOT NULL,
    bezahlt_von          INTEGER NOT NULL REFERENCES personen(id)
);

CREATE TABLE IF NOT EXISTS beteiligungen (
    ausgabe_id INTEGER NOT NULL REFERENCES ausgaben(id),
    person_id  INTEGER NOT NULL REFERENCES personen(id),
    PRIMARY KEY (ausgabe_id, person_id)
);
"""


def verbindung():
    """Öffnet eine Verbindung zur Datenbankdatei."""
    verbindung = sqlite3.connect(DATENBANK_DATEI)
    # Damit kommen Zeilen als etwas zurück, das sich wie ein Dictionary liest:
    # zeile["name"] statt zeile[2].
    verbindung.row_factory = sqlite3.Row
    verbindung.execute("PRAGMA foreign_keys = ON")
    return verbindung


def initialisiere():
    """Legt die Tabellen an, falls sie noch nicht existieren."""
    with verbindung() as db:
        db.executescript(SCHEMA)


# --- Kassen ------------------------------------------------------------------

def lege_kasse_an(name, namen_der_personen, waehrung="EUR"):
    """Legt eine Kasse mit ihren Teilnehmenden an und gibt das Token zurück.

    Das Token ist die halbe Adresse: Wer es kennt, kommt in die Kasse.
    Deshalb wird es zufällig erzeugt und nicht hochgezählt.
    """
    token = secrets.token_urlsafe(9)

    with verbindung() as db:
        zeiger = db.execute(
            "INSERT INTO kassen (token, name, waehrung) VALUES (?, ?, ?)",
            (token, name, waehrung),
        )
        kasse_id = zeiger.lastrowid

        for person in namen_der_personen:
            db.execute(
                "INSERT INTO personen (kasse_id, name) VALUES (?, ?)",
                (kasse_id, person.strip()),
            )

    return token


def hole_kasse(token):
    """Gibt die Kasse zu einem Token zurück — oder None."""
    with verbindung() as db:
        return db.execute("SELECT * FROM kassen WHERE token = ?", (token,)).fetchone()


def hole_personen(kasse_id):
    with verbindung() as db:
        return db.execute(
            "SELECT * FROM personen WHERE kasse_id = ? ORDER BY id", (kasse_id,)
        ).fetchall()


# --- Ausgaben ----------------------------------------------------------------

def lege_ausgabe_an(kasse_id, titel, cent, bezahlt_von, beteiligte_ids):
    with verbindung() as db:
        zeiger = db.execute(
            "INSERT INTO ausgaben (kasse_id, titel, cent, bezahlt_von)"
            " VALUES (?, ?, ?, ?)",
            (kasse_id, titel, cent, bezahlt_von),
        )
        ausgabe_id = zeiger.lastrowid

        for person_id in beteiligte_ids:
            db.execute(
                "INSERT INTO beteiligungen (ausgabe_id, person_id) VALUES (?, ?)",
                (ausgabe_id, person_id),
            )


def hole_ausgaben(kasse_id):
    """Alle Ausgaben einer Kasse, jede mit der Liste der Beteiligten.

    Zwei Abfragen statt einer: erst die Ausgaben, dann die Beteiligungen.
    Ein JOIN würde jede Ausgabe mehrfach liefern, einmal je Beteiligtem.
    """
    with verbindung() as db:
        ausgaben = db.execute(
            "SELECT a.*, p.name AS bezahlt_von_name"
            " FROM ausgaben a JOIN personen p ON p.id = a.bezahlt_von"
            " WHERE a.kasse_id = ? ORDER BY a.id DESC",
            (kasse_id,),
        ).fetchall()

        ergebnis = []
        for ausgabe in ausgaben:
            beteiligte = db.execute(
                "SELECT person_id FROM beteiligungen WHERE ausgabe_id = ?"
                " ORDER BY person_id",
                (ausgabe["id"],),
            ).fetchall()

            ergebnis.append(
                {
                    "id": ausgabe["id"],
                    "titel": ausgabe["titel"],
                    "cent": ausgabe["cent"],
                    "bezahlt_von": ausgabe["bezahlt_von"],
                    "bezahlt_von_name": ausgabe["bezahlt_von_name"],
                    "beteiligte": [zeile["person_id"] for zeile in beteiligte],
                }
            )

        return ergebnis
