"""Tests for the event-text catalogue."""

from __future__ import annotations

import pytest
from conftest import load

localization = load("localization")


class TestNormalize:
    @pytest.mark.parametrize(
        ("language", "expected"),
        [
            ("de", "de"),
            ("de-DE", "de"),
            ("de_DE", "de"),
            ("DE", "de"),
            ("en-GB", "en"),
        ],
    )
    def test_regional_variants_collapse_to_the_base_language(self, language, expected):
        assert localization.normalize(language) == expected

    @pytest.mark.parametrize("language", [None, ""])
    def test_missing_language_defaults_to_english(self, language):
        assert localization.normalize(language) == "en"


class TestTranslate:
    def test_english_is_the_base(self):
        assert localization.translate("en", "sun.next_setting") == "Sunset"

    def test_german_is_translated(self):
        assert localization.translate("de", "sun.next_setting") == "Sonnenuntergang"

    def test_regional_variant_uses_its_base_language(self):
        assert localization.translate("de-CH", "sun.next_setting") == "Sonnenuntergang"

    def test_unknown_language_falls_back_to_english(self):
        assert localization.translate("ja", "sun.next_setting") == "Sunset"

    def test_placeholders_are_filled(self):
        assert (
            localization.translate("de", "appliance.done_estimated", name="Waschma")
            == "Waschma vermutlich fertig"
        )
        assert (
            localization.translate("en", "appliance.done_estimated", name="Washer")
            == "Washer likely done"
        )

    def test_unknown_key_returns_the_key_rather_than_raising(self):
        assert localization.translate("en", "nope.missing") == "nope.missing"

    def test_missing_placeholder_degrades_to_the_raw_template(self):
        assert localization.translate("en", "schedule.starts") == "{name} starts"

    def test_every_language_covers_the_full_english_catalogue(self):
        english = set(localization.CATALOG["en"])
        for language, catalogue in localization.CATALOG.items():
            missing = english - set(catalogue)
            assert not missing, f"{language} is missing {sorted(missing)}"

    def test_no_language_invents_keys_english_does_not_have(self):
        english = set(localization.CATALOG["en"])
        for language, catalogue in localization.CATALOG.items():
            extra = set(catalogue) - english
            assert not extra, f"{language} has stray keys {sorted(extra)}"

    def test_placeholders_match_across_languages(self):
        import re

        placeholders = lambda text: set(re.findall(r"{(\w+)}", text))  # noqa: E731
        for key, english in localization.CATALOG["en"].items():
            for language, catalogue in localization.CATALOG.items():
                assert placeholders(catalogue[key]) == placeholders(english), (
                    f"{language}:{key} uses different placeholders"
                )


class TestFormatNumber:
    @pytest.mark.parametrize(
        ("value", "language", "expected"),
        [
            (21.84, "en", "21.8"),
            (21.84, "de", "21,8"),
            (21.0, "en", "21.0"),
            (-3.27, "de", "-3,3"),
            (21.84, "fr", "21,8"),
            (21.84, "ja", "21.8"),
            (21.84, None, "21.8"),
        ],
    )
    def test_decimal_separator_follows_the_language(self, value, language, expected):
        assert localization.format_number(value, language) == expected
