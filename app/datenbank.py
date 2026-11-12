"""Zugriff auf die Datenbank.

Wir benutzen SQLite: Die ganze Datenbank ist eine einzige Datei neben der
Anwendung. Kein Server, keine Zugangsdaten, nichts zu installieren.
"""

import os
import secrets
import sqlite3
from pathlib import Path

# Beim Entwickeln liegt die Datenbank neben dem Projekt. Im Container liegt sie
# in einem Verzeichnis, das den Neustart überlebt — deshalb die Umgebungsvariable.
VERZEICHNIS = Path(os.getenv("DATENBANK_VERZEICHNIS", Path(__file__).parent.parent))
DATENBANK_DATEI = VERZEICHNIS / "gruppenkasse.db"

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
    bezahlt_von          INTEGER NOT NULL REFERENCES personen(id),
    original_waehrung    TEXT,
    original_cent        INTEGER,
    kurs                 REAL
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
    """Legt die Tabellen an, falls sie noch nicht existieren, und wandert mit."""
    with verbindung() as db:
        db.executescript(SCHEMA)
        _wandere_mit(db)


# Spalten, die nach dem ersten Entwurf dazugekommen sind. SQLite kann Spalten
# nachträglich anfügen, aber nicht "wenn noch nicht vorhanden" — deshalb erst
# nachsehen, was schon da ist.
NACHTRAEGLICHE_SPALTEN = [
    ("ausgaben", "original_waehrung", "TEXT"),
    ("ausgaben", "original_cent", "INTEGER"),
    ("ausgaben", "kurs", "REAL"),
]


def _wandere_mit(db):
    """Ergänzt Spalten, die in älteren Datenbankdateien noch fehlen.

    Das ist eine Migration. Ohne sie bricht die Anwendung bei allen, die die
    Datenbank schon vor der Änderung angelegt haben — und das sind nach
    Sitzung 4 alle.
    """
    for tabelle, spalte, typ in NACHTRAEGLICHE_SPALTEN:
        vorhandene = [
            zeile["name"]
            for zeile in db.execute(f"PRAGMA table_info({tabelle})").fetchall()
        ]
        if spalte not in vorhandene:
            db.execute(f"ALTER TABLE {tabelle} ADD COLUMN {spalte} {typ}")


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

def lege_ausgabe_an(
    kasse_id,
    titel,
    cent,
    bezahlt_von,
    beteiligte_ids,
    original_waehrung=None,
    original_cent=None,
    kurs=None,
):
    """Legt eine Ausgabe an.

    `cent` ist immer der Betrag in der Währung der Kasse. War die Ausgabe in
    einer anderen Währung, stehen Originalbetrag, Originalwährung und der
    verwendete Kurs zusätzlich daneben — damit später nachvollziehbar ist,
    wie gerechnet wurde.
    """
    with verbindung() as db:
        zeiger = db.execute(
            "INSERT INTO ausgaben"
            " (kasse_id, titel, cent, bezahlt_von, original_waehrung,"
            "  original_cent, kurs)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (kasse_id, titel, cent, bezahlt_von, original_waehrung,
             original_cent, kurs),
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
                    "original_waehrung": ausgabe["original_waehrung"],
                    "original_cent": ausgabe["original_cent"],
                    "kurs": ausgabe["kurs"],
                    "beteiligte": [zeile["person_id"] for zeile in beteiligte],
                }
            )

        return ergebnis
