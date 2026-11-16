# Projektregeln für den Agenten

Dieses Projekt wird in der Vorlesung *Vibe Coding* gemeinsam entwickelt. Es ist Lehrmaterial:
Der Code muss von Leuten gelesen werden können, die gerade erst anfangen.

## Sprache

- Code, Bezeichner und Kommentare auf Deutsch, soweit es nicht albern wird.
  `berechne_salden()` ist gut, `get_Kassen_by_token()` nicht.
- Commit-Nachrichten auf Deutsch, eine Zeile, was sich fachlich ändert.

## Technik

- Python mit FastAPI, SQLite über das Standardmodul `sqlite3`, kein ORM.
- Oberfläche: HTML-Vorlagen mit Jinja2, einfaches CSS, JavaScript nur wo nötig.
- Keine zusätzlichen Abhängigkeiten ohne Rückfrage. Was in `requirements.txt` steht, ist die Liste.
- Geldbeträge **niemals** als Gleitkommazahl rechnen. Intern in Cent als ganze Zahl.

## Stil

- Lieber eine Funktion mehr als eine clevere Zeile.
- Jede Funktion, die eine fachliche Regel umsetzt, bekommt einen kurzen Kommentar mit der Regel
  im Klartext — und einen Test.
- Keine Abkürzungen in Namen.

## Was nicht passieren darf

- Keine Schlüssel, Token oder Passwörter im Code oder in committeten Dateien.
  Alles Geheime kommt aus Umgebungsvariablen, Vorlage ist `.env.example`.
- Keine echten personenbezogenen Daten in Testdaten oder Beispielen.
