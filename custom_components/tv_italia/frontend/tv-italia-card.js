/*
 * TV Italia card — guida TV compatta e scorrevole per Home Assistant
 *
 *   type: custom:tv-italia-card
 *   title: Guida TV          # opzionale, "" per nasconderlo
 *   height: 320              # altezza dell'elenco in px (scorre se i canali sono di piu')
 *   tabs: [now, next]        # schede: now (In onda) | next (A seguire) | prime (Stasera)
 *   view: now                # scheda iniziale
 *   show_next: false         # mostra anche il programma successivo
 *   show_logo: true          # mostra i loghi dei canali
 *   platform: all            # all | dtt (digitale terrestre) | sky
 *   filters: true            # filtri per genere (Film, Serie, Sport, ...) e Preferiti
 *   show_star: true          # stellina per i canali preferiti
 *   favorites_first: true    # preferiti in cima all'elenco
 *   entities:                # opzionale: di default tutti i canali TV Italia
 *     - sensor.tv_rai1
 */
const CARD_VERSION = "1.6.0";

const TAB_LABELS = { now: "In onda", next: "A seguire", prime: "Stasera" };

const FILTERS = [
  ["all", "Tutti"], ["fav", "★ Preferiti"], ["film", "Film"], ["serie", "Serie"], ["sport", "Sport"],
  ["news", "Notizie"], ["kids", "Bambini"], ["docs", "Documentari"], ["show", "Show"],
];

// "tra 5 min", "tra 1 h 20 min"
const fromNow = (iso) => {
  if (!iso) return "";
  const min = Math.max(0, Math.round((new Date(iso) - Date.now()) / 60000));
  if (min < 1) return "ora";
  if (min < 60) return `tra ${min} min`;
  const h = Math.floor(min / 60), m = min % 60;
  return `tra ${h} h${m ? ` ${m} min` : ""}`;
};

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

const hhmm = (iso) =>
  iso ? new Date(iso).toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit" }) : "";

const STYLE = `
  :host { display:block; }
  ha-card { overflow:hidden; display:flex; flex-direction:column; }
  .head { display:flex; align-items:center; justify-content:space-between; gap:8px; padding:10px 12px 8px; }
  .head h2 { margin:0; font-size:1rem; font-weight:500; color:var(--primary-text-color);
    white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .tabs { display:flex; flex:none; margin-left:auto; background:var(--secondary-background-color); border-radius:999px; padding:2px; }
  .tabs button { border:0; background:transparent; color:var(--secondary-text-color); font:inherit; font-size:.75rem;
    padding:3px 10px; border-radius:999px; cursor:pointer; }
  .tabs button.on { background:var(--primary-color); color:var(--text-primary-color, #fff); }
  .list { overflow-y:auto; overscroll-behavior:contain; scrollbar-width:thin;
    scrollbar-color:var(--scrollbar-thumb-color, var(--divider-color)) transparent;
    border-top:1px solid var(--divider-color); }
  .list::-webkit-scrollbar { width:6px; }
  .list::-webkit-scrollbar-thumb { background:var(--divider-color); border-radius:3px; }
  .row { position:relative; display:flex; align-items:center; gap:10px; padding:6px 12px 8px; cursor:pointer; }
  .row + .row { border-top:1px solid var(--divider-color); }
  .row:hover, .row:focus-visible { background:var(--secondary-background-color); outline:none; }
  /* Fondo scuro fisso: molti loghi sono bianchi e sparirebbero sul tema chiaro */
  .logo { width:40px; height:28px; flex:none; box-sizing:border-box; padding:3px 4px; border-radius:6px;
    background:#263238; object-fit:contain; }
  .badge { display:flex; align-items:center; justify-content:center; padding:0 2px; font-size:.62rem; font-weight:600;
    line-height:1; text-align:center; color:#fff; overflow:hidden; }
  .info { flex:1; min-width:0; }
  .top { display:flex; align-items:baseline; gap:6px; font-size:.72rem; color:var(--secondary-text-color); line-height:1.3; }
  .ch { flex:1; min-width:0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .ch b { font-weight:600; color:var(--primary-text-color); margin-right:4px; }
  .time { flex:none; font-variant-numeric:tabular-nums; }
  .title { font-size:.9rem; font-weight:500; line-height:1.3; color:var(--primary-text-color);
    white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .dim { color:var(--secondary-text-color); font-weight:400; }
  .next { font-size:.72rem; color:var(--secondary-text-color); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .bar { position:absolute; left:12px; right:12px; bottom:3px; height:2px; border-radius:1px; background:var(--divider-color); }
  .bar > div { height:100%; border-radius:1px; background:var(--primary-color); }
  .empty { padding:16px 12px; color:var(--secondary-text-color); font-size:.9rem; }
  .chips { display:flex; gap:6px; overflow-x:auto; padding:0 12px 8px; scrollbar-width:none; }
  .chips::-webkit-scrollbar { display:none; }
  .chips:empty { display:none; }
  .chip { flex:none; border:1px solid var(--divider-color); background:transparent; color:var(--primary-text-color);
    font:inherit; font-size:.75rem; padding:2px 10px; border-radius:999px; cursor:pointer; white-space:nowrap; }
  .chip.on { background:var(--primary-color); border-color:var(--primary-color); color:var(--text-primary-color, #fff); }
  .star { flex:none; border:0; background:none; padding:4px 2px 4px 6px; margin:-4px -4px -4px 0; cursor:pointer;
    font-size:1.15rem; line-height:1; color:var(--disabled-text-color, #bdbdbd); }
  .star.on { color:#f5b301; }
`;

class TvItaliaCard extends HTMLElement {
  static getStubConfig() {
    return { title: "Guida TV", height: 320, tabs: ["now", "next"] };
  }

  setConfig(config) {
    const tabs = config.tabs ?? ["now", "next"];
    if (!Array.isArray(tabs) || !tabs.length || tabs.some((t) => !TAB_LABELS[t])) {
      throw new Error("tabs deve essere un elenco di: now, next, prime");
    }
    if (config.view && !tabs.includes(config.view)) {
      throw new Error(`view deve essere una delle schede: ${tabs.join(", ")}`);
    }
    if (config.platform && !["all", "dtt", "sky"].includes(config.platform)) {
      throw new Error("platform deve essere 'all', 'dtt' oppure 'sky'");
    }
    this._config = {
      title: "Guida TV", height: 320, show_next: false, show_logo: true, platform: "all",
      filters: true, show_star: true, favorites_first: true, ...config, tabs,
    };
    this._filter = this._filter || "all";
    this._config.view = config.view ?? tabs[0];
    this._view = this._config.view;
    this._sig = null;
    this._built = false;
    if (this._hass) this._update();
  }

  getCardSize() {
    const h = parseInt(this._config?.height, 10) || 320;
    return Math.ceil((h + 44) / 50);
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6, rows: "auto" };
  }

  set hass(hass) {
    this._hass = hass;
    this._update();
  }

  _entities() {
    if (!this._hass) return [];
    if (Array.isArray(this._config.entities) && this._config.entities.length) {
      return this._config.entities.map((e) => (typeof e === "string" ? e : e.entity));
    }
    return Object.values(this._hass.states)
      .filter((s) => s.attributes && s.attributes.source === "tv_italia")
      .filter((s) => this._config.platform === "all"
        || (s.attributes.channel_platform || "dtt") === this._config.platform)
      .sort((a, b) => (this._config.favorites_first ? (b.attributes.favorite ? 1 : 0) - (a.attributes.favorite ? 1 : 0) : 0)
        || (a.attributes.channel_number || 999) - (b.attributes.channel_number || 999))
      .map((s) => s.entity_id);
  }

  // Genere del programma mostrato nella scheda attuale
  _genre(a) {
    if (this._view === "next") return ((a.upcoming && a.upcoming[0]) || {}).genre;
    if (this._view === "prime") return (a.prime_time || {}).genre;
    return a.genre;
  }

  _matches(id) {
    const a = this._hass.states[id]?.attributes;
    if (!a || this._filter === "all") return true;
    if (this._filter === "fav") return !!a.favorite;
    return this._genre(a) === this._filter;
  }

  _renderChips(ents) {
    if (!this._config.filters) return;
    const attrs = ents.map((id) => this._hass.states[id]?.attributes).filter(Boolean);
    const count = (f) => f === "all" ? attrs.length
      : f === "fav" ? attrs.filter((a) => a.favorite).length
      : attrs.filter((a) => this._genre(a) === f).length;
    // Mostra solo i filtri con almeno un canale (e quello selezionato)
    const shown = FILTERS.filter(([f]) => f === "all" || f === this._filter || count(f) > 0);
    this._chips.innerHTML = shown.length > 1
      ? shown.map(([f, label]) => `<button class="chip${f === this._filter ? " on" : ""}" data-filter="${f}">${label}</button>`).join("")
      : "";
  }

  _build() {
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    const height = this._config.height;
    const h = typeof height === "number" || /^\d+$/.test(String(height)) ? `${height}px` : height;
    const title = this._config.title;
    this.shadowRoot.innerHTML = `
      <style>${STYLE}</style>
      <ha-card>
        <div class="head">
          ${title ? `<h2>${esc(title)}</h2>` : ""}
          ${this._config.tabs.length > 1 ? `<div class="tabs">${this._config.tabs
            .map((t) => `<button data-view="${t}">${TAB_LABELS[t]}</button>`).join("")}</div>` : ""}
        </div>
        <div class="chips"></div>
        <div class="list" style="max-height:${esc(h)}"></div>
      </ha-card>`;
    this._list = this.shadowRoot.querySelector(".list");
    this._chips = this.shadowRoot.querySelector(".chips");
    this._chips.addEventListener("click", (e) => {
      const chip = e.target.closest(".chip");
      if (!chip || chip.dataset.filter === this._filter) return;
      this._filter = chip.dataset.filter;
      this._sig = null;
      this._update();
      this._list.scrollTop = 0;
    });

    this.shadowRoot.querySelectorAll(".tabs button").forEach((b) =>
      b.addEventListener("click", (ev) => {
        ev.stopPropagation();
        if (this._view === b.dataset.view) return;
        this._view = b.dataset.view;
        this._sig = null;
        this._update();
        this._list.scrollTop = 0;
      })
    );
    // Un solo listener per tutte le righe (le righe vengono ricreate)
    const open = (row) =>
      row && this.dispatchEvent(new CustomEvent("hass-more-info", {
        detail: { entityId: row.dataset.entity }, bubbles: true, composed: true,
      }));
    this._list.addEventListener("click", (e) => {
      const star = e.target.closest(".star");
      if (star) {
        e.stopPropagation();
        const on = !star.classList.contains("on");
        star.classList.toggle("on", on);  // risposta immediata, poi conferma dal server
        star.textContent = on ? "★" : "☆";
        this._hass.callService("tv_italia", "set_favorite", { entity_id: star.dataset.star, favorite: on });
        return;
      }
      open(e.target.closest(".row"));
    });
    this._list.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(e.target.closest(".row")); }
    });
    this._built = true;
  }

  _update() {
    if (!this._hass || !this._config) return;
    const ents = this._entities();
    const sig = this._view + this._filter + ents.map((id) => this._hass.states[id]?.last_updated ?? id).join();
    if (this._built && sig === this._sig) return;
    this._sig = sig;
    if (!this._built) this._build();

    this.shadowRoot.querySelectorAll(".tabs button").forEach((b) =>
      b.classList.toggle("on", b.dataset.view === this._view));

    this._renderChips(ents);
    const shown = ents.filter((id) => this._matches(id));

    // Aggiorna solo l'elenco mantenendo la posizione di scorrimento
    const scroll = this._list.scrollTop;
    this._list.innerHTML = shown.length
      ? shown.map((id) => this._row(id)).join("")
      : `<div class="empty">${ents.length
        ? (this._filter === "fav" ? "Nessun preferito: tocca ☆ accanto a un canale." : "Nessun canale con questo genere.")
        : "Nessun canale. Aggiungi l'integrazione TV Italia."}</div>`;
    this._list.scrollTop = scroll;
    // Se un logo non si carica, al suo posto mostra il nome del canale
    this._list.querySelectorAll("img.logo").forEach((img) =>
      img.addEventListener("error", () => {
        const badge = document.createElement("div");
        badge.className = "logo badge";
        badge.textContent = img.dataset.name;
        img.replaceWith(badge);
      }, { once: true }));
  }

  _row(id) {
    const st = this._hass.states[id];
    if (!st) return `<div class="empty">Entità non trovata: ${esc(id)}</div>`;
    const a = st.attributes;
    const num = a.channel_number ? String(a.channel_number).padStart(2, "0") : "";

    let logo = "";
    if (this._config.show_logo) {
      logo = a.channel_logo
        ? `<img class="logo" src="${esc(a.channel_logo)}" alt="" loading="lazy" referrerpolicy="no-referrer"
             data-name="${esc((a.channel_name || "TV").slice(0, 7))}">`
        : `<div class="logo badge">${esc((a.channel_name || "TV").slice(0, 7))}</div>`;
    }

    let time = "", title, extra = "", bar = "";
    if (st.state === "unavailable" || st.state === "unknown") {
      title = `<div class="title dim">Guida non disponibile</div>`;
    } else if (this._view === "next") {
      const n = (a.upcoming && a.upcoming[0]) || (a.next_title ? { title: a.next_title, start: a.next_start } : null);
      time = n ? `${hhmm(n.start)} · ${fromNow(n.start)}` : "";
      title = n
        ? `<div class="title">${esc(n.title)}</div>`
        : `<div class="title dim">Nessuna informazione</div>`;
      if (n && this._config.show_next && a.upcoming && a.upcoming[1]) {
        extra = `<div class="next">Poi ${hhmm(a.upcoming[1].start)} ${esc(a.upcoming[1].title)}</div>`;
      }
    } else if (this._view === "prime") {
      const p = a.prime_time;
      time = p ? `${hhmm(p.start)}–${hhmm(p.end)}` : "";
      title = p
        ? `<div class="title">${esc(p.title)}</div>`
        : `<div class="title dim">Nessuna informazione</div>`;
    } else {
      time = a.end ? `fino alle ${hhmm(a.end)}` : "";
      title = `<div class="title">${esc(st.state)}</div>`;
      if (this._config.show_next && a.next_title) {
        extra = `<div class="next">${hhmm(a.next_start)} ${esc(a.next_title)}</div>`;
      }
      if (Number.isFinite(a.progress)) {
        bar = `<div class="bar"><div style="width:${a.progress}%"></div></div>`;
      }
    }

    const name = a.channel_name || a.friendly_name || id;
    const star = this._config.show_star
      ? `<button class="star${a.favorite ? " on" : ""}" data-star="${esc(id)}"
           aria-label="${a.favorite ? "Togli dai preferiti" : "Aggiungi ai preferiti"}">${a.favorite ? "★" : "☆"}</button>`
      : "";
    return `<div class="row" data-entity="${esc(id)}" tabindex="0" role="button" aria-label="${esc(name)}">
      ${logo}
      <div class="info">
        <div class="top"><span class="ch">${num ? `<b>${num}</b>` : ""}${esc(name)}</span><span class="time">${time}</span></div>
        ${title}${extra}
      </div>${star}${bar}
    </div>`;
  }
}

if (!customElements.get("tv-italia-card")) {
  customElements.define("tv-italia-card", TvItaliaCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "tv-italia-card",
    name: "TV Italia",
    description: "Guida TV compatta e scorrevole: in onda, a seguire, preferiti e filtri per genere.",
    preview: true,
  });
  console.info(`%c TV-ITALIA-CARD %c ${CARD_VERSION} `, "background:#0b5;color:#fff", "background:#333;color:#fff");
}
