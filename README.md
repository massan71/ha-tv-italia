<img src="icon.png" alt="" width="96" align="right">

# TV Italia per Home Assistant

Integrazione personalizzata che mostra i **canali televisivi italiani** (digitale terrestre e Sky) con la guida TV:
programma in onda, avanzamento, programma successivo e **prima serata**.

- Un sensore per canale (`sensor.tv_rai1`, `sensor.tv_skyuno`, …): lo stato è il titolo in onda.
- 46 canali del digitale terrestre con numerazione LCN (Rai, Mediaset, La7, TV8, NOVE, Cielo, Real Time, DMAX, …).
- 35 canali Sky con la numerazione del decoder Sky (Sky TG24, Sky Uno, Sky Atlantic, Sky Sport, Sky Cinema, …).
- I sensori si chiamano con il numero davanti (`001 · Rai 1`, `108 · Sky Uno`), così negli elenchi di Home Assistant sono in ordine di telecomando.
- Card Lovelace inclusa (`custom:tv-italia-card`), compatta e scorrevole, caricata automaticamente, con le schede "In onda" e "Stasera".
- Configurazione da interfaccia, nessun YAML.
- Guida da una sorgente XMLTV pubblica (di default [epgshare01](https://epgshare01.online)), sostituibile con qualsiasi URL XMLTV `.xml` o `.xml.gz`.

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
ad altezza fissa che scorre. Le schede **In onda** e **Stasera** cambiano vista; toccando un canale si aprono i dettagli.

```yaml
type: custom:tv-italia-card
title: Guida TV      # "" per nascondere il titolo
height: 320          # altezza dell'elenco in px: oltre, scorre
view: now            # now | prime
show_next: false     # mostra anche il programma successivo
show_logo: true
platform: all      # all | dtt (digitale terrestre) | sky
# entities:          # opzionale, di default tutti i canali configurati
#   - sensor.tv_rai1
#   - sensor.tv_canale5
```

Se la card non compare o non si aggiorna dopo l'installazione, ricarica la pagina del browser (svuota la cache).

## Attributi dei sensori

| Attributo | Descrizione |
|---|---|
| `channel_number`, `channel_name`, `channel_group`, `channel_platform`, `channel_logo` | Dati del canale (`channel_platform`: `dtt` o `sky`) |
| `start`, `end`, `progress`, `remaining_minutes` | Orari e avanzamento del programma in onda |
| `subtitle`, `description`, `categories`, `episode`, `image` | Dettagli del programma |
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

## Note
La guida TV proviene da servizi di terze parti: completezza e accuratezza dipendono dalla sorgente scelta.
