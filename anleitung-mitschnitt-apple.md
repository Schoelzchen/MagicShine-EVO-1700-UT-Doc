# Magicshine-Lampe analysieren mit iPhone und Mac

Anleitung, um die Bluetooth-Schnittstelle einer Magicshine-Lampe (hier die **EVO 1700 UT**) mit iPhone und Mac zu untersuchen. Ziel:

1. herausfinden, welche Bluetooth-Dienste die Lampe anbietet (u. a. welches Firmware-Update-Verfahren sie nutzt),
2. die Befehle der offiziellen Magicshine-App mitschneiden (Abblend-/Fernlicht, Helligkeit, Modi, Akku),
3. optional: ein offizielles Firmware-Update mitschneiden, um das Firmware-Bild zu erhalten.

Alle Schritte sind rein lesend bzw. beobachtend. Es wird nichts an die Lampe geschrieben, was nicht auch die offizielle App tut.

---

## Vorbereitung

- Damit nichts dazwischenfunkt, sollte nur ein Gerät mit der Lampe verbunden sein. Solange die Magicshine-App die Einstellungsseite der Lampe zeigt, ist die Lampe für andere Geräte gar nicht erreichbar. Vor jedem Schritt:
  - Magicshine-App schließen bzw. die Lampe darin trennen,
  - Radcomputer-Erweiterungen, die die Lampe per Bluetooth verbinden, deaktivieren oder den Radcomputer ausschalten.
- Lampe aufladen und einschalten.
- Andere Bluetooth-Geräte am iPhone (AirPods, Apple Watch, …) möglichst ausschalten, damit der Mitschnitt übersichtlich bleibt.

---

## Schritt 1: Dienste der Lampe auflisten

Dauer: ca. 5 Minuten. Benötigt: nur das iPhone **oder** den Mac.

### Mit dem iPhone

1. App **nRF Connect for Mobile** (Nordic Semiconductor) oder **LightBlue** (Punch Through) aus dem App Store installieren, beide kostenlos.
2. App öffnen und nach Geräten suchen. Die Lampe heißt vermutlich ähnlich wie `M2-B0 …` oder enthält `EVO`.
3. Lampe auswählen und **Connect** tippen.
4. Die Liste der Dienste (Services) per Screenshot festhalten. Jeden Dienst aufklappen, damit auch die Kanäle (Characteristics) sichtbar sind.
5. Falls vorhanden, den Dienst **Device Information** (`180A`) öffnen und diese Werte notieren:
   - Manufacturer Name
   - Model Number
   - Firmware Revision
   - Hardware Revision
   - Software Revision
6. **Nur lesen, nichts schreiben.** Danach trennen.

### Mit dem Mac

Gleiches Vorgehen mit **LightBlue** (Mac App Store) oder dem kostenlosen Open-Source-Programm **Bluetility**. Beide nutzen das eingebaute Bluetooth des Macs. *nRF Connect for Desktop* ist nicht nötig, es braucht zusätzlich einen Nordic-USB-Stick.

> Apple zeigt statt der MAC-Adresse eine eigene Geräte-Kennung an. Das ist normal.

### Worauf es ankommt

| Gefundene UUID | Bedeutung |
|---|---|
| `FFE0` / `FFE1` | Herstellereigener Steuerkanal von Magicshine (bekannt) |
| `ADB425D4-…` mit `8CE5DD01`–`8CE5DD04` | Xingzhe Light Profile, offener Steuerweg mit echtem Aus/An (siehe `erkenntnisse.md`) |
| `FEB3` mit `FED4`–`FED8` | Alibaba IoT Service (AIS), Update-Verfahren wie bei der EVO 1700 ohne UT. Im Referenz-Code ohne Signatur, nur Prüfsumme |
| `FE59` | Nordic Secure DFU, meist kryptografisch signiert (eigene Firmware praktisch ausgeschlossen) |
| `00001530-1212-EFDE-1523-785FEABCD123` | Älteres Nordic-DFU-Verfahren ohne Signatur |
| `180F` / `2A19` | Standard-Akkudienst. Bei der EVO 1700 ohne UT nicht vorhanden, bei der UT vorhanden |
| `180A` | Geräteinformationen (siehe oben) |

---

## Schritt 2: Die Magicshine-App mitschneiden

Benötigt: iPhone mit der Magicshine-App, Mac, Lightning- bzw. USB-C-Kabel, eine (kostenlose) Apple-ID.

### Einmalig einrichten

1. **Bluetooth-Logging-Profil installieren**
   1. Auf <https://developer.apple.com/bug-reporting/profiles-and-logs/> mit der Apple-ID anmelden. Ein kostenpflichtiges Entwicklerkonto ist nicht nötig.
   2. Unter *iOS* das Profil **Bluetooth** herunterladen.
   3. Auf dem iPhone öffnen (per AirDrop oder direkt in Safari) und installieren: *Einstellungen → Allgemein → VPN und Geräteverwaltung → Profil installieren*.
   4. Falls das Profil darum bittet: iPhone neu starten.
   5. Das Profil läuft nach einigen Tagen automatisch ab und muss dann neu installiert werden.
2. **PacketLogger auf dem Mac besorgen**
   1. Auf <https://developer.apple.com/download/all/> nach **Additional Tools for Xcode** suchen. Am besten die neueste Version zur macOS-Version des Macs wählen.
   2. Das DMG öffnen. Im Ordner **Hardware** liegt **PacketLogger.app**.
   3. PacketLogger in den Programme-Ordner kopieren.

### Mitschnitt aufnehmen

1. iPhone per Kabel an den Mac anschließen, entsperren und **Vertrauen** bestätigen.
2. PacketLogger starten und **File → New iOS Trace** wählen. Ab jetzt wird der Bluetooth-Verkehr des iPhones live aufgezeichnet.
3. Die Magicshine-App öffnen und mit der Lampe verbinden.
4. Die folgenden Aktionen **langsam und nacheinander** ausführen, mit etwa 5 Sekunden Pause dazwischen. Die Reihenfolge und Uhrzeiten mitschreiben (Vorlage siehe unten):
   1. Verbinden, Akku- und Temperaturanzeige ansehen
   2. Nur **Abblendlicht** einschalten, Helligkeit in mehreren Stufen ändern (z. B. niedrig → mittel → hoch)
   3. Nur **Fernlicht** einschalten, ebenso mehrere Stufen
   4. Abblend- und Fernlicht **gleichzeitig**, falls die App das anbietet
   5. **Blinken**, **SOS** und weitere Muster
   6. **Aus**
   7. Einen **eigenen Modus anlegen**, ändern und wieder **löschen**
   8. Die Seite mit **Firmware-Version / Version Upgrade** öffnen, **ohne** ein Update zu starten
   9. Sonstige Einstellungen der App einmal antippen (z. B. Lichtsensor, Di2, ANT+), ohne sie dauerhaft zu ändern
5. In PacketLogger mit **File → Save** als `.pklg` speichern, z. B. `magicshine-evo1700ut-app.pklg`.

### Optional: Firmware-Update mitschneiden

Nur wenn die App ohnehin ein Update anbietet und du es installieren möchtest. Ein Update nur für den Mitschnitt würde ich nicht auslösen.

1. Wie oben einen neuen iOS-Trace starten.
2. Lampe voll geladen lassen, iPhone nah an die Lampe legen.
3. Update in der App starten und bis zum Ende warten. Währenddessen nichts anderes tun.
4. Als eigene Datei speichern, z. B. `magicshine-evo1700ut-update.pklg`. Der Mitschnitt enthält dann das vollständige Firmware-Bild.

### Protokoll-Vorlage

```
Datum:
Lampe / Firmware-Version laut App:
iPhone-Modell / iOS-Version:
Magicshine-App-Version:

Uhrzeit   Aktion in der App                    Beobachtung an der Lampe
--------  -----------------------------------  ------------------------
12:00:00  verbunden                            -
12:00:10  Abblendlicht niedrig                 ...
...
```

---

## Ergebnisse übergeben

- Screenshots aus Schritt 1, die `.pklg`-Datei(en) und das ausgefüllte Protokoll.
- Die `.pklg`-Datei enthält den **gesamten** Bluetooth-Verkehr des iPhones. Wenn andere Geräte aktiv waren, sind auch diese enthalten. Ausgewertet wird nur die Verbindung zur Lampe.
- Wireshark kann `.pklg`-Dateien direkt öffnen. Nützliche Filter:
  - `btatt` – alle Bluetooth-Datenpakete
  - `btatt.opcode == 0x12 || btatt.opcode == 0x52` – Schreibbefehle der App an die Lampe
  - `btatt.opcode == 0x1b` – Antworten der Lampe (Notifications)

---

## Hintergrund

- Rahmenformat der Magicshine-Befehle: `DE <Länge> <Befehl> <Daten…> <XOR-Prüfsumme> ED`. `A2` legt eigene Modi an (`BB`) bzw. löscht sie (`AA`), `A4` fragt den Akku ab, `A1` die Temperatur.
- Die UT hat zusätzlich das Xingzhe-Steuerprotokoll (`8CE5DD03`). Die Magicshine-App benutzt es nicht, es taucht im Mitschnitt also nicht auf.
- Alle Ergebnisse stehen in [`erkenntnisse.md`](erkenntnisse.md) (Deutsch) und [`reference.md`](reference.md) (Englisch).
