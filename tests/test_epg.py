"""Test del parser XMLTV e delle regole su canali e generi."""
import gzip
from datetime import datetime, timedelta, timezone

NOW = datetime(2026, 11, 24, 20, 45, tzinfo=timezone.utc)
WINDOW = (NOW - timedelta(hours=6), NOW + timedelta(days=2))


def test_parse_time(epg):
    dt = epg.parse_xmltv_time("20261124203000 +0100")
    assert dt.isoformat() == "2026-11-24T20:30:00+01:00"
    assert epg.parse_xmltv_time("20261124203000").tzinfo == timezone.utc
    assert epg.parse_xmltv_time("garbage") is None


def test_parse_window_dedup_and_icon(epg, mini_xml):
    guides = epg.parse_xmltv(mini_xml, *WINDOW)
    rai1 = guides["Rai1.it"]
    titles = [p.title for p in rai1.programmes]
    assert titles == ["Tg1", "Una finestra vista lago", "Porta a Porta"]  # no vecchio, no duplicato
    assert guides["Rai.1.HD..101.it"].icon == "https://example.org/rai1.png"
    assert rai1.display_names == ["Rai 1"]


def test_parse_gzip_is_identical(epg, mini_xml):
    plain = epg.parse_xmltv(mini_xml, *WINDOW)
    gz = epg.parse_xmltv(gzip.compress(mini_xml), *WINDOW)
    assert {k: len(v.programmes) for k, v in plain.items()} == {
        k: len(v.programmes) for k, v in gz.items()
    }


def test_parse_keeps_only_wanted_channels(epg, mini_xml):
    guides = epg.parse_xmltv(
        mini_xml, *WINDOW, wanted_ids={"Rai1.it"}, wanted_names={epg.normalize_name("Canale 5")}
    )
    assert set(guides) == {"Rai1.it", "Canale.5.it"}


def test_resolve_by_id_then_by_name(epg, mini_xml):
    guides = epg.parse_xmltv(mini_xml, *WINDOW)
    assert epg.resolve_channel(guides, ("Missing.it", "Rai1.it"), "Rai 1").epg_id == "Rai1.it"
    # ID sconosciuto: trovato per nome ("Canale 5" == "Canale 5")
    assert epg.resolve_channel(guides, ("Nope.it",), "Canale 5").epg_id == "Canale.5.it"
    assert epg.resolve_channel(guides, ("Nope.it",), "Inesistente") is None


def test_normalize_name(epg):
    assert epg.normalize_name("Rai 1 HD") == "rai1"
    assert epg.normalize_name("Rai 1 4K") == "rai1"
    assert epg.normalize_name("Super!") == "super!"


def test_current_and_upcoming(epg, mini_xml):
    progs = epg.parse_xmltv(mini_xml, *WINDOW)["Rai1.it"].programmes
    current, upcoming = epg.current_and_upcoming(progs, NOW, 5)
    assert current.title == "Una finestra vista lago"
    assert [p.title for p in upcoming] == ["Porta a Porta"]
    assert epg.programme_at(progs, NOW + timedelta(hours=1)).title == "Porta a Porta"


def test_genres(epg, mini_xml):
    guides = epg.parse_xmltv(mini_xml, *WINDOW)
    tg1, fiction, porta = guides["Rai1.it"].programmes
    assert epg.genre_of(tg1) == "news"
    assert epg.genre_of(fiction) == "serie"  # Intrattenimento > Fiction
    assert epg.genre_of(porta) is None
    assert epg.genre_of(porta, "show") == "show"  # genere del canale
    assert epg.genre_of(guides["Canale.5.it"].programmes[0]) == "sport"


def test_channel_table_is_consistent(const, epg):
    keys = [c.key for c in const.CHANNELS]
    assert len(keys) == len(set(keys)), "chiavi duplicate"
    numbers = [(c.platform, c.number) for c in const.CHANNELS if c.number]
    assert len(numbers) == len(set(numbers)), "numeri duplicati"
    assert set(const.DEFAULT_CHANNELS) <= set(keys)
    for c in const.CHANNELS:
        assert c.platform in ("dtt", "sky")
        assert c.genre is None or c.genre in epg.GENRES
        assert c.epg_ids
