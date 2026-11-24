<img src="icon.png" alt="" width="96" align="right">

[![Validate](https://github.com/massan71/ha-tv-italia/actions/workflows/validate.yml/badge.svg)](https://github.com/massan71/ha-tv-italia/actions/workflows/validate.yml)

# TV Italia per Home Assistant

Integrazione personalizzata che mostra i **canali televisivi italiani** (digitale terrestre e Sky) con la guida TV:
programma in onda, avanzamento, programma successivo e **prima serata**.

- Un sensore per canale (`sensor.tv_rai1`, `sensor.tv_skyuno`, …): lo stato è il titolo in onda.
- 46 canali del digitale terrestre con numerazione LCN (Rai, Mediaset, La7, TV8, NOVE, Cielo, Real Time, DMAX, …).
- 35 canali Sky con la numerazione del decoder Sky (Sky TG24, Sky Uno, Sky Atlantic, Sky Sport, Sky Cinema, …).
- I sensori si chiamano con il numero davanti (`001 · Rai 1`, `108 · Sky Uno`), così negli elenchi di Home Assistant sono in ordine di telecomando.
- Card Lovelace inclusa (`custom:tv-italia-card`), compatta e scorrevole, caricata automaticamente, con le schede "In onda" e "A seguire".
- Configurazione da interfaccia, nessun YAML.
- Guida da una sorgente XMLTV pubblica (di default [epgshare01](https://epgshare01.online)), sostituibile con qualsiasi URL XMLTV `.xml` o `.xml.gz`.
- **Guida di riserva** ([epgitalia.tv](https://www.epgitalia.tv)): usata solo se la principale non risponde o le mancano dei canali. Si può cambiare o disattivare (campo vuoto) nelle opzioni.
- Se la guida non si aggiorna da oltre 12 ore compare un avviso in **Impostazioni → Riparazioni**, che sparisce da solo quando torna disponibile.

## Installazione

### HACS (repository personalizzato)
1. HACS → ⋮ → *Repository personalizzati* → aggiungi l'URL di questo repository, categoria **Integrazione**.
2. Installa **TV Italia** e riavvia Home Assistant.

### Manuale
Copia `custom_components/tv_italia` in `<config>/custom_components/tv_italia` e riavvia Home Assistant.

## Configurazione
*Impostazioni → Dispositivi e servizi → Aggiungi integrazione → TV Italia*, poi scegli i canali.
Puoi cambiare canali, URL della guida e frequenza di aggiornamento da **Configura**.

## Card

Card compatta: un canale per riga (logo, numero, titolo, orario e barra di avanzamento) dentro un elenco
ad altezza fissa che scorre. Le schede **In onda** e **A seguire** (con orario e "tra 20 min") cambiano vista;
toccando un canale si aprono i dettagli. È disponibile anche la scheda **Stasera** (prima serata).

```yaml
type: custom:tv-italia-card
title: Guida TV      # "" per nascondere il titolo
height: 320          # altezza dell'elenco in px: oltre, scorre
tabs: [now, next]    # now (In onda) | next (A seguire) | prime (Stasera)
view: now            # scheda iniziale
show_next: false     # mostra anche il programma successivo
show_logo: true
platform: all      # all | dtt (digitale terrestre) | sky
filters: true      # filtri per genere e Preferiti
show_star: true    # stellina per i preferiti
favorites_first: true
# entities:          # opzionale, di default tutti i canali configurati
#   - sensor.tv_rai1
#   - sensor.tv_canale5
```

Se la card non compare o non si aggiorna dopo l'installazione, ricarica la pagina del browser (svuota la cache).

## Preferiti e filtri

Tocca la ☆ accanto a un canale per metterlo tra i preferiti: finisce in cima all'elenco ed è
salvato in Home Assistant, quindi vale su tutti i dispositivi. Sopra l'elenco ci sono i filtri
**Preferiti, Film, Serie, Sport, Notizie, Bambini, Documentari, Show** (si vedono solo quelli con
almeno un canale). Il genere viene dalle categorie della guida o, se mancano, dal tipo di canale.

## Azioni

| Azione | Cosa fa |
|---|---|
| `tv_italia.set_favorite` | Aggiunge/toglie canali dai preferiti (`entity_id`, `favorite` opzionale: se manca inverte) |
| `tv_italia.stasera` | Restituisce la prima serata (21:30) con un `message` pronto per una notifica. Opzioni: `only_favorites`, `platform` |

Notifica ogni sera alle 20:30:

```yaml
triggers:
  - trigger: time
    at: "20:30:00"
actions:
  - action: tv_italia.stasera
    data:
      only_favorites: true
    response_variable: stasera
  - action: notify.mobile_app_il_mio_telefono
    data:
      title: "📺 Stasera in TV"
      message: "{{ stasera.message }}"
```

## Attributi dei sensori

| Attributo | Descrizione |
|---|---|
| `channel_number`, `channel_name`, `channel_group`, `channel_platform`, `channel_logo` | Dati del canale (`channel_platform`: `dtt` o `sky`) |
| `start`, `end`, `progress`, `remaining_minutes` | Orari e avanzamento del programma in onda |
| `subtitle`, `description`, `categories`, `episode`, `image` | Dettagli del programma |
| `genre`, `favorite` | Genere del programma in onda e se il canale è tra i preferiti |
| `next_title`, `next_start` | Programma successivo |
| `upcoming` | Lista dei prossimi 6 programmi |
| `prime_time` | Programma in onda alle 21:30 di stasera |

Esempio di automazione: notifica quando su Rai 1 inizia un programma che contiene "Montalbano".

```yaml
triggers:
  - trigger: state
    entity_id: sensor.tv_rai1
conditions:
  - condition: template
    value_template: "{{ 'montalbano' in trigger.to_state.state | lower }}"
actions:
  - action: notify.notify
    data:
      message: "Su Rai 1 inizia ora: {{ trigger.to_state.state }}"
```

## Icona
L'icona è inclusa in `custom_components/tv_italia/brand/` e viene mostrata da Home Assistant 2026.3 in poi.

## Sviluppo

```bash
pip install pytest && pytest
```

A ogni push GitHub Actions esegue hassfest, la validazione HACS e i test.

## Note
La guida TV proviene da servizi di terze parti: completezza e accuratezza dipendono dalla sorgente scelta.
