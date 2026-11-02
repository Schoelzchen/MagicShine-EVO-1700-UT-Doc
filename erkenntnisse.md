# Magicshine EVO 1700 UT: Erkenntnisse aus der Bluetooth-Untersuchung

Zusammenfassung einer eintägigen Untersuchung (November 2026) an einer **Magicshine EVO 1700 UT** mit iPhone, Mac und Hammerhead Karoo 3. Ziel war, die Lampe besser vom Radcomputer aus zu steuern und zu verstehen, warum der Akkustand fast immer „100 %“ zeigt.

Die technische Referenz mit allen Bytes und Tabellen steht auf Englisch in [`reference.md`](reference.md). Hier stehen die Ergebnisse auf Deutsch, nach Themen geordnet, mit dem Weg dorthin und den Irrtümern, die unterwegs korrigiert wurden.

> **Haftungsausschluss.** Kein offizielles Magicshine-Dokument. Alles wurde an einer einzelnen Lampe mit Firmware 1.0.0 / Software 1.0.1 gemessen. Eine andere Firmware kann sich anders verhalten. Wer an die Lampe schreibt, kann ihre gespeicherten Modi verändern. Ein Befehl (`DF` auf dem Light Control Point) versetzt sie in den Firmware-Update-Modus. Nutzung auf eigene Gefahr.

---

## Das Wichtigste in Kürze

1. **Die UT hat zwei Bluetooth-Steuerwege.** Der Magicshine-eigene (`FFE0`) legt nur „eigene Modi“ an. Ein offener Standard des Radcomputer-Herstellers Xingzhe (`8CE5DD03`) steuert die Lampe direkt: **echtes Aus/An**, Abblend/Fernlicht, Helligkeit, SOS. Jeder Befehl wird bestätigt.
2. **Der Akku wird nur in Stufen gemeldet**, passend zur Akku-LED: grün (100–21 %), rot (20–11 %), rot blinkend (10–1 %). Deshalb springt die Anzeige in App und am Radcomputer von 100 auf 20 %. Genauer liefert die Lampe den Wert nicht.
3. **Eigene Firmware ist praktisch ausgeschlossen.** Die UT nutzt einen Nordic-Chip mit signiertem Update-Verfahren (Nordic Secure DFU).
4. **Existierende Karoo-Erweiterungen verstellen die Taster-Modi.** Sie schreiben bei jedem Moduswechsel und bei „Aus“ einen eigenen Modus und löschen ihn nie. Danach hat der Taster nur noch eine Stufe.
5. **Die Magicshine-App merkt sich eigene Modi selbst** und schreibt sie bei jedem Verbinden wieder auf die Lampe.
6. **Die Fernbedienung MJ-6558 („FTR LightSync“) funkt per Bluetooth-Rundruf.** Die Lampe hat sich aber die Funkadresse der Fernbedienung gemerkt. Nachahmen lässt sie sich deshalb praktisch nicht, mithören schon.

---

## 1. Gerät und Firmware

- Bluetooth-Name: `M2-B0 EVO1700_UT`.
- Firmware `1.0.0`, Hardware `1.0.0`, Software `1.0.1`. Das ist der Stand nach einem Update über die Magicshine-App.
- ANT+: Modell `522`, Software `0.101`, Hardware `1`, dazu eine 5-stellige Gerätenummer, die je Lampe verschieden ist.
- Chip: Nordic Semiconductor (passt zu ANT+), Update-Dienst Nordic Secure DFU (`FE59`).
- **Die normale EVO 1700 (ohne UT) ist technisch ein anderes Gerät:** anderer Chip, Alibaba-Update-Dienst `FEB3`, kein Xingzhe-Protokoll. Ergebnisse von dort gelten nicht automatisch für die UT und umgekehrt.

**Eigene Firmware:** Updates über Nordic Secure DFU sind normalerweise mit dem Schlüssel des Herstellers signiert. Ein verändertes Firmware-Bild würde die Lampe nicht annehmen. Ohne Öffnen der Lampe und Hardware-Zugriff führt hier kein Weg weiter. Das lohnt sich nicht: Fast alles, was man sich wünscht, geht über das Xingzhe-Protokoll.

---

## 2. Empfohlener Steuerweg: das Xingzhe-Protokoll

Die UT enthält den Dienst `ADB425D4-B1C6-11ED-AFA1-0242AC120002` mit den Characteristics `8CE5DD01`–`8CE5DD04`. Er folgt dem öffentlich dokumentierten **„Bluetooth Light Profile“ von Xingzhe** (<https://developer.imxingzhe.com/docs/device/light/>), das für Radcomputer gedacht ist. Die Magicshine-App benutzt diesen Weg selbst gar nicht.

**So steuert man die Lampe:**
1. Verbinden.
2. Indications auf `8CE5DD03` und Notifications auf `8CE5DD02` einschalten.
3. `00` (Steuerung übernehmen) schreiben, Antwort `80 00 01`.
4. Befehle schreiben, jeweils mit Antwort `80 <Befehl> 01`:

| Befehl | Wirkung | Getestet |
|---|---|---|
| `03 00` | **Licht aus** | ✅ |
| `03 0F` | Licht an, mit der zuletzt eingestellten Helligkeit | ✅ |
| `04 00` / `04 01` | Abblendlicht / Fernlicht | ✅ |
| `06 <0–100>` | Helligkeit in Prozent (getestet: 10, 25, 50) | ✅ |
| `03 11` | SOS | ✅ |
| `03 07` | schnelles Blinken: **keine Wirkung, keine Antwort** | ❌ |

**Beobachtetes Verhalten:**
- Die Antwort kommt nach **40–130 ms**. Das ist spürbar schneller als die Steuerung über ANT+.
- **Die Taster-Modi bleiben unverändert.** Dieser Weg legt keine eigenen Modi an.
- **Nach dem Trennen behält die Lampe ihren Zustand.** Ausgeschaltet bleibt sie aus und ist sofort wieder verbindbar.
- **Jeder Tastendruck an Lampe oder Fernbedienung wird gemeldet** (`8CE5DD02`: Modus, Abblend/Fernlicht, Helligkeit). Blinkmodi werden **nicht** gemeldet.
- Die Helligkeit im Status bezieht sich auf das Maximum des jeweiligen Lichts: Abblend 25/50/100 % = 200/400/800 lm, Fernlicht 25/50/100 % = 400/800/1700 lm.
- Die übrigen Funktionen der Spezifikation (Auto-Sleep, Bremslicht, Lichtsensor, Animationen, Navigation, Fernbedienungs-Abfrage) **beantwortet die UT nicht**, auch nicht mit „nicht unterstützt“. Sie ignoriert sie still.

**Wichtig:** Hält ein Gerät die Bluetooth-Verbindung dauerhaft, sendet die Lampe keinen eigenen Rundruf mehr. In diesem Zustand ließ sie sich per Fernbedienung nicht einschalten. Eine Steuer-App sollte nach dem Schalten wieder trennen oder das zumindest berücksichtigen.

---

## 3. Der Magicshine-Weg (`FFE0`) und die „eigenen Modi“

Rahmenformat: `DE <Länge> <Befehl> <Daten…> <XOR> ED`. Die XOR-Prüfsumme wird von der Länge bis zum letzten Datenbyte gebildet.

**Reine Abfragen** (verändern nichts):
- `DE06A400A2ED`: Akku-Stufe in Frame-Byte 8.
- `DE06A100A7ED`: Temperatur in °C in Frame-Byte 8. Projekte für andere Lampen suchen sie über das Muster `17 03`, das es bei der UT nicht gibt.
- `DE06AD00ABED`: Modellname (`EVO1700_UT`).

**Der Befehl `A2` legt eigene Modi an oder löscht sie.** Er stellt das Licht nicht „live“ ein:

```
DE 14 A2 01 <Slot> <Abblend: an, Muster, Wert> <Fernlicht: an, Muster, Wert> 00×6 <BB|AA> <XOR> ED
```

- `BB` = eigenen Modus anlegen bzw. überschreiben. Die Lampe springt sofort hinein. Ab dann schaltet der Taster **nur noch durch die eigenen Modi** dieses Lichts statt durch die drei Werksstufen.
- `AA` = eigenen Modus löschen. Ohne eigene Modi kommen die Werksstufen zurück.
- `00` am Ende ignoriert die Lampe.
- Muster: `01` dauerhaft, `02` SOS, `03` Flash. Wert = Helligkeit in Prozent.

**Gemessene Regeln für die Slots:**
- Der Slot ist eine **Platznummer in einer gemeinsamen Liste**, keine Wahl zwischen Abblend- und Fernlicht. Welches Licht gemeint ist, steht allein im Inhalt.
- Mindestens **6 Slots** funktionieren. Der Taster schaltet sie in Slot-Reihenfolge durch.
- **Beim Löschen rücken die Slots nach.** Nach dem Löschen von Slot 1 wird Slot 2 zu Slot 1.
- `AA` löscht **nach Slot**, der restliche Inhalt ist egal.
- Ein `BB` hinter das Ende der Liste wird abgelehnt.
- Eigene Modi überstehen das Aus- und Einschalten.

**Sicher aufräumen:** so lange `AA` auf Slot 1 senden, bis die Lampe mit `DE07B60000B1ED` antwortet. Dann sind alle eigenen Modi weg.

**Eigene Modi auslesen:** Eine Abfrage der Liste gibt es nicht. Ihren Inhalt erfährt man, wenn man am Taster durchschaltet und dabei den Xingzhe-Status mitliest. Die Anzahl lässt sich über abgelehnte `BB`-Befehle ermitteln. Das legt aber einen Probe-Modus an und hat in einem Fall den Taster bis zum Aufräumen blockiert.

### Warum die Taster-Modi „verschwinden“

Zwei bekannte Karoo-Erweiterungen (KarooFireFly und LightONKaroo, Stand November 2026) steuern Magicshine-Lampen über `A2 … BB` und löschen nie mit `AA`. Ihr **„Aus“ ist `A2` mit Helligkeit 0**. Bei der UT schaltet das nicht aus, sondern legt einen eigenen Modus an, den die Lampe mit Minimum betreibt (Status: 1 %). LightONKaroo sendet dieses „Aus“ laut Quellcode jedes Mal, wenn man seinen Einstellungsbildschirm öffnet. Folge: Am Taster gibt es nur noch eine sehr schwache Abblend-Stufe. Mit der Aufräum-Methode oben oder durch Löschen in der Magicshine-App ist das behebbar.

---

## 4. Wie die Magicshine-App mit eigenen Modi umgeht

Ermittelt per Mitschnitt mit dem iPhone (PacketLogger):
- **Die App speichert eigene Modi lokal** und liest sie nie aus der Lampe. Modi, die ein anderes Gerät angelegt hat, zeigt sie nicht an.
- **Beim Verbinden schreibt sie alle gespeicherten Modi zurück** auf die Lampe, in der Reihenfolge Slot 1, 2, … Einen Modus, den ein anderes Gerät gelöscht hat, bringt sie also zurück. Dauerhaft löschen kann man nur in der App.
- Sie vergibt die Slots in der Reihenfolge des Anlegens. Die Oberfläche bietet nur einen Modus pro Licht an, die Lampe kann mehr.
- Beim Bewegen des Reglers sendet sie `BB` als Vorschau. **„Speichern“ sendet nichts.**
- „Zurück ohne Speichern“ löscht nur einen **neu angefangenen** Modus. Bei bestehenden stellt es den gespeicherten Wert wieder her.
- „Löschen“ sendet `AA` und schreibt die übrigen Modi auf die nachgerückten Slots neu.
- Solange die App die **Einstellungsseite** der Lampe zeigt, kommt kein anderes Gerät an die Lampe. In der Übersicht (Akku, Temperatur) ist eine gleichzeitige Verbindung möglich.
- Die Schalter „Light Sensor“ und „Motion Detection“ sind bei der UT ausgegraut. Die Lampe hat offenbar keinen Lichtsensor.

---

## 5. Akku und Temperatur

- **Akku-Stufen** laut Anleitung und Beobachtung: grün 100–21 %, rot 20–11 %, rot blinkend 10–1 %. App und ANT+-Radcomputer zeigen nur diese Stufen.
- **Unter 10 %** schaltet die Lampe zwangsweise auf die kleinste Abblendstufe. Ob sie dann noch Bluetooth-Befehle annimmt, ist offen.
- Die UT hat zusätzlich den Bluetooth-Standard-Akkudienst (`2A19`). Ob er feiner auflöst, ist noch nicht gemessen.
- **Restlaufzeit schätzen** lässt sich mit den Herstellerangaben:

| Licht | Stufe | Lumen | Laufzeit |
|---|---|---|---|
| Abblend | niedrig / mittel / hoch | 200 / 400 / 800 | 17 / 9 / 5 h |
| Fernlicht | niedrig / mittel / hoch | 400 / 800 / 1700 | 10 / 5 / 3 h |
| Blinken | Day / Night Flash | 0–1700 / 400–1700 | 10,5 / 6 h |

- **Temperatur:** In den Tests bis 46 °C, in einem eigenen Test des Testers über 60 °C. **Die Lampe schaltet wegen Hitze nicht ab**, sie regelt vorher die Helligkeit herunter.
- Laut Tester gibt es **kein Auto-Off** und **keine StVZO-Zulassung**.

---

## 6. Bedienung von Lampe und Fernbedienung

**Lampe (eine Taste):**

| Geste | Wirkung |
|---|---|
| 1 s halten | an / aus; sie startet im zuletzt genutzten Modus |
| Klick | nächste Stufe (niedrig → mittel → hoch) |
| Doppelklick | Abblend ↔ Fernlicht |
| Klick, wenn aus | Akkustand für 3 s |
| 3 s halten, wenn aus | Sperre für den Transport an/aus |

**Fernbedienung MJ-6558 (○ und □), über den Status nachgemessen:**

| Geste | Wirkung |
|---|---|
| ○ kurz | nächste Stufe des aktuellen Lichts |
| ○ doppelt | Abblend ↔ Fernlicht; das neue Licht startet auf der niedrigen Stufe. Im Fernlicht schaltet ○ dann die Fernlicht-Stufen durch |
| □ kurz | **Fernlicht volle Leistung** (1700 lm); ○ oder □ führt zurück zur vorherigen Abblend-Stufe |
| □ doppelt | Blinkmodus; ein zweites □ doppelt blinkt schneller, ○ beendet ihn |
| ○ oder □ 1 s halten | an / aus |
| 5 s halten | Fernbedienung sperren / entsperren |

**Koppeln:** Lampe an, ○ und □ etwa 5 s halten, bis die Fernbedienung blau blinkt. Dann an den Lampentaster halten, bis auch die Lampe blau blinkt, und ○ oder □ klicken. Laut Anleitung teilen sich Fernbedienung und Shimano Di2 die Kopplung: Vor dem Koppeln mit Di2 muss die Fernbedienung entkoppelt werden. ANT+ ist davon unabhängig.

---

## 7. Die Fernbedienung als Funksignal

- „FTR LightSync“ (Front, Tail, Remote) ist **Bluetooth-Rundfunk** (Advertising). Bei jedem Tastendruck sendet die MJ-6558 eine kurze Salve gleicher Pakete mit Service Data auf `FFE1`:

```
18 01 06 <Zähler> 02 02 <Tastencode>
```

| Taste | kurz | doppelt | lang |
|---|---|---|---|
| ○ | `21` | `22` | `23` |
| □ | `11` | `12` | `13` |

- Im Paket steht **keine Kennung**. Die Lampe speichert stattdessen die **Funkadresse der gekoppelten Fernbedienung** im Dienst `42820001` (Characteristic `42820004`). Im selben Dienst stehen die ANT+-Gerätenummer der Lampe (`42820002`) und zwei leere Plätze, vermutlich für weiteres Zubehör.
- **Nachahmen:** macOS kann solche Service Data nicht senden. Der undokumentierte Schlüssel `kCBAdvDataServiceData` wird stillschweigend ignoriert, nachgewiesen mit einem iPhone als Empfänger. Android könnte die Daten senden, aber keine fremde Funkadresse annehmen. Wegen des Adressfilters ist ein Nachbau deshalb praktisch aussichtslos.
- **Mithören** funktioniert dagegen problemlos. Eine Radcomputer-Erweiterung könnte die Tasten der Fernbedienung als zusätzliche Eingabe nutzen.

---

## 8. Hammerhead Karoo und ANT+

- Die Lampe lässt sich am Karoo per ANT+ koppeln. Das **verändert keine eigenen Modi**.
- Mit „Auto Control“ schaltet der Karoo die Lampe über ANT+ selbst. Einmal geschah das direkt nach dem Koppeln, die Lampe ging auf 50 % und dann aus. Wer die Lampe per Bluetooth steuert, sollte Auto Control ausschalten, sonst arbeiten beide gegeneinander.

---

## 9. Hinweise für Entwickler

1. **Steuern über `8CE5DD03`** (Xingzhe), nicht über `A2`.
2. **Nie `A2 … BB` ohne passendes Löschen senden**, schon gar nicht als „Aus“.
3. **Den Status `8CE5DD02` abonnieren.** Er zeigt jede Änderung, auch Tastendrücke.
4. **Die Verbindung nicht dauerhaft halten**, wenn die Fernbedienung weiter funktionieren soll.
5. **Am Radcomputer Auto Control ausschalten**, wenn per Bluetooth gesteuert wird.
6. **Den Akku als Stufe anzeigen** (hoch / niedrig / kritisch), nicht als falsche Prozentzahl. Für die Restlaufzeit die Herstellerangaben und die Zeit pro Stufe nutzen.
7. **Niemals senden:**
   - `DF` auf `8CE5DD03` (Firmware-Update-Modus)
   - irgendetwas an `FE59`/`8EC90003`
   - unbekannte Opcodes
   - an `FFE4`, `FFE6`, `8CE5DD04` und den Dienst `42820001`

---

## 10. Irrtümer, die unterwegs korrigiert wurden

Damit andere nicht in dieselben Fallen laufen:
- **„`A2` mit `00` am Ende setzt das Licht nur vorübergehend“:** Das wurde an einer EVO 1300 beobachtet, gilt aber nicht für die UT. Sie ignoriert solche Befehle.
- **„Das Platz-Byte wählt Abblend- oder Fernlicht“:** Falsch. Es ist eine Slot-Nummer, das Licht ergibt sich aus dem Inhalt.
- **„`AA` stellt die Werksmodi der betroffenen Gruppe wieder her“:** Ungenau. `AA` löscht einen Slot, und die übrigen rücken nach.
- **„Die Lampe nimmt nur eine Verbindung an“:** Falsch. Zwei gleichzeitige Verbindungen funktionieren, außer wenn die App auf der Einstellungsseite ist.
- **„Der erste Status nach dem Verbinden ist unzuverlässig“:** Falsch. Die Lampe war in dem Fall einfach aus.
- **„□ an der Fernbedienung = Übersetzungsfehler“:** Beide Beschreibungen stimmen. □ ist „volle Leistung“, und der Fernlicht-Modus mit durchschaltbaren Stufen wird über ○ doppelt erreicht.

---

## 11. Offene Fragen

- Meldet `2A19` den Akku bei einer Entladung feiner als die LED-Stufen?
- Nimmt die Lampe unter 10 % Akku noch Bluetooth-Befehle an?
- Ab welcher Temperatur regelt sie herunter, und ist das im Status sichtbar?
- Wie viele Slots für eigene Modi gibt es höchstens (mindestens 6)?
- Was bedeuten `A6 01`, `FFE2`–`FFE7` und die Beschriftungen (`2901`) im Dienst `42820001`?
- Welche Geste löscht die Kopplung an der UT genau? (Laut Anleitung: Klick, dann 3 s halten; andere Magicshine-Anleitungen nennen 10 s.)
- Blockiert eine gehaltene Verbindung immer das Einschalten per Fernbedienung?

---

## 12. Vorgehen und Werkzeuge

- **Mac:** Python mit [bleak](https://github.com/hbldh/bleak) für Scans, Dienstlisten und gezielte Befehle. Eine Webcam hat die Helligkeit an der Wand gemessen, damit die Tests automatisch auswertbar waren.
- **iPhone:** Apples Bluetooth-Logging-Profil und PacketLogger, um die offizielle Magicshine-App mitzuschneiden. Anleitung: [`anleitung-mitschnitt-apple.md`](anleitung-mitschnitt-apple.md).
- **Karoo 3:** `adb`, nur lesend.
- **Ablauf:** Jede Testreihe begann mit dem Notieren der Taster-Modi und endete mit dem Aufräumen und einer Kontrolle am Taster. Unbekannte Befehle und Update-Dienste wurden nie beschrieben.

## 13. Quellen und Dank

- [lenne0815/karoo-magicshine-controls](https://github.com/lenne0815/karoo-magicshine-controls): Messungen an der EVO 1700 (ohne UT), Entladetest
- [TimFourcode/evo1300](https://github.com/TimFourcode/evo1300): erster Einsatz von `8CE5DD03` (HORI 1300), Beobachtung zum Speicher-Byte
- [m4jki/allty-1500s-control](https://github.com/m4jki/allty-1500s-control): `A2` als Anlegen/Löschen eigener Modi mit Slots
- [JaJaJim/KMagicWheeltopBlip](https://github.com/JaJaJim/KMagicWheeltopBlip): Funkformat der MJ-6558
- [derstrassi/karoofirefly](https://github.com/derstrassi/karoofirefly), [JaJaJim/LightONKaroo](https://github.com/JaJaJim/LightONKaroo): Karoo-Anbindung und ursprüngliche Magicshine-Befehle
- Xingzhe Bluetooth Light Profile: <https://developer.imxingzhe.com/docs/device/light/>
- Magicshine: Bedienungsanleitung EVO 1700 UT, Faltblatt MJ-6558, FAQ (Fakten zusammengefasst, nicht wiedergegeben)
