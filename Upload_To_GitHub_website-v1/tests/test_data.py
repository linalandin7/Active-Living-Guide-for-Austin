"""The facility data the site ships with must be well formed and consistent."""
import json
import re
import unittest
from urllib.parse import urlparse

from harness import ROOT, embedded_facilities, read_html

REQUIRED = ["name", "type", "activity", "cost", "address", "city", "zip", "longitude", "latitude",
            "days", "hours", "website", "school", "parentName", "notice"]


class DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = embedded_facilities()

    def test_not_empty(self):
        self.assertGreater(len(self.data), 0)

    def test_every_record_has_all_fields(self):
        for f in self.data:
            for key in REQUIRED:
                self.assertIn(key, f, f"{f.get('name')} is missing '{key}'")

    def test_names_are_present(self):
        for f in self.data:
            self.assertTrue(str(f["name"]).strip(), "a record has an empty name")

    def test_type_is_one_the_site_has_an_image_for(self):
        html = read_html()
        block = re.search(r"const typeImages = \{(.*?)\};", html, re.S).group(1)
        known = {a or b for a, b in re.findall(r'(?m)^\s*(?:"([^"]+)"|([A-Za-z]+))\s*:', block)}
        self.assertTrue(known, "could not read typeImages from index.html")
        for f in self.data:
            self.assertIn(f["type"], known, f"{f['name']} has unknown type {f['type']!r}")

    def test_coordinates_are_numbers_in_central_texas_or_null(self):
        for f in self.data:
            lat, lon = f["latitude"], f["longitude"]
            self.assertEqual(lat is None, lon is None, f"{f['name']}: only one of latitude/longitude is set")
            if lat is not None:
                self.assertIsInstance(lat, (int, float))
                self.assertTrue(29.8 <= lat <= 30.9 and -98.3 <= lon <= -97.2, f"{f['name']} is outside the Austin area")

    def test_zip_is_five_digits_or_empty(self):
        for f in self.data:
            self.assertRegex(str(f["zip"] or ""), r"^(\d{5})?$", f"{f['name']} has a bad ZIP")

    def test_website_is_empty_or_http_url(self):
        for f in self.data:
            w = f["website"]
            if w:
                u = urlparse(w)
                self.assertIn(u.scheme, ("http", "https"), f"{f['name']} website is not a URL")
                self.assertTrue(u.netloc, f"{f['name']} website has no host")

    def test_no_missing_cost_is_shown_as_free(self):
        for f in self.data:
            if not f["cost"]:
                self.assertNotIn("free", str(f["cost"]).lower())

    def test_no_exact_duplicate_cards(self):
        seen = set()
        for f in self.data:
            key = (f["name"], f["address"], f["school"])
            self.assertNotIn(key, seen, f"duplicate card: {key}")
            seen.add(key)

    def test_data_copies_are_in_sync(self):
        """index.html, facilities.json and facilities.js must carry identical data."""
        as_json = json.loads((ROOT / "facilities.json").read_text(encoding="utf-8"))
        self.assertEqual(self.data, as_json, "facilities.json differs from the data inside index.html")
        js_text = (ROOT / "facilities.js").read_text(encoding="utf-8")
        m = re.search(r"window\.AMSC_FACILITIES = (\[.*?\n\]);", js_text, re.S)
        self.assertIsNotNone(m, "facilities.js has no AMSC_FACILITIES array")
        self.assertEqual(self.data, json.loads(m.group(1)), "facilities.js differs from the data inside index.html")


if __name__ == "__main__":
    unittest.main()
