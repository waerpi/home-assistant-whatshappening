"""Phrasing for the generated event texts.

Event titles are built at runtime from live entity names, so they cannot
live in the regular `translations/` files — those only cover static keys.
This catalogue fills that gap: English is the base, every other language
falls back to it key by key, so a partial translation degrades to English
rather than to a missing string.

Deliberately free of Home Assistant imports, which keeps it unit testable.
"""

from __future__ import annotations

DEFAULT_LANGUAGE = "en"

CATALOG: dict[str, dict[str, str]] = {
    "en": {
        "sun.next_rising": "Sunrise",
        "sun.next_setting": "Sunset",
        "sun.next_dawn": "Dawn",
        "sun.next_dusk": "Dusk",
        "sun.next_noon": "Solar noon",
        "calendar.untitled": "Appointment",
        "schedule.starts": "{name} starts",
        "schedule.ends": "{name} ends",
        "timer.finished": "{name} finished",
        "automation.detail": "Automation",
        "presence.arriving": "{name} is expected home",
        "presence.detail": "{minutes} min away",
        "appliance.done": "{name} done",
        "appliance.done_estimated": "{name} likely done",
        "appliance.detail_remaining": "from its remaining time",
        "appliance.detail_estimated": "estimated from runtime",
        "trend.prediction": "{name} likely {value}",
        "trend.detail_current": "currently {value}",
    },
    "de": {
        "sun.next_rising": "Sonnenaufgang",
        "sun.next_setting": "Sonnenuntergang",
        "sun.next_dawn": "Morgendämmerung",
        "sun.next_dusk": "Abenddämmerung",
        "sun.next_noon": "Sonnenhöchststand",
        "calendar.untitled": "Termin",
        "schedule.starts": "{name} startet",
        "schedule.ends": "{name} endet",
        "timer.finished": "{name} abgelaufen",
        "automation.detail": "Automation",
        "presence.arriving": "{name} kommt voraussichtlich nach Hause",
        "presence.detail": "{minutes} min Fahrzeit",
        "appliance.done": "{name} fertig",
        "appliance.done_estimated": "{name} vermutlich fertig",
        "appliance.detail_remaining": "laut Restlaufzeit",
        "appliance.detail_estimated": "geschätzt aus der Laufzeit",
        "trend.prediction": "{name} vermutlich {value}",
        "trend.detail_current": "aktuell {value}",
    },
}

# Languages that write 1.5 as "1,5". Home Assistant has no public helper for
# this, and pulling in `locale` would depend on what the host has installed.
COMMA_DECIMAL_LANGUAGES = frozenset(
    {
        "bg", "ca", "cs", "da", "de", "el", "es", "et", "eu", "fi", "fr", "gl",
        "hr", "hu", "id", "is", "it", "lb", "lt", "lv", "nb", "nl", "nn", "no",
        "pl", "pt", "ro", "ru", "sk", "sl", "sr", "sv", "tr", "uk", "vi",
    }
)


def normalize(language: str | None) -> str:
    """`de-DE` and `DE` both mean `de`."""
    if not language:
        return DEFAULT_LANGUAGE
    return language.replace("_", "-").split("-", 1)[0].lower()


def translate(language: str | None, key: str, **placeholders: object) -> str:
    """Look `key` up, falling back to English and finally to the key itself."""
    code = normalize(language)
    template = CATALOG.get(code, {}).get(key)
    if template is None:
        template = CATALOG[DEFAULT_LANGUAGE].get(key)
    if template is None:
        return key

    try:
        return template.format(**placeholders)
    except (KeyError, IndexError):
        # A catalogue entry asking for a placeholder the caller did not pass
        # is a bug, but a half-rendered timeline beats a broken one.
        return template


def format_number(value: float, language: str | None = None) -> str:
    """One decimal, with the separator the language expects."""
    formatted = f"{value:.1f}"
    if normalize(language) in COMMA_DECIMAL_LANGUAGES:
        return formatted.replace(".", ",")
    return formatted
