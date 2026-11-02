# Magicshine EVO 1700 UT – Bluetooth LE documentation

Open, reverse-engineered documentation of the Bluetooth LE interface of the **Magicshine EVO 1700 UT** front light. It is meant for anyone who wants to control the light from a bike computer, a phone or their own code, and for anyone wondering why the battery always shows "100 %".

All results were measured on a real unit (firmware 1.0.0 / software 1.0.1) in November 2026, using a Mac, an iPhone and a Hammerhead Karoo 3.

> **Disclaimer.** This is not an official Magicshine document, and it is not affiliated with Magicshine. The interface is undocumented and may change with firmware updates. Writing to the light can change its stored modes, and one command (`DF` on the Light Control Point) puts it into firmware-update mode. Use at your own risk.

## Documents

| File | Language | Content |
|---|---|---|
| [`reference.md`](reference.md) | English | Technical reference: GATT database, both control protocols with all bytes, battery, controls, remote radio format, do-not-send list, open questions |
| [`erkenntnisse.md`](erkenntnisse.md) | German | Summary of all findings by topic, how they were obtained, corrected mistakes, notes for developers |
| [`anleitung-mitschnitt-apple.md`](anleitung-mitschnitt-apple.md) | German | How to inspect the light and capture the official Magicshine app with an iPhone and a Mac |

## Key findings

1. **Two BLE control paths.** The Magicshine channel (`FFE1`/`FFE0`, command `A2`) only stores *custom modes*. The light also implements the open **Xingzhe "Bluetooth Light Profile"** (`8CE5DD03`). It controls the light directly: **real off/on**, low/high beam, intensity and SOS. Every command is acknowledged within 40–130 ms, and the button modes stay untouched.
2. **Battery is reported in steps only**, matching the button LED: green 100–21 %, red 20–11 %, flashing red 10–1 %. This is why apps and bike computers jump from 100 % to 20 %.
3. **Custom firmware is practically impossible.** The light uses a Nordic SoC with signed Nordic Secure DFU.
4. **Existing Karoo extensions corrupt the button modes.** They send `A2 … BB` for every mode change, and also as "off", but never delete. Afterwards the button cycles only one mode.
5. **The Magicshine app keeps custom modes locally** and writes them back to the light every time it connects.
6. **The MJ-6558 remote ("FTR LightSync") is a BLE advertiser.** Its packets carry no ID, but the light stores the remote's Bluetooth address. Listening to the remote works; emulating it is practically impossible.

## Quick start: switching the light via BLE

```
1. Connect to the light (advertised name "M2-B0 EVO1700_UT").
2. Enable indications on 8CE5DD03-0A4D-11E9-AB14-D663BD873D93
   and notifications on 8CE5DD02-0A4D-11E9-AB14-D663BD873D93.
3. Write 00              -> indication 80 00 01   (request control)
4. Write 03 0F / 03 00   -> on / off
   Write 04 00 / 04 01   -> low beam / high beam
   Write 06 <0..100>     -> intensity in %
   Write 03 11           -> SOS
5. Every change (including button presses) arrives on 8CE5DD02:
   2F 00 01 <mode> <beam> <intensity>
```

Never send `DF` to `8CE5DD03`, and never write to the DFU service `FE59`. See [`reference.md`](reference.md), section 10.

## Kurzfassung auf Deutsch

Die EVO 1700 UT lässt sich über das offene Xingzhe-Protokoll (`8CE5DD03`) per Bluetooth **wirklich ein- und ausschalten**. Abblend/Fernlicht, Helligkeit und SOS gehen auch, ohne dass die Modi am Taster verändert werden. Der Magicshine-eigene Befehl `A2` legt dagegen nur „eigene Modi“ an. Genau deshalb hatten bisherige Karoo-Erweiterungen danach nur noch eine Stufe am Taster. Der Akku wird nur in den drei Stufen der LED gemeldet (100–21 / 20–11 / 10–1 %). Alle Details stehen in [`erkenntnisse.md`](erkenntnisse.md).

## Credits

This work builds on [lenne0815/karoo-magicshine-controls](https://github.com/lenne0815/karoo-magicshine-controls), [TimFourcode/evo1300](https://github.com/TimFourcode/evo1300), [m4jki/allty-1500s-control](https://github.com/m4jki/allty-1500s-control), [JaJaJim/KMagicWheeltopBlip](https://github.com/JaJaJim/KMagicWheeltopBlip), [derstrassi/karoofirefly](https://github.com/derstrassi/karoofirefly), [JaJaJim/LightONKaroo](https://github.com/JaJaJim/LightONKaroo) and the public [Xingzhe Bluetooth Light Profile](https://developer.imxingzhe.com/docs/device/light/). Magicshine manuals are summarised, not reproduced.
