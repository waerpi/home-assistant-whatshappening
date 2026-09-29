<p align="center">
  <img src="custom_components/whatshappening/brand/logo@2x.png" alt="What&#8217;s happening next?" width="340">
</p>

<!-- The HACS badge says "custom" rather than "default" on purpose: this
     repository is installed as a custom repository. Switch it to
     `hacs-default-orange` once it is accepted into the default store. -->

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/hacs-custom-orange.svg?style=flat-square" alt="hacs"></a>
  <a href="https://github.com/waerpi/home-assistant-whatshappening/releases"><img src="https://img.shields.io/github/v/release/waerpi/home-assistant-whatshappening?style=flat-square" alt="release"></a>
  <a href="https://github.com/waerpi/home-assistant-whatshappening/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/waerpi/home-assistant-whatshappening/ci.yml?branch=main&style=flat-square" alt="build"></a>
  <a href="https://github.com/waerpi/home-assistant-whatshappening/blob/main/LICENSE"><img src="https://img.shields.io/github/license/waerpi/home-assistant-whatshappening?style=flat-square" alt="license"></a>
</p>

A weather forecast for your home: instead of looking back at what happened,
this Home Assistant integration shows a **timeline of the next few minutes** —
assembled from the sun, your calendars, schedules, timers, automations, travel
times and how your appliances behave.

```
In the next 30 minutes

🌅  Sunset                            in 12 min
💡  Outdoor lighting turns on         in 12 min
🌡  Living room likely 21.8 °C        in 30 min
🚗  Alex is expected home             in 18 min
🔌  Washing machine likely done       in 24 min
```

## What it looks at

| Source | Where the prediction comes from | Certain? |
| --- | --- | --- |
| 🌅 Sun | `sun.sun` (rise, set, dawn, dusk) | exact |
| 📅 Calendars | `calendar.get_events` for the chosen calendars | exact |
| 🗓 Schedules | `next_event` of `schedule.*` helpers | exact |
| ⏲ Timers | `finishes_at` of running `timer.*` helpers | exact |
| ⏰ `input_datetime` | the helper's point in time | exact |
| 💡 Automations | time and sun triggers from the automation config | exact, or likely when the automation has conditions |
| 🚗 Arrivals | a travel time sensor (Waze, Google Maps, HERE …) | estimate |
| 🔌 Appliances | a remaining-time sensor, otherwise power draw plus a typical cycle length | estimate |
| 🌡 Trends | linear extrapolation of numeric sensors | estimate |

Anything short of a hard commitment is phrased as a guess ("likely",
"expected") and shown in italics on the card.

## Languages

The integration is English by default and follows Home Assistant's configured
language. German is included; the card's own wording and the generated event
texts both switch with it:

```
Home Assistant set to German:   🌅  Sonnenuntergang        in 12 min
Home Assistant set to English:  🌅  Sunset                 in 12 min
```

Decimal separators follow the language too — `21.8 °C` in English, `21,8 °C`
in German.

Adding a language means adding one block to `CATALOG` in
`custom_components/whatshappening/localization.py` and one to `STRINGS` in
`frontend/whatshappening-card.js`. Missing keys fall back to English one by
one, so a partial translation is fine. The test suite checks that every
language covers the full set of keys and uses the same placeholders.

## Installation

### HACS (recommended)

This is a custom repository — it is not in the HACS default store (see
[Publishing to HACS](#publishing-to-hacs)), so it has to be added once:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=waerpi&repository=home-assistant-whatshappening&category=integration)

Or by hand:

1. HACS → Integrations → ⋮ → *Custom repositories*
2. Add `https://github.com/waerpi/home-assistant-whatshappening` as an *Integration*
3. Install "What's happening next?" and restart Home Assistant

### Manual

Copy `custom_components/whatshappening` into `<config>/custom_components/` and
restart Home Assistant.

## Setup

*Settings → Devices & Services → Add Integration → "What's happening next?"*

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=whatshappening)

The dialog asks for:

- **Look-ahead window** – how far ahead to look (default: 30 minutes)
- **Calendars** – which calendar entities to include
- **Sensors for trend prediction** – e.g. `sensor.living_room_temperature`
- **Travel time sensors** – sensors whose state is the number of minutes to get home
- **Appliance power sensors** – e.g. `sensor.washing_machine_power`
- **Remaining time sensors** – if the appliance reports one itself
- Toggles for sun, schedules, timers, automations and `input_datetime`

Everything can be changed later via *Configure*.

### Entities

| Entity | Meaning |
| --- | --- |
| `sensor.what_s_happening` | Number of expected events, with the full timeline in the `events` attribute |
| `sensor.what_s_happening_next_event` | Title of the next event, details in its attributes |

The `events` attribute is a list ordered by time:

```yaml
events:
  - key: sun:next_setting
    when: "2026-09-29T19:42:00+02:00"
    in_minutes: 12.0
    title: Sunset
    kind: sun
    icon: mdi:weather-sunset-down
    emoji: "🌅"
    confidence: 1.0
    certain: true
    entity_id: sun.sun
    detail: null
```

## The card

The Lovelace card is served and loaded by the integration itself — there is no
dashboard resource to register by hand.

```yaml
type: custom:whatshappening-card
entity: sensor.what_s_happening
# optional:
title: In the next 30 minutes   # otherwise derived from the window
max: 8                          # rows to show at most
show_relative: true             # "in 12 min" instead of "19:42"
```

Clicking a row opens the more-info dialog of the entity behind it.

If the card reports `Custom element doesn't exist` right after installing or
updating, the browser is still showing the page it had before the module was
registered — reload with Ctrl+Shift+R.

## How the estimates work

**Appliances.** If the appliance reports a remaining time, that value is used
directly. Otherwise it counts as running while its power draw is above the
threshold; short pauses within a cycle (heating, spinning) of up to five
minutes do not end the run. The finish time is the start plus the typical
cycle length.

**Trends.** A least-squares line is fitted through the readings of the last 45
minutes and extended to the end of the window. Changes below 0.3 units are not
reported at all, and the fit's r² decides how much the estimate is trusted.

**Arrivals.** A travel time sensor gives the minutes to get home. If a `person`
entity can be matched to the sensor by name, the event disappears once that
person is home.

**Automations.** `time` and `sun` triggers are read, including offsets and
references to `input_datetime` helpers. Disabled automations are skipped, and
an automation with conditions is reported as likely rather than certain.

## Development

```bash
pip install -r requirements_test.txt
pytest
```

The prediction maths (`predict.py`) and the text catalogue (`localization.py`)
deliberately have no Home Assistant imports, so the tests run without a full
Home Assistant install.

CI runs the tests, Home Assistant's `hassfest` manifest validation and the
HACS repository validation.

## License

MIT
