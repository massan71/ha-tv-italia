"""Costanti per l'integrazione TV Italia."""
from __future__ import annotations

from dataclasses import dataclass

DOMAIN = "tv_italia"

CONF_CHANNELS = "channels"
CONF_EPG_URL = "epg_url"
CONF_REFRESH_HOURS = "refresh_hours"

DEFAULT_EPG_URL = "https://epgshare01.online/epgshare01/epg_ripper_IT1.xml.gz"
DEFAULT_REFRESH_HOURS = 6

# Ora (locale) usata per calcolare la "prima serata"
PRIME_TIME_HOUR = 21
PRIME_TIME_MINUTE = 30

# Quanti programmi successivi esporre negli attributi
UPCOMING_COUNT = 6

CARD_URL = "/tv_italia/tv-italia-card.js"
CARD_VERSION = "1.4.0"


@dataclass(frozen=True)
class Channel:
    """Canale del digitale terrestre italiano."""

    key: str
    name: str
    number: int
    epg_ids: tuple[str, ...]
    group: str
    platform: str = "dtt"  # "dtt" = digitale terrestre, "sky" = Sky
    # Logo di riserva (Wikimedia Commons) se quello della guida non funziona
    logo: str | None = None


# Canali del digitale terrestre nazionale, con numero LCN.
# epg_ids: ID XMLTV candidati, in ordine di preferenza. Viene usato il primo
# che ha programmi nella guida; se nessuno corrisponde si prova per nome.
CHANNELS: tuple[Channel, ...] = (
    Channel("rai1", "Rai 1", 1, ("Rai1.it", "Rai.1.HD..101.it"), "Rai"),
    Channel("rai2", "Rai 2", 2, ("Rai2.it", "Rai.2.HD..102.it"), "Rai"),
    Channel("rai3", "Rai 3", 3, ("Rai3.it", "Rai.3.HD..103.it"), "Rai"),
    Channel("rete4", "Rete 4", 4, ("Rete.4.it",), "Mediaset"),
    Channel("canale5", "Canale 5", 5, ("Canale.5.it",), "Mediaset"),
    Channel("italia1", "Italia 1", 6, ("Italia.1.it",), "Mediaset"),
    Channel("la7", "LA7", 7, ("LA7.HD.it",), "La7"),
    Channel("tv8", "TV8", 8, ("TV8.HD.it",), "Sky"),
    Channel("nove", "NOVE", 9, ("Nove.it", "NOVE.HD..149.it"), "Warner Bros. Discovery",
            logo="https://thumb.wikimedia.org/wikipedia/commons/thumb/2/2d/Nove_-_Logo_2017.svg/250px-Nove_-_Logo_2017.svg.png"),
    Channel("venti", "20 Mediaset", 20, ("20.it",), "Mediaset"),
    Channel("rai4", "Rai 4", 21, ("Rai4.it", "Rai.4..5021.it"), "Rai"),
    Channel("iris", "Iris", 22, ("Iris.it",), "Mediaset"),
    Channel("rai5", "Rai 5", 23, ("Rai5.it", "Rai.5..5023.it"), "Rai"),
    Channel("raimovie", "Rai Movie", 24, ("RaiMovie.it", "Rai.Movie..5024.it"), "Rai"),
    Channel("raipremium", "Rai Premium", 25, ("RaiPremium.it", "Rai.Premium..5025.it"), "Rai"),
    Channel("cielo", "Cielo", 26, ("cielo.it",), "Sky"),
    Channel("twentyseven", "Twentyseven", 27, ("27.Twentyseven.it",), "Mediaset"),
    Channel("la7d", "LA7d", 29, ("LA7D.it",), "La7",
            logo="https://thumb.wikimedia.org/wikipedia/commons/thumb/8/8b/LA7d_%282024%29.svg/250px-LA7d_%282024%29.svg.png"),
    Channel("la5", "La5", 30, ("La.5.it",), "Mediaset"),
    Channel("realtime", "Real Time", 31, ("Real.Time.it", "Real.Time.HD..160.it"), "Warner Bros. Discovery",
            logo="https://thumb.wikimedia.org/wikipedia/commons/thumb/8/89/Real_Time_HD_logo.png/250px-Real_Time_HD_logo.png"),
    Channel("foodnetwork", "Food Network", 33, ("Food.Network.it", "Food.Network.HD..417.it"), "Warner Bros. Discovery",
            logo="https://thumb.wikimedia.org/wikipedia/commons/thumb/0/06/Food_Network_logo.svg/250px-Food_Network_logo.svg.png"),
    Channel("cine34", "Cine34", 34, ("Cine34.it",), "Mediaset"),
    Channel("focus", "Focus", 35, ("Focus.it",), "Mediaset"),
    Channel("warnertv", "Warner TV", 37, ("Warner.TV.it",), "Warner Bros. Discovery"),
    Channel("giallo", "Giallo", 38, ("Giallo.TV.it", "GIALLO.HD..167.it"), "Warner Bros. Discovery",
            logo="https://thumb.wikimedia.org/wikipedia/commons/thumb/8/8e/Giallo_-_Logo_2014.svg/250px-Giallo_-_Logo_2014.svg.png"),
    Channel("topcrime", "Top Crime", 39, ("Top.Crime.it", "TOPcrime.HD..168.it"), "Mediaset"),
    Channel("boing", "Boing", 40, ("Boing.it",), "Mediaset"),
    Channel("k2", "K2", 41, ("K2.it",), "Warner Bros. Discovery",
            logo="https://thumb.wikimedia.org/wikipedia/commons/thumb/b/b4/K2_new_logo.svg/250px-K2_new_logo.svg.png"),
    Channel("raigulp", "Rai Gulp", 42, ("RaiGulp.it", "Rai.Gulp..5042.it"), "Rai"),
    Channel("raiyoyo", "Rai Yoyo", 43, ("RaiYoyo.it", "Rai.Yoyo..5043.it"), "Rai"),
    Channel("frisbee", "Frisbee", 44, ("Frisbee.it",), "Warner Bros. Discovery"),
    Channel("cartoonito", "Cartoonito", 46, ("Cartoonito.it",), "Mediaset"),
    Channel("super", "Super!", 47, ("Super!.it",), "Paramount"),
    Channel("rainews24", "Rai News 24", 48, ("RaiNews24.it", "Rai.News.24..508.it"), "Rai"),
    Channel("italia2", "Italia 2", 49, ("Italia.2.it",), "Mediaset"),
    Channel("tgcom24", "TGCom24", 51, ("TGCom.it",), "Mediaset"),
    Channel("dmax", "DMAX", 52, ("DMAX.it", "DMAX.HD..170.it"), "Warner Bros. Discovery",
            logo="https://thumb.wikimedia.org/wikipedia/commons/thumb/4/4f/DMAX_-_Logo_2016.svg/250px-DMAX_-_Logo_2016.svg.png"),
    Channel("raistoria", "Rai Storia", 54, ("RaiStoria.it", "Rai.Storia..5054.it"), "Rai"),
    Channel("mediasetextra", "Mediaset Extra", 55, ("Mediaset.Extra.it",), "Mediaset"),
    Channel("hgtv", "HGTV", 56, ("HGTV.it", "HGTV.HD..418.it"), "Warner Bros. Discovery",
            logo="https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a8/HGTV_2010.svg/250px-HGTV_2010.svg.png"),
    Channel("raiscuola", "Rai Scuola", 57, ("RaiScuola.it",), "Rai"),
    Channel("raisport", "Rai Sport", 58, ("RaiSport.it", "RAI.Sport...227.it"), "Rai"),
    Channel("motortrend", "Motor Trend", 59, ("Motor.Trend.it", "Motor.Trend.HD..419.it"), "Warner Bros. Discovery"),
    Channel("sportitalia", "Sportitalia", 60, ("Sportitalia.HD.it",), "Sportitalia"),
    Channel("supertennis", "SuperTennis", 64, ("SuperTennis.HD.it",), "FITP"),
    Channel("la7cinema", "LA7 Cinema", 0, ("LA7.CINEMA.it",), "La7"),
    # --- Sky (numerazione del decoder Sky, novembre 2026) ---
    Channel("skytg24", "Sky TG24", 100, ('Sky.TG24.it',), "Sky", "sky"),
    Channel("skyuno", "Sky Uno", 108, ('Sky.Uno.it',), "Sky", "sky"),
    Channel("skyuno1", "Sky Uno +1", 109, ('Sky.Uno.+.it',), "Sky", "sky"),
    Channel("skyatlantic", "Sky Atlantic", 111, ('Sky.Atlantic.it',), "Sky", "sky"),
    Channel("skyserie", "Sky Serie", 112, ('Sky.Serie.it',), "Sky", "sky"),
    Channel("skyinvestigation", "Sky Investigation", 113, ('Sky.Investigation.it',), "Sky", "sky"),
    Channel("skycollection", "Sky Collection", 114, ('Sky.Collection.it',), "Sky", "sky"),
    Channel("skycrime", "Sky Crime", 115, ('Sky.Crime.it',), "Sky", "sky"),
    Channel("skydocumentaries", "Sky Documentaries", 117, ('Sky.Documentaries.it',), "Sky", "sky"),
    Channel("skyadventure", "Sky Adventure", 118, ('Sky.Adventure.it',), "Sky", "sky"),
    Channel("skynature", "Sky Nature", 119, ('Sky.Nature.it',), "Sky", "sky"),
    Channel("skyarte", "Sky Arte", 120, ('Sky.Arte.it',), "Sky", "sky"),
    Channel("skysport24", "Sky Sport 24", 200, ('Sky.Sport.24.it',), "Sky", "sky"),
    Channel("skysportuno", "Sky Sport Uno", 201, ('Sky.Sport.Uno.it',), "Sky", "sky"),
    Channel("skysportcalcio", "Sky Sport Calcio", 202, ('Sky.Sport.Calcio.it',), "Sky", "sky"),
    Channel("skysporttennis", "Sky Sport Tennis", 203, ('Sky.Sport.Tennis.it',), "Sky", "sky"),
    Channel("skysportarena", "Sky Sport Arena", 204, ('Sky.Sport.Arena.it',), "Sky", "sky"),
    Channel("skysportbasket", "Sky Sport Basket", 205, ('Sky.Sport.NBA.it',), "Sky", "sky"),
    Channel("skysportmax", "Sky Sport Max", 206, ('Sky.Sport.Max.it',), "Sky", "sky"),
    Channel("skysportf1", "Sky Sport F1", 207, ('Sky.Sport.F1.it',), "Sky", "sky"),
    Channel("skysportmotogp", "Sky Sport MotoGP", 208, ('Sky.Sport.MotoGP.it',), "Sky", "sky"),
    Channel("skysportgolf", "Sky Sport Golf", 209, ('Sky.Sport.Golf.it',), "Sky", "sky"),
    Channel("skysportlegend", "Sky Sport Legend", 210, ('Sky.Sport.Legend.it',), "Sky", "sky"),
    Channel("skysportmix", "Sky Sport Mix", 211, ('Sky.Sport.Mix.it',), "Sky", "sky"),
    Channel("skysport4k", "Sky Sport 4K", 213, ('Sky.Sport.4K.it',), "Sky", "sky"),
    Channel("skycinemauno", "Sky Cinema Uno", 301, ('Sky.Cinema.Uno.it',), "Sky", "sky"),
    Channel("skycinemadue", "Sky Cinema Due", 302, ('Sky.Cinema.Due.it',), "Sky", "sky"),
    Channel("skycinemacollection", "Sky Cinema Collection", 303, ('Sky.Cinema.Collection.it',), "Sky", "sky"),
    Channel("skycinemafamily", "Sky Cinema Family", 304, ('Sky.Cinema.Family.it',), "Sky", "sky"),
    Channel("skycinemaaction", "Sky Cinema Action", 305, ('Sky.Cinema.Action.it',), "Sky", "sky"),
    Channel("skycinemasuspense", "Sky Cinema Suspense", 306, ('Sky.Cinema.Suspense.it',), "Sky", "sky"),
    Channel("skycinemaromance", "Sky Cinema Romance", 307, ('Sky.Cinema.Romance.it',), "Sky", "sky"),
    Channel("skycinemadrama", "Sky Cinema Drama", 308, ('Sky.Cinema.Drama.it',), "Sky", "sky"),
    Channel("skycinemacomedy", "Sky Cinema Comedy", 309, ('Sky.Cinema.Comedy.it',), "Sky", "sky"),
    Channel("skycinemauno24", "Sky Cinema Uno +24", 310, ('Sky.Cinema.Uno.+24.it',), "Sky", "sky"),
)

CHANNELS_BY_KEY: dict[str, Channel] = {c.key: c for c in CHANNELS}

# Canali generalisti selezionati di default
DEFAULT_CHANNELS: list[str] = [
    "rai1", "rai2", "rai3", "rete4", "canale5", "italia1", "la7", "tv8", "nove",
]
