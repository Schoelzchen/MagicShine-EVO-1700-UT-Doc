# Magicshine EVO 1700 UT – Bluetooth LE Reference

Reverse-engineered description of the Bluetooth LE interface of the **Magicshine EVO 1700 UT** front light, measured on a real unit in November 2026.

Unless a source is named, every statement here was measured on that unit. Statements taken from other projects or specifications are marked as such. A German summary of all findings, including how they were obtained, is in [`erkenntnisse.md`](erkenntnisse.md).

> **Disclaimer.** This is not an official Magicshine document. The interface is undocumented by Magicshine and may change with firmware updates. Writing to the light can change its stored modes. One command (`DF` on the Light Control Point) puts it into firmware-update mode. Use at your own risk.

---

## 1. Device under test

| Item | Value |
|---|---|
| Advertised name | `M2-B0 EVO1700_UT` |
| Manufacturer (`2A29`) | `Magicshine` |
| Model (`2A24`) | `EVO1700 UT` |
| Firmware (`2A26`) / Hardware (`2A27`) / Software (`2A28`) | `1.0.0` / `1.0.0` / `1.0.1` |
| ANT+ product info (as shown by a Hammerhead Karoo 3) | 5-digit device number (unit-specific), model `522`, software `0.101`, hardware `1` |
| Radio / bootloader | Nordic Semiconductor SoC with Nordic Secure DFU (`FE59`) |
| Firmware state | updated via the official Magicshine iOS app on 2026-11-01, before all measurements |

The non-UT **EVO 1700** is a different design. It has a different GATT layout, an Alibaba AIS OTA service (`FEB3`) instead of Nordic DFU, and no Xingzhe light service. See [lenne0815/karoo-magicshine-controls](https://github.com/lenne0815/karoo-magicshine-controls). Do not assume results transfer between the two.

---

## 2. GATT database

| Service | Characteristic | Properties | Purpose |
|---|---|---|---|
| `180A` Device Information | `2A29`, `2A24`, `2A25`, `2A27`, `2A26`, `2A28`, `2A23`, `2A2A`, `2A50` | read | Standard. System ID, regulatory data and PnP ID read as zeros |
| `180F` Battery | `2A19` | read, notify | Standard battery level in % |
| `FFE1` Magicshine legacy | `FFE0` | read, write, notify | Magicshine command/response channel (section 4) |
| | `FFE2` | read | unknown, read `01 00 01` |
| | `FFE3` | read, notify | unknown, read `00 64` |
| | `FFE4` | write | unknown, **not tested** |
| | `FFE5` | read, indicate | unknown, empty |
| | `FFE6` | write | unknown, **not tested** |
| | `FFE7` | read, indicate | unknown, read `02 71 00` |
| `ADB425D4-B1C6-11ED-AFA1-0242AC120002` Xingzhe Light Service | `8CE5DD01-0A4D-11E9-AB14-D663BD873D93` | read | Light Features |
| | `8CE5DD02-…` | read, notify | Light Machine Status |
| | `8CE5DD03-…` | write, indicate | **Light Control Point** (section 3) |
| | `8CE5DD04-…` | write, indicate | Light Network (spec: not implemented). **Not tested** |
| `42820001-D3E8-480B-95BB-2A34850D4048` | `42820002`–`42820008` | read | ASCII strings. `42820004` = 12 hex digits = **Bluetooth address of the paired MJ-6558 remote** (without colons). `42820003`/`42820005` read `000000000000`, possibly empty pairing slots. `42820002` = the light's **ANT+ device number** in decimal (matches the number shown on the bike computer). The `2901` descriptors were not read yet |
| `FE59` Nordic Secure DFU | `8EC90003-F315-4F60-9FB8-838830DAEA50` | write, indicate | Buttonless DFU. **Never write** |

The advertising contains the Xingzhe light service short UUID `25D4`.

---

## 3. Recommended control path: Xingzhe Light Profile

The service `ADB425D4-…` follows the public **Bluetooth Light Profile** of the bike computer maker Xingzhe (行者): <https://developer.imxingzhe.com/docs/device/light/> (version 1.6.0). It is meant for bike computers to control lights. The official Magicshine app does **not** use it. It only uses `FFE0`.

This is the only path found that offers a real **off** command without touching the light's stored modes.

### 3.1 Features and status as reported by the UT

`8CE5DD01` Light Features = `02 00 81 80 02 00 0E FF 64 00`. The light returns 10 bytes; the spec defines 20, and the Basic Functions field is missing.

| Field | Raw | Meaning (per spec) |
|---|---|---|
| Light Type (u16) | `0x0002` | front light |
| Light Mode (u32) | `0x00028081` | bit 0 off, bit 7 fast flash, bit 15 steady on, bit 17 SOS |
| Beam (u8) | `0x0E` | low/high beam supported, 3 modes |
| Focus | `0xFF` | not supported |
| Intensity | `0x64` | adjustable up to 100 % |
| Color | `0x00` | single colour |

`8CE5DD02` Light Machine Status, e.g. `2F 00 01 0F 00 19`:

| Byte | Field | Example | Meaning |
|---|---|---|---|
| 0 | Flags | `2F` | fields present: index, type, mode, beam, intensity |
| 1 | Light Index | `00` | |
| 2 | Light Type | `01` | front light |
| 3 | Light Mode | `0F` | `00` off, `0F` steady on, `11` SOS |
| 4 | Beam Mode | `00` | `00` low beam, `01` high beam |
| 5 | Intensity | `19` | current intensity in % (`FF` before the first `06` command) |

The status is sent as a notification after every change.

### 3.2 Control Point commands (`8CE5DD03`, write with response)

Each command is `<opcode> [parameter]`. The light answers with an indication `80 <opcode> <result>`, where `01` = success. The spec also defines `02` not supported, `03` invalid parameter, `04` failed and `05` not permitted.

| Command | Effect on the UT | Measured |
|---|---|---|
| `00` | Request Control. Send once after connecting, before any other command | ✅ `80 00 01` |
| `03 00` | **Light off** (fully dark) | ✅ |
| `03 0F` | Light on (steady) with the last intensity | ✅ |
| `03 11` | SOS | ✅ |
| `03 07` | Fast flash. **No effect, no indication**, even though it is listed in Features | ❌ |
| `04 00` / `04 01` | Low beam / high beam (status confirms; high beam was not checked by eye) | ✅ |
| `06 <0–100>` | Intensity in %. Tested with 10, 25 and 50 % on the low beam | ✅ |
| `01` | Reset of device control. Scope unclear, **not tested** | – |
| `DF` | **Enters DFU mode and disconnects. Never send** | – |

Minimal sequence:
1. Connect.
2. Enable indications on `8CE5DD03` and notifications on `8CE5DD02`.
3. Write `00` and wait for `80 00 01`.
4. Send `03 0F`, `04 00`, `06 32` and so on as needed.
5. Write `03 00` to switch off.

### 3.3 Full opcode list (from the spec) and UT status

Opcodes on the Light Control Point as listed in the Xingzhe spec, and whether they were tested on the UT. Functions `10`–`1A` accept `FF` (or `FFFF`/`FFFFFFFF`) as "read current value". **On the UT, none of these queries (`10`–`1A`, `24`) got any answer**, neither with the light off nor on. They are silently ignored instead of returning "not supported" (`02`). The same happens with `03 07`. This matches the missing Basic Functions field in the Features response.

| Op | Meaning | Parameter | UT |
|---|---|---|---|
| `00` | Request Control | – | ✅ works |
| `01` | Reset device control | – | untested (scope unclear) |
| `02` | Set light type | u8 | untested (do not send) |
| `03` | Set light mode | u8 | ✅ `00`, `0F`, `11`; `07` no response |
| `04` | Beam low/high | `00`/`01` | ✅ works |
| `05` | Focus | 0–100 | untested; Features say not supported |
| `06` | Intensity | 0–100 | ✅ works |
| `07` | Intensity mode manual/auto | `00`/`01` | untested |
| `08` | Fall detection | `00`/`01` | untested |
| `09` | Colour | ≤ 4 bytes | untested; light is single-colour |
| `0A` / `0B` | Training / navigation data | ≤ 18 bytes | untested; format not specified |
| `10` | Auto-sleep | `00`/`01`/`FF` | ❌ no response (query with `FF`) |
| `11` | Wake on motion | `00`/`01`/`FF` | ❌ no response (query with `FF`) |
| `12` | Auto-sleep time | u16 30–6000 s / `FFFF` | ❌ no response (query with `FF`) |
| `13` | Brake detection | `00`/`01`/`FF` | ❌ no response (query with `FF`) |
| `14` | Brake light intensity | 0–100 / `FF…` | ❌ no response (query with `FF`) |
| `15` | Ambient light sensor | `00`/`01`/`FF` | ❌ no response (query with `FF`) |
| `16`–`18` | Team animation / navigation sync / data sync | `00`/`01`/`FF` | ❌ no response (query with `FF`) |
| `19` / `1A` | Animation ID / team animation ID | u32 / `FFFFFFFF` | ❌ no response (query with `FF`) |
| `24` | Paired remote (`FFFFFFFF` = query) | u32 | ❌ no response (query with `FF`) |
| `DA` | Date and time | 8 bytes | untested |
| `DF` | Enter DFU | – | **never send** |

The official app shows switches for "Light Sensor" and "Motion Detection" for the UT, but they are greyed out and cannot be used. The UT probably has no ambient light sensor. This matches its Features response, which reports no intensity ranges and no Functions field.

Beyond the official app, the profile provides: real off/on, live beam and intensity changes without touching custom modes, live SOS, and a status notification for every change, including button presses.

### 3.4 Measured behaviour

- **Latency:** The indication arrives 40–130 ms after the write.
- **Disconnect keeps state:** After `03 00` and a disconnect, the light stays off. It keeps advertising and accepts a new connection within about 1 s. A new `00` plus `03 0F` switches it back on with the last intensity.
- **Stored modes stay untouched:** In the tested sequences the button modes were unchanged afterwards.
- **Button presses are reported.** After `00`, every press on the light's button produces a `8CE5DD02` notification with mode, beam and intensity, also for custom modes. The factory modes report as 25 / 50 / 100 % for both beams; a double click passes through intermediate values before the beam changes. Nothing is sent unsolicited on `FFE0`.
- The status read right after connecting reflects the real state: `2F 00 01 00 00 FF` = off, `2F 00 01 0F 00 FF` = on. Intensity reads `FF` until it changes.
- **Custom modes (section 4.3):** `03 00` / `03 0F` also act while a custom mode is active. `03 0F` then returns with the custom mode's intensity.
- **No release command:** The spec has no command to hand back control. Disconnecting was enough in all tests.

---

## 4. Magicshine legacy protocol (`FFE1` / `FFE0`)

Used by the official Magicshine app and by existing community projects.

### 4.1 Framing

```
DE <len> <cmd> <data …> <xor> ED
```

- `len` = total frame length including `DE` and `ED`.
- `xor` = XOR of all bytes from `len` up to the last data byte.
- Commands are written to `FFE0`. Responses arrive as notifications on `FFE0`. The response command is the request command + `0x10` (e.g. `A4` → `B4`).

### 4.2 Queries (read-only)

| Request | Response (UT) | Meaning |
|---|---|---|
| `DE06A400A2ED` (A4) | `DE13B40004000000640000000000000000C7ED` | battery: data byte 4 (frame byte 8) = `0x64` = 100 |
| `DE06A100A7ED` (A1) | `DE0DB100001118071B0103ABED` | info; **temperature in °C = data byte 4 (frame byte 8)**, here 27 °C. It rose to 39 °C with the light on |
| `DE06AD00ABED` (AD) | `…45564F313730305F5554…` | model name, ASCII `EVO1700_UT` |
| `DE06AB00ADED` (AB) | `DE08BB0000FF4CED` | speed sensor, meaning unknown |
| `DE06AC00AAED` (AC) | `DE08BC0000FF4BED` | light sensor, meaning unknown |
| `DE06A500A3ED` (A5) | none | profiles; no answer on the UT |
| `DE06A900AFED` (A9) | none | runtime; no answer on the UT |
| `DE07A601EF4FED` (A6 01) | not observed | sent by the official app after connecting; meaning unknown, **not tested** |

The official app polls `A1` and `A4` every 20 s.

Projects written for other lamps locate the temperature by searching for the byte pattern `17 03`. That pattern does not occur on the UT; use the fixed position instead.

### 4.3 `A2` – custom modes (not live control)

```
DE 14 A2 01 <slot> <G0: on, pattern, value> <G1: on, pattern, value> 00 00 00 00 00 00 <op> <xor> ED
```

| Field | Values |
|---|---|
| `slot` | Custom-mode slot, starting at `01`. The other project assumes up to 20 slots; only slots 1–2 were confirmed here |
| G0 | low beam: `on` = `01`/`00`, `pattern` = `01` steady, `02` SOS, `03` flash, `value` = intensity in % |
| G1 | high beam, same layout |
| `op` | `BB` = add/overwrite custom mode, `AA` = delete custom mode. `00` is **ignored** (no ack, no effect) |

Ack: `DE 07 B6 00 <r> <xor> ED`. Both `r = 01` and `r = 00` were observed. A delete with `r = 00` still took effect once, so the meaning of `r` is unclear.

**What `BB` really does:** It does **not** set the light "live". It stores a custom mode, and the light switches to it immediately. From then on, the button cycles only through the custom modes of that beam group instead of its three factory modes. The custom mode survives power cycles. Deleting it with `AA` brings the factory modes back.

Measured facts:
- **Slot = position in one shared list of custom modes**, not the beam choice. The beam group is defined only by which group is `on` in the frame.
- **Capacity:** slots 1–6 were all accepted, and the button cycles them in slot order. More were not tried; the other project assumes 20.
- **Low and high beam share the slot list.** Writing a high-beam mode to a slot that held a low-beam mode replaces it.
- **Slots shift down on delete.** After deleting slot 1 of six, the former slot 2 is slot 1 and slot 6 is empty. `AA` on an empty slot has no effect and is acked with `r = 00`.
- **`AA` deletes by slot. The rest of the frame is ignored.** A delete with the wrong content still removed the mode in that slot.
- `BB` on a slot beyond the end of the list (e.g. slot 3 with one mode stored) is rejected (`r = 00`, no effect). Appending to the next free slot works.
- When the active custom mode is deleted, the light jumps to the next remaining mode, or back to the factory mode when none is left.
- Ack `r`: `01` = applied. `00` comes for empty or out-of-range slots, but twice a delete with `r = 00` **did** take effect. So `r = 00` does not reliably mean "failed". Counting with "`AA` on slot 1 until `r = 00`" still works.
- **How the official app uses slots:** It assigns slots in creation order (first saved mode → slot 1, second → slot 2), enables exactly one group per mode, and also sends the other group's stored values marked "off" (e.g. `00 01 27`). Its slider sends values about 1 % below the displayed value (20 % → `0x13`).
  - Moving the slider: `BB` preview on that mode's slot. Opening a mode sends it twice.
  - "Save": sends **nothing**.
  - Back without saving, on an existing mode: `BB` with the stored value, no `AA`.
  - Back without saving, on a new mode: `AA` on the new slot, then `BB` to restore the previous mode.
  - Delete (swipe left, bin): `AA` on the entry's slot, then the remaining modes are rewritten to their shifted slots.
- **The official app keeps its custom modes locally and does not read them from the light.** It never sends `A5` and only reads `FFE0` (which holds only the last frame) and `2A19`. Modes written by another client do not appear in the app.
- **When the app connects, it writes all its stored custom modes back to the light on its own** (`BB` on slot 1, 2, … in order, about 60 ms apart). A mode deleted by another client therefore comes back the next time the app connects. To remove a custom mode for good, delete it in the app.
- Custom modes survive power cycles.

**Reading custom modes:** There is no list query (`A5` gets no answer, and the app does not read the list). Two partial methods work:
- **Content:** Subscribe to `8CE5DD02` and cycle through the modes with the button. Each press reports the active mode's pattern, beam and intensity.
- **Count:** Send `BB` from a high slot downwards (8, 7, 6, …). Writes beyond the end of the list are rejected (`r = 00`, no status notification); the first accepted slot is count + 1. **But** the accepted `BB` creates a mode, and deleting it again with `AA` once left the button unresponsive until the list was cleared and `03 0F` was sent. This is not a safe read-only method.

**Safe clean-up:** repeat `AA` on slot `01` (any content) until the ack is `r = 00`. Then the list is empty, and both beams are back to their factory modes.

**Signature of an "off" written as A2:** `BB` with intensity 0 (e.g. `DE14A20101010100000000000000000000BB0DED`, used as "off" by KarooFireFly and LightONKaroo) does not switch the light off. It stores a custom mode that the light runs at its minimum, reported as intensity `01` (1 %). Such a stray 1 % low-beam mode appeared on the light whenever LightONKaroo had been opened on the Karoo. The code explains it: LightONKaroo (v0.1.6-R4) sends its "OFF" (`A2 … 01 01 00 … BB`) to every assigned light 500 ms after its settings screen opens (`setSettingsUiActive`), regardless of the light's enabled switch. KarooFireFly sends the same frame after each 3-second mode preview (`testMode`). After LightONKaroo was uninstalled and the mode deleted, it did not come back. Re-pairing the light via ANT+ on the Karoo did not create any custom mode.

**Pitfalls seen in existing projects:** Several Karoo extensions use `BB` for every mode change and never send `AA`. On the UT this leaves custom modes behind, and the button then has only one mode left per beam. To repair it, delete the entries in the Magicshine app, or send `AA` with the same slot and content.

---

## 5. Battery

- `2A19` (standard Battery Level) reads `100` on a full battery. Whether it has finer resolution than the `A4` value is **not yet measured**. No notifications arrived during short tests.
- `A4`/`B4` data byte 4 is also `100` on a full battery.
- Field observation: Magicshine app and Karoo (ANT+) showed 100 % for most of a ride and then jumped to about 20 %. This matches the indicator thresholds in the manual (21 % / 11 %, section 7.3).
- Official runtimes per mode (section 7.2) allow a software estimate of the remaining runtime.
- On the non-UT EVO 1700 (firmware v1), lenne0815 measured a full discharge in which `B4` only reported 100 → 50 → 30. The light's own button LED shows green (21–100 %), red (11–20 %) and red flashing (1–10 %).

---

## 6. Connections and coexistence

- The light accepted two simultaneous connections (Mac + iPhone app) while the app showed its overview screen. While the app showed the light's **settings screen**, other clients could not find or connect to the light.
- ANT+ control (Karoo's built-in light control) works independently of BLE. Seven seconds after re-pairing via ANT+ with **Auto Control on**, the Karoo switched the light to 50 % and then off by itself, while a BLE client was connected (it was only observed, not captured). Turn off "Auto Control" on the Karoo if a BLE controller is used, so the two don't fight.
- ANT+ pairing on the Karoo does not touch the custom-mode list.

---

## 7. Physical controls and official specifications

Source: official *EVO 1700 UT User Manual* (magicshine.com, "User Manuals"), the printed MJ-6558 leaflet and the Magicshine FAQ. Summarised here. The manuals themselves are © Magicshine and not reproduced.

### 7.1 Light button

| Gesture | State | Effect |
|---|---|---|
| hold 1 s | on / off | switch on / off; it switches on in the last used mode |
| click | on | next level LOW → MEDIUM → HIGH |
| double click | on | low beam ↔ high beam |
| click | off | show battery level for 3 s |
| hold 3 s | off | lock on (for transport). Unlock: hold 3 s or connect the charger |
| click, then hold 3 s | off | clear the pairing memory (remote / Di2). Other Magicshine manuals give "click/double click + 10 s" instead, so not verified on the UT |

### 7.2 Modes, output and runtime (manual, ANSI FL1, 25 °C, 25 km/h airflow)

| Beam | Level | Lumen | Runtime | BLE status intensity |
|---|---|---|---|---|
| Low | LOW | 200 | 17 h | 25 % |
| Low | MEDIUM | 400 | 9 h | 50 % |
| Low | HIGH | 800 | 5 h | 100 % |
| High | LOW | 400 | 10 h | 25 % |
| High | MEDIUM | 800 | 5 h | 50 % |
| High | HIGH | 1700 | 3 h | 100 % |
| Flash | Day Flash | 0–1700 | 10.5 h | – |
| Flash | Night Flash | 400–1700 | 6 h | – |

The BLE intensity in `8CE5DD02` is therefore relative to the maximum of the active beam, not to 1700 lm. The manual does not mention SOS, although the light supports it via BLE. It does not state the battery capacity either.

Tester's observations (more reliable than the manual's translation):
- **Thermal behaviour:** The light reached **over 60 °C** in one of the tester's own tests and **never switches off because of heat**; it dims down instead (thermal derating). In our tests up to 46 °C, no derating was observed in the status.
- **No auto-off.**
- **No StVZO approval.**

### 7.3 Battery indicator and low battery

| Indicator | Meaning |
|---|---|
| steady green | 100–21 % (while charging: full) |
| steady red | 20–11 % |
| flashing red | 10–1 % (while charging: charging) |

- **Below 10 %, the light switches automatically to the lowest low-beam level and cannot be changed.** Whether BLE commands are still accepted then has not been measured.
- Charging takes about 3 h at 5 V / 2 A.
- These thresholds match the observation of 100 % → 20 % on app and Karoo. The light seems to report only these indicator steps.

### 7.4 MJ-6558 remote

Behaviour measured via the `8CE5DD02` status while the tester pressed the remote (factory modes):

| Gesture | Effect (measured) |
|---|---|
| ○ or □ hold 1 s | on / off (with a paired FTR tail light: both), per manual |
| ○ click | next level of the current beam: 25 → 50 → 100 → 25 % |
| ○ double click | low beam ↔ high beam; the new beam starts at 25 % (seen twice) |
| □ click | **high beam 100 % ("full output")** from any low-beam level |
| □ or ○ click while in □ full output | back to the **previous** low-beam level |
| ○ click after ○ double click (high-beam mode) | cycles the high-beam levels 25 → 50 → 100 → 25 % |
| □ double click | flash mode; a second □ double click flashes faster (probably Day/Night Flash); ○ click ends it. **No status notification is sent for flashing** |
| any button hold 5 s | lock / unlock the remote (3 s red / green), per manual |

So both descriptions are right: the manual's "□ = full output" is accurate, and the tester's observation "high-beam mode where ○ cycles the levels" is the mode reached with ○ double click.

- **Pairing (leaflet):** Switch the light on. Hold ○ and □ for about 5 s until the remote flashes blue. Hold the remote close to the light button until the light flashes blue as well, then click ○ or □. Both indicators show blue for 2 s.
- The remote charges in about 1 h. Its indicator also shows the light's battery state (green / red / flashing red).
- "FTR LightSync" = **F**ront light, **T**ail light, **R**emote. Compatible: EVO 1700 UT, EVO 1700 PRO, MJ-6558.

### 7.5 Shimano Di2 and ANT+

- **Di2:** Clear an existing remote pairing first. Wake Di2 with a button press and switch the light on; it searches (flashing blue). Success = 3 s steady blue; it gives up after 5 min. At least two free Di2 buttons are needed. Example mapping: channel 1 click = levels, double = beam; channel 2 click = full high beam, double = Day/Night Flash. Remote and Di2 thus appear to share one pairing.
- **ANT+:** independent of remote/Di2 pairing. The light supports the ANT+ Lighting Control profile and may appear as a number on the bike computer (the same number is stored in `42820002`, see section 2).

## 8. Remote control MJ-6558 – radio protocol (measured)

The MJ-6558 (advertised name `M0-C0 MJ_6558`) is a **BLE advertiser**. "FTR LightSync" is therefore plain BLE advertising, not a separate radio protocol. Each button event is sent as a burst of about 3–17 advertisements carrying service data on UUID `FFE1`. Nothing is sent between presses.

Service data (7 bytes):

```
18 01 06 <counter> 02 02 <code>
```

| Byte | Meaning |
|---|---|
| 0–2 | `18 01 06`, constant |
| 3 | event counter, +1 per event, wraps around |
| 4–5 | `02 02`, constant |
| 6 | button code |

| Code | Button ○ | Button □ |
|---|---|---|
| short | `21` | `11` |
| double | `22` | `12` |
| long (> 1 s) | `23` | `13` |
| press start (seen just before a code) | `00` | `00` |

Effect on the UT, as reported via `8CE5DD02`:
- ○ short: next level (25 → 50 → 100 %).
- ○ long: on/off.
- ○ double: switch to high beam.
- □ short: high beam 100 %; □ or ○ again returns to the previous low-beam level. See section 7.4 for the complete, measured behaviour.
- □ double (flash mode) produces no status notification. □ long (on/off per manual) was not verified.

The payload contains **no device ID**. The light stores the **Bluetooth address of its paired remote**: characteristic `42820004` contains exactly the remote's Bluetooth address (12 hex digits, no colons), as compared with an iPhone capture of the remote's advertising. So the light very probably filters remote packets by this address. This was not tested directly.

**Emulation attempt from macOS (failed):** Passing the undocumented key `"kCBAdvDataServiceData"` (string key) to `CBPeripheralManager.startAdvertising` reports success, but an iPhone scanning nearby never received any `FFE1` service data from the Mac. With a local name added, only flags, TX power and the name were sent. A `CBUUID` key crashes (`-[CBUUID UTF8String]`). macOS therefore cannot send this payload. The light did not react, whether or not the real remote was nearby.

Android can advertise such service data but normally cannot use a foreign, fixed Bluetooth address. Because of the address filter, emulation from a Karoo is unlikely to work either. Reading the remote's broadcasts passively, as an input for a Karoo extension, works fine.

Pairing (from the manuals): the remote is paired with the light as described in the manual, and the pairing can be removed from the remote. Without a paired remote, the light searches for other accessories again, e.g. a Shimano Di2 system. The manual suggests that the remote is the last accessory in this search; once it is paired, the light stops searching. This fits service `42820001`, which holds the light's ANT+ device number, the remote's address and two empty slots (`000000000000`), possibly for further accessories such as Di2. The slot assignment is not confirmed.

Other findings:
- The remote also exposes a GATT server with `FFE1` (`FFE0`–`FFE7`) and the Alibaba AIS OTA service `FEB3` (`FED4`–`FED8`), similar to the non-UT EVO 1700. Readable values were empty or zero. Reading them did not affect pairing.
- **While a BLE client was connected, the UT did not advertise, and switching it on from off with the remote failed repeatedly.** Without a connection, it worked immediately (tested once). A controller that keeps a permanent connection may therefore block switching on with the remote.
- Earlier, the Xingzhe "paired remote" query (`24 FFFFFFFF`) got no answer, so the pairing ID cannot be read from the light.

## 9. Firmware

- The UT uses **Nordic Secure DFU** (`FE59`). Such updates are normally signed by the vendor, so custom or modified firmware via OTA is very unlikely to be accepted.
- The non-UT EVO 1700 instead uses an Alibaba AIS OTA service (`FEB3`/`FED4`–`FED8`). Its reference implementation only checks a CRC.
- Do not write to any DFU characteristic, and do not send `DF` on the Light Control Point.

---

## 10. Do-not-send list

| Target | Reason |
|---|---|
| `FE59` / `8EC90003` | Nordic DFU |
| `8CE5DD03` opcode `DF` | enters DFU mode |
| `8CE5DD03` opcodes `01`, `02`, `05`, `08`–`0B`, `24`, `DA` | untested; `02` changes the light type |
| `8CE5DD04` | untested |
| `FFE4`, `FFE6`, service `42820001` | unknown purpose |
| `A2 … BB` without a matching `AA` | changes the button modes |

---

## 11. Open questions

- Exact gesture to clear the pairing on the UT (manual: click + 3 s; other Magicshine manuals: 10 s).
- Does the light still accept BLE commands below 10 % battery (forced lowest level)?
- At which temperature does the light start to dim, and is the derating visible in the `8CE5DD02` intensity?
- Flash modes are not reported in `8CE5DD02`. Is there any other way to detect them over BLE?
- Does `2A19` report finer battery steps during a discharge?
- What do `A6 01` and the ack value `r` of `B6` mean?
- Maximum number of custom-mode slots (≥ 6 confirmed).
- Why did `AA` on the newly appended last slot block the button once?
- Is there a BLE command equivalent to a short button press ("next level")? None is known on the connection-based channels. The MJ-6558 broadcast is a candidate.
- Do Control Point commands work without `00`? What happens on a button press during BLE control?
- What does intensity above 50 % and on the high beam look like?
- What do `FFE2`–`FFE7` do?
- How is the MJ-6558 paired, and are `42820003`/`42820005` further pairing slots? What do the `2901` descriptors of service `42820001` say?
- Does a held BLE connection always block switching on with the remote?

---

## 12. Method and tools

- **Mac:** Python with [bleak](https://github.com/hbldh/bleak) for scanning, GATT dumps and controlled writes. A webcam measured wall brightness to detect light changes automatically.
- **iPhone:** Apple's Bluetooth logging profile plus PacketLogger to capture the official Magicshine app. A custom `.pklg` parser decoded the ATT traffic.
- **Karoo 3:** `adb`, read-only.

## 13. Sources and credits

- [lenne0815/karoo-magicshine-controls](https://github.com/lenne0815/karoo-magicshine-controls): EVO 1700 (non-UT) captures and discharge test
- [TimFourcode/evo1300](https://github.com/TimFourcode/evo1300): `FLAG_SAVE` observation, first use of `8CE5DD03` (HORI 1300)
- [m4jki/allty-1500s-control](https://github.com/m4jki/allty-1500s-control): `A2` as custom-mode add/delete with slots, `AE`/`AF` sensor commands
- [JaJaJim/KMagicWheeltopBlip](https://github.com/JaJaJim/KMagicWheeltopBlip): MJ-6558 remote advertising format
- [derstrassi/karoofirefly](https://github.com/derstrassi/karoofirefly), [JaJaJim/LightONKaroo](https://github.com/JaJaJim/LightONKaroo): Karoo integration and original Magicshine frames
- Xingzhe Bluetooth Light Profile: <https://developer.imxingzhe.com/docs/device/light/> (© Shanghai Da Bu Zi Duo Information Technology Co.; only the parts needed here are summarised)
