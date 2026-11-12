# Ein Container ist ein Paket aus Betriebssystem, Python, unseren
# Abhängigkeiten und unserem Code. Was hier läuft, läuft überall gleich —
# das beendet das "bei mir läuft es doch".

FROM python:3.12-slim

WORKDIR /app

# Erst nur die Abhängigkeiten kopieren und installieren. Solange sich
# requirements.txt nicht ändert, muss dieser Schritt beim nächsten Bauen
# nicht wiederholt werden.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Die Datenbankdatei liegt außerhalb des Containers, damit die Daten einen
# Neustart überleben.
VOLUME ["/daten"]
ENV DATENBANK_VERZEICHNIS=/daten

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
