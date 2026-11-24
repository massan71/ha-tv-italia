"""Parser XMLTV per la guida TV (nessuna dipendenza da Home Assistant)."""
from __future__ import annotations

import gzip
import io
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Iterable

_TIME_RE = re.compile(r"^(\d{14})\s*([+-]\d{4})?")


@dataclass(slots=True)
class Programme:
    """Un programma della guida."""

    start: datetime
    stop: datetime
    title: str
    subtitle: str | None = None
    description: str | None = None
    categories: list[str] = field(default_factory=list)
    icon: str | None = None
    episode: str | None = None

    def as_dict(self) -> dict:
        return {
            "title": self.title,
            "subtitle": self.subtitle,
            "description": self.description,
            "categories": self.categories,
            "icon": self.icon,
            "episode": self.episode,
            "start": self.start.isoformat(),
            "end": self.stop.isoformat(),
        }


@dataclass(slots=True)
class ChannelGuide:
    """Palinsesto di un singolo canale XMLTV."""

    epg_id: str
    display_names: list[str] = field(default_factory=list)
    icon: str | None = None
    programmes: list[Programme] = field(default_factory=list)


def parse_xmltv_time(value: str) -> datetime | None:
    """Converte '20261123050000 +0000' in datetime con timezone."""
    match = _TIME_RE.match(value.strip())
    if not match:
        return None
    stamp, offset = match.groups()
    dt = datetime.strptime(stamp, "%Y%m%d%H%M%S")
    if offset:
        sign = 1 if offset[0] == "+" else -1
        delta = timedelta(hours=int(offset[1:3]), minutes=int(offset[3:5]))
        tz = timezone(sign * delta)
    else:
        tz = timezone.utc
    return dt.replace(tzinfo=tz)


def normalize_name(name: str) -> str:
    """Normalizza un nome canale per il confronto ('Rai 1 HD' -> 'rai1')."""
    name = name.lower()
    name = re.sub(r"\b(hd|sd|fhd|uhd|4k|italia|it)\b", "", name)
    return re.sub(r"[^a-z0-9!]", "", name)


def decompress(raw: bytes) -> bytes:
    """Decomprime se il contenuto e' gzip."""
    if raw[:2] == b"\x1f\x8b":
        return gzip.decompress(raw)
    return raw


def _text(elem: ET.Element, tag: str) -> str | None:
    child = elem.find(tag)
    if child is None or child.text is None:
        return None
    return child.text.strip() or None


def parse_xmltv(
    raw: bytes,
    window_start: datetime,
    window_end: datetime,
    wanted_ids: set[str] | None = None,
    wanted_names: set[str] | None = None,
) -> dict[str, ChannelGuide]:
    """Analizza un file XMLTV e restituisce i palinsesti per ID canale.

    Mantiene solo i programmi che si sovrappongono a [window_start, window_end].
    Se sono indicati `wanted_ids`/`wanted_names` (nomi gia' normalizzati) tiene
    solo i canali corrispondenti: le guide complete hanno migliaia di canali e
    tenerli tutti in memoria sarebbe uno spreco. Il file .gz viene decompresso
    a flusso, senza caricarlo tutto in memoria.
    """
    filtering = wanted_ids is not None or wanted_names is not None
    wanted_ids = wanted_ids or set()
    wanted_names = wanted_names or set()
    keep_cache: dict[str, bool] = {}

    def keep(epg_id: str, names: list[str] | None = None) -> bool:
        if not filtering:
            return True
        if epg_id in keep_cache and names is None:
            return keep_cache[epg_id]
        candidates = names or [epg_id.rsplit(".", 1)[0]]
        result = epg_id in wanted_ids or any(
            normalize_name(n) in wanted_names for n in candidates
        )
        keep_cache[epg_id] = result
        return result

    source = (
        gzip.GzipFile(fileobj=io.BytesIO(raw)) if raw[:2] == b"\x1f\x8b" else io.BytesIO(raw)
    )
    guides: dict[str, ChannelGuide] = {}

    for _event, elem in ET.iterparse(source, events=("end",)):
        if elem.tag == "channel":
            epg_id = elem.get("id")
            if epg_id:
                names = [d.text.strip() for d in elem.findall("display-name") if d.text]
                if keep(epg_id, names):
                    guide = guides.setdefault(epg_id, ChannelGuide(epg_id))
                    guide.display_names = names
                    icon = elem.find("icon")
                    if icon is not None and icon.get("src"):
                        guide.icon = icon.get("src")
            elem.clear()

        elif elem.tag == "programme":
            epg_id = elem.get("channel")
            if not epg_id or not keep(epg_id):
                elem.clear()
                continue
            start = parse_xmltv_time(elem.get("start", ""))
            stop = parse_xmltv_time(elem.get("stop", "")) if elem.get("stop") else None
            title = _text(elem, "title")
            if start and title:
                if stop is None:
                    stop = start + timedelta(minutes=30)
                if stop > window_start and start < window_end:
                    icon_el = elem.find("icon")
                    episode = None
                    for ep in elem.findall("episode-num"):
                        if ep.get("system") == "onscreen" and ep.text:
                            episode = ep.text.strip()
                            break
                    guides.setdefault(epg_id, ChannelGuide(epg_id)).programmes.append(
                        Programme(
                            start=start,
                            stop=stop,
                            title=title,
                            subtitle=_text(elem, "sub-title"),
                            description=_text(elem, "desc"),
                            categories=[
                                c.text.strip() for c in elem.findall("category") if c.text
                            ],
                            icon=icon_el.get("src") if icon_el is not None else None,
                            episode=episode,
                        )
                    )
            elem.clear()

    for guide in guides.values():
        guide.programmes.sort(key=lambda p: p.start)
        # rimuove duplicati con lo stesso orario di inizio
        deduped: list[Programme] = []
        for prog in guide.programmes:
            if deduped and deduped[-1].start == prog.start:
                continue
            deduped.append(prog)
        guide.programmes = deduped

    return guides


def resolve_channel(
    guides: dict[str, ChannelGuide],
    epg_ids: Iterable[str],
    name: str,
) -> ChannelGuide | None:
    """Trova il palinsesto di un canale: prima per ID, poi per nome."""
    for epg_id in epg_ids:
        guide = guides.get(epg_id)
        if guide and guide.programmes:
            return guide
    wanted = normalize_name(name)
    for guide in guides.values():
        if not guide.programmes:
            continue
        names = guide.display_names or [guide.epg_id.rsplit(".", 1)[0]]
        if any(normalize_name(n) == wanted for n in names):
            return guide
    return None


def current_and_upcoming(
    programmes: list[Programme], now: datetime, count: int
) -> tuple[Programme | None, list[Programme]]:
    """Restituisce il programma in onda e i successivi."""
    current = None
    upcoming: list[Programme] = []
    for prog in programmes:
        if prog.stop <= now:
            continue
        if prog.start <= now < prog.stop and current is None:
            current = prog
            continue
        if prog.start >= now or current is not None:
            upcoming.append(prog)
            if len(upcoming) >= count:
                break
    return current, upcoming


def programme_at(programmes: list[Programme], when: datetime) -> Programme | None:
    """Programma in onda in un dato istante."""
    for prog in programmes:
        if prog.start <= when < prog.stop:
            return prog
    return None


# --- Generi -----------------------------------------------------------------
# Generi semplificati mostrati nei filtri della card.
GENRES = ("film", "serie", "sport", "news", "kids", "docs", "show")

# Regole sulle categorie XMLTV (prima e seconda categoria, minuscole).
# L'ordine conta: la prima regola che corrisponde vince.
_GENRE_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("sport", ("sport", "calcio", "tennis", "motori", "basket", "golf", "rugby", "ciclismo")),
    ("news", ("informazione", "telegiornale", "notiziario", "news", "attualita", "tg ")),
    ("kids", ("cartoni", "bimbi", "kids", "ragazzi", "anime", "bambini", "live action",
              "educativo", "famiglie")),
    ("serie", ("serie", "fiction", "telefilm", "soap", "sit-com", "sitcom", "miniserie")),
    ("film", ("film", "cinema", "commedia", "drammatico", "azione", "thriller", "avventura",
              "fantasy", "fantastico", "poliziesco", "crime", "horror", "western", "romantico",
              "fantascienza", "biografico", "giallo")),
    ("docs", ("mondo e tendenze", "scoperta", "scienza", "storia", "natura", "documentari",
              "spazio", "regno animale", "viaggi", "uomini", "arte", "cultura")),
    ("show", ("intrattenimento", "show", "talk", "varietà", "varieta", "reality", "magazine",
              "quiz", "musica", "lifestyle", "cucina")),
)


def genre_of(prog: Programme, default: str | None = None) -> str | None:
    """Genere semplificato di un programma, o il genere tipico del canale."""
    cats = [c.lower() for c in prog.categories[:2]]
    if cats:
        first = cats[0]
        joined = " > ".join(cats)
        # "Intrattenimento > Fiction" e' una serie, non uno show
        if first == "intrattenimento" and len(cats) > 1:
            for genre, words in _GENRE_RULES:
                if any(w in cats[1] for w in words):
                    return genre
        for genre, words in _GENRE_RULES:
            if any(w in first for w in words):
                return genre
        for genre, words in _GENRE_RULES:
            if any(w in joined for w in words):
                return genre
    return default
