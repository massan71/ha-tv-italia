/*
 * TV Italia card — guida TV per Home Assistant
 *
 *   type: custom:tv-italia-card
 *   title: Guida TV            # opzionale
 *   view: now                  # now | prime  (vista iniziale)
 *   show_next: true            # mostra il programma successivo
 *   entities:                  # opzionale: di default tutti i canali TV Italia
 *     - sensor.tv_rai1
 */
const CARD_VERSION = "1.0.1";

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

const hhmm = (iso) => {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit" });
};

class TvItaliaCard extends HTMLElement {
  static getStubConfig() {
    return { title: "Guida TV", view: "now", show_next: true };
  }

  setConfig(config) {
    this._config = { view: "now", show_next: true, ...config };
    this._view = this._config.view === "prime" ? "prime" : "now";
    this._sig = null;
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
  }

  getCardSize() {
    return 2 + this._entities().length;
  }

  set hass(hass) {
    this._hass = hass;
    const ents = this._entities();
    const sig = ents.map((id) => {
      const s = hass.states[id];
      return s ? `${s.state}|${s.attributes.progress}|${s.last_updated}` : id;
    }).join(";") + this._view;
    if (sig === this._sig) return;
    this._sig = sig;
    this._render();
  }

  _entities() {
    if (!this._hass) return [];
    if (Array.isArray(this._config.entities) && this._config.entities.length) {
      return this._config.entities.map((e) => (typeof e === "string" ? e : e.entity));
    }
    return Object.values(this._hass.states)
      .filter((s) => s.attributes && s.attributes.source === "tv_italia")
      .sort((a, b) => (a.attributes.channel_number || 999) - (b.attributes.channel_number || 999))
      .map((s) => s.entity_id);
  }

  _row(id) {
    const st = this._hass.states[id];
    if (!st) return `<div class="row missing">Entità non trovata: ${esc(id)}</div>`;
    const a = st.attributes;
    const logo = a.channel_logo
      ? `<img class="logo" src="${esc(a.channel_logo)}" alt="" loading="lazy" referrerpolicy="no-referrer">`
      : `<div class="logo badge">${esc(a.channel_number ?? "")}</div>`;
    const num = a.channel_number ? `<span class="num">${esc(a.channel_number)}</span>` : "";

    let body;
    if (st.state === "unavailable") {
      body = `<div class="title dim">Guida non disponibile</div>`;
    } else if (this._view === "prime") {
      const p = a.prime_time;
      body = p
        ? `<div class="title">${esc(p.title)}</div>
           <div class="meta">${hhmm(p.start)} – ${hhmm(p.end)}${p.subtitle ? " · " + esc(p.subtitle) : ""}</div>`
        : `<div class="title dim">Nessuna informazione</div>`;
    } else {
      const progress = Number.isFinite(a.progress) ? a.progress : 0;
      const next = this._config.show_next && a.next_title
        ? `<div class="next">Dopo, ${hhmm(a.next_start)}: ${esc(a.next_title)}</div>`
        : "";
      body = `<div class="title">${esc(st.state)}</div>
        <div class="meta">${a.start ? `${hhmm(a.start)} – ${hhmm(a.end)}` : ""}${
          a.remaining_minutes != null ? ` · ancora ${a.remaining_minutes} min` : ""}</div>
        <div class="bar"><div style="width:${progress}%"></div></div>${next}`;
    }

    return `<div class="row" data-entity="${esc(id)}" tabindex="0" role="button">
      ${logo}
      <div class="info">
        <div class="ch">${num}${esc(a.channel_name || a.friendly_name || id)}</div>
        ${body}
      </div>
    </div>`;
  }

  _render() {
    if (!this._hass || !this.shadowRoot) return;
    const ents = this._entities();
    const title = this._config.title ?? "Guida TV";
    const rows = ents.length
      ? ents.map((id) => this._row(id)).join("")
      : `<div class="empty">Nessun canale configurato. Aggiungi l'integrazione TV Italia.</div>`;

    this.shadowRoot.innerHTML = `
      <style>
        ha-card { overflow: hidden; }
        .head { display:flex; align-items:center; justify-content:space-between; padding:16px 16px 8px; gap:8px; }
        .head h2 { margin:0; font-size:1.25rem; font-weight:500; color:var(--primary-text-color); }
        .tabs { display:flex; background:var(--secondary-background-color); border-radius:999px; padding:3px; }
        .tabs button { border:0; background:transparent; color:var(--secondary-text-color); font:inherit; font-size:.85rem;
          padding:4px 12px; border-radius:999px; cursor:pointer; }
        .tabs button.on { background:var(--primary-color); color:var(--text-primary-color, #fff); }
        .list { padding:0 8px 8px; }
        .row { display:flex; gap:12px; padding:10px 8px; border-radius:12px; cursor:pointer; align-items:flex-start; }
        .row:hover, .row:focus-visible { background:var(--secondary-background-color); outline:none; }
        .row + .row { border-top:1px solid var(--divider-color); }
        .logo { width:48px; height:36px; object-fit:contain; flex:none; border-radius:6px; }
        .badge { display:flex; align-items:center; justify-content:center; background:var(--primary-color);
          color:var(--text-primary-color, #fff); font-weight:600; }
        .info { flex:1; min-width:0; }
        .ch { font-size:.78rem; color:var(--secondary-text-color); text-transform:uppercase; letter-spacing:.04em; }
        .num { display:inline-block; min-width:1.6em; margin-right:6px; padding:0 4px; text-align:center; border-radius:4px;
          background:var(--secondary-background-color); color:var(--primary-text-color); font-weight:600; }
        .title { font-weight:500; color:var(--primary-text-color); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; margin-top:2px; }
        .dim { color:var(--secondary-text-color); font-weight:400; }
        .meta, .next { font-size:.8rem; color:var(--secondary-text-color); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
        .next { margin-top:4px; }
        .bar { height:4px; border-radius:2px; background:var(--divider-color); margin-top:6px; overflow:hidden; }
        .bar > div { height:100%; background:var(--primary-color); }
        .empty, .missing { padding:16px; color:var(--secondary-text-color); }
      </style>
      <ha-card>
        <div class="head">
          <h2>${esc(title)}</h2>
          <div class="tabs">
            <button data-view="now" class="${this._view === "now" ? "on" : ""}">In onda</button>
            <button data-view="prime" class="${this._view === "prime" ? "on" : ""}">Stasera</button>
          </div>
        </div>
        <div class="list">${rows}</div>
      </ha-card>`;

    this.shadowRoot.querySelectorAll(".tabs button").forEach((b) =>
      b.addEventListener("click", (ev) => {
        ev.stopPropagation();
        this._view = b.dataset.view;
        this._sig = null;
        this._render();
      })
    );
    this.shadowRoot.querySelectorAll(".row[data-entity]").forEach((r) => {
      const open = () =>
        this.dispatchEvent(new CustomEvent("hass-more-info", {
          detail: { entityId: r.dataset.entity }, bubbles: true, composed: true,
        }));
      r.addEventListener("click", open);
      r.addEventListener("keydown", (e) => (e.key === "Enter" || e.key === " ") && open());
    });
  }
}

if (!customElements.get("tv-italia-card")) {
  customElements.define("tv-italia-card", TvItaliaCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "tv-italia-card",
    name: "TV Italia",
    description: "Guida ai canali TV italiani: in onda ora e prima serata.",
    preview: true,
  });
  console.info(`%c TV-ITALIA-CARD %c ${CARD_VERSION} `, "background:#0b5;color:#fff", "background:#333;color:#fff");
}
