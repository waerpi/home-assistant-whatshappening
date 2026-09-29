# Was passiert gleich? 🔮

Ein Wetterbericht für dein Zuhause: statt zurückzuschauen, was passiert ist,
zeigt diese Home-Assistant-Integration eine **Timeline der nächsten Minuten** —
zusammengesetzt aus Sonnenstand, Kalendern, Zeitplänen, Timern, Automationen,
Fahrzeiten und dem Verhalten deiner Geräte.

```
In den nächsten 30 Minuten

🌅  Sonnenuntergang                      in 12 min
💡  Außenbeleuchtung wird aktiviert      in 12 min
🌡  Wohnzimmer vermutlich 21,8 °C        in 30 min
🚗  Bartu kommt voraussichtlich nach Hause   in 18 min
🔌  Waschmaschine vermutlich fertig      in 24 min
```

## Was ausgewertet wird

| Quelle | Woher die Vorhersage kommt | Sicher? |
| --- | --- | --- |
| 🌅 Sonne | `sun.sun` (Auf-/Untergang, Dämmerung) | exakt |
| 📅 Kalender | `calendar.get_events` für die gewählten Kalender | exakt |
| 🗓 Zeitpläne | `next_event` der `schedule.*`-Helfer | exakt |
| ⏲ Timer | `finishes_at` laufender `timer.*` | exakt |
| ⏰ `input_datetime` | Zeitpunkt des Helfers | exakt |
| 💡 Automationen | Zeit- und Sonnen-Trigger aus der Automations-Config | exakt bzw. wahrscheinlich, wenn Bedingungen enthalten sind |
| 🚗 Ankunft | Fahrzeit-Sensor (Waze, Google Maps, HERE …) | Schätzung |
| 🔌 Geräte | Restlaufzeit-Sensor, sonst Leistungsaufnahme + typische Programmdauer | Schätzung |
| 🌡 Trends | lineare Extrapolation numerischer Sensoren | Schätzung |

Alles, was keine harte Zusage ist, wird im Text als *vermutlich* bzw.
*voraussichtlich* gekennzeichnet und in der Karte kursiv dargestellt.

## Installation

### HACS (empfohlen)

1. HACS → Integrationen → ⋮ → *Benutzerdefinierte Repositories*
2. `https://github.com/waerpi/home-assistant-whatshappening` als *Integration* hinzufügen
3. „Was passiert gleich?" installieren und Home Assistant neu starten

### Manuell

Den Ordner `custom_components/whatshappening` nach `<config>/custom_components/`
kopieren und Home Assistant neu starten.

## Einrichtung

*Einstellungen → Geräte & Dienste → Integration hinzufügen → „Was passiert gleich?"*

Im Dialog legst du fest:

- **Vorschau-Zeitraum** – wie weit nach vorn geschaut wird (Standard: 30 Minuten)
- **Kalender** – welche Kalender-Entitäten einbezogen werden
- **Sensoren für Trend-Vorhersage** – z. B. `sensor.wohnzimmer_temperatur`
- **Fahrzeit-Sensoren** – Sensoren, deren Zustand die Minuten bis nach Hause ist
- **Leistungssensoren von Geräten** – z. B. `sensor.waschmaschine_power`
- **Restlaufzeit-Sensoren** – falls das Gerät selbst eine Restzeit meldet
- Schalter für Sonne, Zeitpläne, Timer, Automationen und `input_datetime`

Alle Werte sind später über *Konfigurieren* änderbar.

### Entitäten

| Entität | Bedeutung |
| --- | --- |
| `sensor.was_passiert_gleich` | Anzahl der erwarteten Ereignisse, komplette Timeline im Attribut `events` |
| `sensor.was_passiert_gleich_nachstes_ereignis` | Titel des nächsten Ereignisses, Details in den Attributen |

Das Attribut `events` ist eine nach Zeit sortierte Liste:

```yaml
events:
  - key: sun:next_setting
    when: "2026-09-29T19:42:00+02:00"
    in_minutes: 12.0
    title: Sonnenuntergang
    kind: sun
    icon: mdi:weather-sunset-down
    emoji: "🌅"
    confidence: 1.0
    certain: true
    entity_id: sun.sun
    detail: null
```

## Die Karte

Die Lovelace-Karte wird von der Integration selbst ausgeliefert und geladen —
es muss keine Ressource von Hand eingetragen werden.

```yaml
type: custom:whatshappening-card
entity: sensor.was_passiert_gleich
# optional:
title: In den nächsten 30 Minuten   # sonst aus dem Zeitraum abgeleitet
max: 8                              # maximal angezeigte Zeilen
show_relative: true                 # "in 12 min" statt "19:42"
```

Ein Klick auf eine Zeile öffnet den Dialog der zugehörigen Entität.

## Wie die Schätzungen funktionieren

**Geräte.** Meldet das Gerät eine Restlaufzeit, wird sie direkt genutzt.
Sonst gilt es als laufend, sobald die Leistungsaufnahme über der Schwelle
liegt; kurze Pausen im Programm (Heizen, Schleudern) von bis zu fünf Minuten
beenden den Lauf nicht. Das Ende ergibt sich aus Startzeitpunkt plus
typischer Programmdauer.

**Trends.** Über die Messwerte der letzten 45 Minuten wird eine
Ausgleichsgerade gelegt und auf das Ende des Zeitraums verlängert. Liegt die
Änderung unter 0,3 Einheiten, taucht sie gar nicht erst auf; das
Bestimmtheitsmaß der Geraden entscheidet, wie sicher die Angabe gilt.

**Ankunft.** Ein Fahrzeit-Sensor liefert die Minuten bis nach Hause. Lässt
sich dem Sensor über den Namen eine `person`-Entität zuordnen, wird das
Ereignis unterdrückt, sobald die Person zu Hause ist.

**Automationen.** Ausgelesen werden `time`- und `sun`-Trigger inklusive
Offsets und Verweisen auf `input_datetime`-Helfer. Deaktivierte Automationen
werden übersprungen; enthält eine Automation Bedingungen, gilt das Ereignis
als wahrscheinlich statt sicher.

## Entwicklung

```bash
pip install -r requirements_test.txt
pytest
```

## Lizenz

MIT
