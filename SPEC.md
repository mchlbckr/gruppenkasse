# Gruppenkasse — Spezifikation

Gemeinsames Projekt aus Durchgang 1 der Vorlesung *Agentic Engineering*.
In Sitzung 2 im Kurs erarbeitet.

## Problem

Wenn eine WG oder eine Urlaubsgruppe zusammen Geld ausgibt, zahlt mal die eine, mal der andere,
und nicht immer für alle. Am Ende weiß niemand, wer wem was schuldet. Die üblichen Lösungen —
eine Notiz im Handy, eine Tabelle, ein Zettel am Kühlschrank — scheitern daran, dass nicht alle
hineinschreiben.

## Nutzer

Eine Gruppe von drei bis acht Personen, die sich kennen. Niemand legt ein Konto an, niemand
installiert etwas. Eine Person legt die Kasse an und teilt einen Link.

## Was die Anwendung können muss

1. Eine **Kasse** anlegen: Name, Währung, Teilnehmende (Vornamen).
2. Die Kasse über einen **unerratbaren Link** teilen; wer den Link hat, darf lesen und schreiben.
3. Eine **Ausgabe** erfassen: Titel, Betrag, Währung, wer bezahlt hat, wer beteiligt war.
4. Beträge in **Fremdwährung** zum Tageskurs in die Kassenwährung umrechnen.
5. Je Person den **Saldo** anzeigen: Wer liegt vorn, wer schuldet?
6. Einen **Ausgleichsvorschlag** berechnen: wer wem wie viel überweist, mit möglichst wenigen
   Überweisungen.

## Was sie nicht können muss

- Keine Anmeldung, keine Passwörter, keine Benutzerkonten.
- Keine echten Zahlungen, keine Bankanbindung.
- Keine Bearbeitung der Vergangenheit über das Löschen einer Ausgabe hinaus.
- Keine App für das Telefon — die Webseite muss auf dem Telefon nur gut bedienbar sein.

## Regeln

**Aufteilung.** Eine Ausgabe wird gleichmäßig auf die beteiligten Personen aufgeteilt. Geht der
Betrag nicht glatt auf, erhalten die ersten Beteiligten den zusätzlichen Cent, sodass die Summe der
Anteile exakt dem Betrag entspricht.

**Saldo.** Der Saldo einer Person ist die Summe dessen, was sie bezahlt hat, minus die Summe ihrer
Anteile. Die Summe aller Salden ist immer null.

**Ausgleich.** Es wird vorgeschlagen, dass die Person mit dem größten negativen Saldo an die Person
mit dem größten positiven Saldo überweist, und zwar den kleineren der beiden Beträge. Das
wiederholt sich, bis alle Salden null sind. Das Ergebnis ist nicht garantiert die kleinstmögliche
Anzahl an Überweisungen, aber immer eine kleine — und es ist in zwei Sätzen erklärbar.

**Währung.** Der Umrechnungskurs wird beim Erfassen der Ausgabe einmal abgerufen und **gespeichert**.
Spätere Kursänderungen verändern bereits erfasste Ausgaben nicht.

## Abnahmekriterien

Die Anwendung ist fertig, wenn:

- [ ] eine Kasse angelegt und über ihren Link von einem anderen Gerät geöffnet werden kann,
- [ ] eine Ausgabe mit Teilbeteiligung erfasst werden kann (nicht alle sind beteiligt),
- [ ] eine Ausgabe in Fremdwährung korrekt umgerechnet gespeichert wird,
- [ ] die Salden aller Personen in Summe null ergeben, auch bei krummen Beträgen,
- [ ] der Ausgleichsvorschlag alle Salden auf null bringt,
- [ ] die Seite auf einem Telefon bedienbar ist,
- [ ] die Anwendung unter einer öffentlichen Adresse läuft.

## Daten

Es werden ausschließlich Testdaten verarbeitet: Vornamen oder Spitznamen. Keine Mailadressen,
keine Konten, keine echten Zahlungsdaten.
