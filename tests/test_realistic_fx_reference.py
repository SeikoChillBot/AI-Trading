"""Offline tests for the ECB reference used only for UI display."""
import json
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

from fx_reference import from_xml, load_fx, validate, URL


class CurrencyDisplayTests(unittest.TestCase):
    def test_official_xml_is_euro_based(self):
        today=datetime.now(timezone.utc).date().isoformat()
        xml=('<?xml version="1.0" encoding="UTF-8"?>'
             '<gesmes:Envelope xmlns:gesmes="http://www.gesmes.org/xml/2002-08-01" '
             'xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref">'
             '<Cube><Cube time="'+today+'"><Cube currency="USD" rate="1.1133"/>'
             '<Cube currency="JPY" rate="170.1"/></Cube></Cube></gesmes:Envelope>')
        data=from_xml(xml.encode())
        self.assertEqual(data["source"],"ECB")
        self.assertEqual(data["reference_date"],today)
        self.assertAlmostEqual(data["usd_per_eur"],1.1133)
        self.assertAlmostEqual(360/data["usd_per_eur"],323.362975,places=4)
    def test_future_and_stale_quotes_rejected(self):
        now=datetime.now(timezone.utc)
        good={"source":"ECB","reference_date":now.date().isoformat(),"usd_per_eur":1.12}
        self.assertTrue(validate(good,now))
        self.assertFalse(validate(dict(good,usd_per_eur=0),now))
        self.assertFalse(validate(dict(good,reference_date=(now.date()-timedelta(days=40)).isoformat()),now))
        self.assertFalse(validate(dict(good,source="unknown"),now))
    def test_recent_cache_skips_network(self):
        now=datetime.now(timezone.utc)
        content={"source":"ECB","reference_date":now.date().isoformat(),"usd_per_eur":1.1133,
                 "retrieved_at":now.isoformat(),"url":URL}
        with tempfile.TemporaryDirectory() as root:
            filename=Path(root)/"fx.json"
            filename.write_text(json.dumps(content))
            with patch("fx_reference.urlopen",side_effect=AssertionError("network must not be accessed")):
                self.assertEqual(load_fx(filename)["usd_per_eur"],1.1133)
    def test_network_failure_does_not_invent_rate(self):
        with tempfile.TemporaryDirectory() as root:
            with patch("fx_reference.urlopen",side_effect=OSError("offline")):
                self.assertIsNone(load_fx(Path(root)/"missing.json"))


if __name__=="__main__":
    unittest.main()
