/**
 * "What's happening next?" — a timeline of the events expected in the next
 * few minutes, read from the sensor the integration provides.
 *
 * Usage:
 *   type: custom:whatshappening-card
 *   entity: sensor.what_s_happening
 *   title: In the next 30 minutes   # optional, derived when omitted
 *   max: 8                          # optional, rows to show
 *   show_relative: true             # optional, "in 12 min" vs "19:42"
 *
 * Event titles arrive already translated from the integration; the strings
 * below are the card's own, and follow the same Home Assistant language.
 */

const STRINGS = {
  en: {
    heading: "What's happening next?",
    horizon: (minutes) => `In the next ${minutes} minutes`,
    empty: "Nothing planned in this window.",
    missing: (entity) => `Entity <code>${entity}</code> not found.`,
    config: "Please set an entity, e.g. sensor.what_s_happening",
    now: "now",
    minutes: (value) => `in ${value} min`,
    hours: (value) => `in ${value} h`,
    hoursMinutes: (hours, minutes) => `in ${hours} h ${minutes} min`,
    cardName: "What's happening next?",
    cardDescription: "Timeline of the events expected in the next minutes",
  },
  de: {
    heading: "Was passiert gleich?",
    horizon: (minutes) => `In den nächsten ${minutes} Minuten`,
    empty: "Nichts Geplantes in diesem Zeitraum.",
    missing: (entity) => `Entität <code>${entity}</code> nicht gefunden.`,
    config: "Bitte eine entity angeben, z. B. sensor.what_s_happening",
    now: "jetzt",
    minutes: (value) => `in ${value} min`,
    hours: (value) => `in ${value} Std`,
    hoursMinutes: (hours, minutes) => `in ${hours} Std ${minutes} min`,
    cardName: "Was passiert gleich?",
    cardDescription: "Timeline der Ereignisse in den nächsten Minuten",
  },
};

/** Falls back to English key by key, so a partial translation still works. */
function strings(language) {
  const code = String(language || "en").replace("_", "-").split("-")[0].toLowerCase();
  return { ...STRINGS.en, ...(STRINGS[code] || {}) };
}

const STYLES = `
  ha-card {
    padding: 16px;
  }
  .header {
    font-size: 1.1rem;
    font-weight: 500;
    margin-bottom: 12px;
    color: var(--primary-text-color);
  }
  .empty {
    color: var(--secondary-text-color);
    padding: 4px 0 8px;
  }
  ul {
    list-style: none;
    margin: 0;
    padding: 0;
  }
  li {
    display: grid;
    grid-template-columns: 28px 1fr auto;
    align-items: baseline;
    gap: 10px;
    padding: 8px 0;
    border-top: 1px solid var(--divider-color);
  }
  li:first-child {
    border-top: none;
  }
  li.clickable {
    cursor: pointer;
  }
  .emoji {
    font-size: 1.2rem;
    line-height: 1.2;
    text-align: center;
  }
  .title {
    color: var(--primary-text-color);
    overflow-wrap: anywhere;
  }
  .detail {
    display: block;
    font-size: 0.8rem;
    color: var(--secondary-text-color);
  }
  .when {
    color: var(--secondary-text-color);
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }
  .soon {
    color: var(--primary-color);
    font-weight: 500;
  }
  .uncertain .title {
    font-style: italic;
  }
`;

class WhatsHappeningCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._timer = null;
  }

  setConfig(config) {
    if (!config || !config.entity) {
      throw new Error(strings(this._hass?.locale?.language).config);
    }
    this._config = {
      max: 10,
      show_relative: true,
      ...config,
    };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    const events = this._events();
    return 1 + Math.min(events.length, this._config?.max ?? 10);
  }

  static getStubConfig(hass) {
    const entity = Object.keys(hass.states).find(
      (id) => id.startsWith("sensor.") && hass.states[id].attributes.events
    );
    return { entity: entity || "sensor.what_s_happening" };
  }

  connectedCallback() {
    // Relative times go stale on their own, so re-render on a slow tick.
    this._timer = window.setInterval(() => this._render(), 15000);
  }

  disconnectedCallback() {
    if (this._timer) {
      window.clearInterval(this._timer);
      this._timer = null;
    }
  }

  // --- data ------------------------------------------------------------

  _state() {
    if (!this._hass || !this._config) return null;
    return this._hass.states[this._config.entity] || null;
  }

  _events() {
    const state = this._state();
    if (!state) return [];
    const events = state.attributes.events;
    return Array.isArray(events) ? events : [];
  }

  // --- rendering -------------------------------------------------------

  _render() {
    if (!this._config || !this.shadowRoot) return;

    const state = this._state();
    if (!this._hass) return;

    const text = strings(this._hass.locale?.language);

    if (!state) {
      this._paint(
        `<div class="empty">${text.missing(this._config.entity)}</div>`,
        this._config.title || text.heading
      );
      return;
    }

    const horizon = state.attributes.horizon_minutes;
    const heading =
      this._config.title ||
      (horizon ? text.horizon(horizon) : text.heading);

    const events = this._events().slice(0, this._config.max);
    if (events.length === 0) {
      this._paint(`<div class="empty">${text.empty}</div>`, heading);
      return;
    }

    const rows = events.map((event) => this._row(event)).join("");
    this._paint(`<ul>${rows}</ul>`, heading);
    this._bindRows(events);
  }

  _row(event) {
    const classes = ["row"];
    if (event.certain === false) classes.push("uncertain");
    if (event.entity_id) classes.push("clickable");

    const when = this._formatWhen(event);
    const soon = event.in_minutes <= 5 ? " soon" : "";
    const detail = event.detail
      ? `<span class="detail">${escapeHtml(event.detail)}</span>`
      : "";

    return `
      <li class="${classes.join(" ")}">
        <span class="emoji">${escapeHtml(event.emoji || "•")}</span>
        <span class="title">${escapeHtml(event.title)}${detail}</span>
        <span class="when${soon}">${escapeHtml(when)}</span>
      </li>`;
  }

  _formatWhen(event) {
    const when = new Date(event.when);
    if (!this._config.show_relative) {
      return when.toLocaleTimeString(this._locale(), {
        hour: "2-digit",
        minute: "2-digit",
      });
    }

    const text = strings(this._locale());
    const minutes = Math.round((when.getTime() - Date.now()) / 60000);
    if (minutes <= 0) return text.now;
    if (minutes < 60) return text.minutes(minutes);

    const hours = Math.floor(minutes / 60);
    const rest = minutes % 60;
    return rest ? text.hoursMinutes(hours, rest) : text.hours(hours);
  }

  _locale() {
    return this._hass?.locale?.language || "en";
  }

  _paint(body, heading) {
    this.shadowRoot.innerHTML = `
      <style>${STYLES}</style>
      <ha-card>
        <div class="header">${escapeHtml(heading)}</div>
        ${body}
      </ha-card>`;
  }

  _bindRows(events) {
    const rows = this.shadowRoot.querySelectorAll("li");
    rows.forEach((row, index) => {
      const entityId = events[index]?.entity_id;
      if (!entityId) return;
      row.addEventListener("click", () => {
        this.dispatchEvent(
          new CustomEvent("hass-more-info", {
            detail: { entityId },
            bubbles: true,
            composed: true,
          })
        );
      });
    });
  }
}

function escapeHtml(value) {
  return String(value ?? "").replace(
    /[&<>"']/g,
    (character) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      })[character]
  );
}

if (!customElements.get("whatshappening-card")) {
  customElements.define("whatshappening-card", WhatsHappeningCard);
}

window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === "whatshappening-card")) {
  window.customCards.push({
    type: "whatshappening-card",
    name: STRINGS.en.cardName,
    description: STRINGS.en.cardDescription,
    preview: false,
  });
}
