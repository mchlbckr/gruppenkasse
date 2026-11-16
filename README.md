# Gruppenkasse

Gemeinsame Ausgaben in einer WG oder auf Reisen erfassen und am Ende ausrechnen, wer wem was
schuldet. Kasse anlegen, Link teilen, fertig — ohne Anmeldung.

Dies ist die **Referenz-Anwendung** aus Durchgang 1 der Vorlesung *Vibe Coding* an der FH Münster.
Die Commit-Historie folgt dem Verlauf der Sitzungen 2 bis 6; zu jeder Sitzung gibt es einen Tag.

| Tag | Stand am Ende von |
|---|---|
| `sitzung-02` | Spezifikation und Repository |
| `sitzung-03` | erste lauffähige Version |
| `sitzung-04` | Datenmodell und Datenbank |
| `sitzung-05` | eigene und fremde Schnittstelle |
| `sitzung-06` | Oberfläche, Test, Pipeline, Deployment |

Wer den Anschluss verloren hat, steigt am Anfang der nächsten Sitzung wieder ein:

```bash
git clone https://github.com/mchlbckr/gruppenkasse.git
cd gruppenkasse
git checkout sitzung-04
```

## Starten

```bash
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
```

```bash
cp .env.example .env
```

```bash
uvicorn app.main:app --reload
```

Dann <http://127.0.0.1:8000> öffnen.

## Tests

```bash
pytest
```

## Im Container

```bash
docker build -t gruppenkasse .
```

```bash
docker run -p 8000:8000 -v gruppenkasse-daten:/daten gruppenkasse
```

## Spezifikation

Was die Anwendung können soll, steht in [SPEC.md](SPEC.md). Die Regeln, nach denen der
KI-Agent in diesem Projekt arbeitet, in [AGENTS.md](AGENTS.md).
