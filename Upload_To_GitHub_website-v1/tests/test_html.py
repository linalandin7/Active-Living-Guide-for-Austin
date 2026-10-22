"""The page structure the JavaScript depends on must exist."""
import re
import unittest

from harness import ROOT, embedded_facilities, read_html


class HtmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = read_html()

    def test_title_and_language(self):
        self.assertIn("<title>AMSC Activity Guide</title>", self.html)
        self.assertIn('<html lang="en">', self.html)

    def test_every_element_the_script_looks_up_exists(self):
        ids = set(re.findall(r'document\.querySelector\("#([A-Za-z0-9_-]+)"\)', self.html))
        self.assertGreater(len(ids), 10)
        for i in ids:
            self.assertRegex(self.html, rf'id="{re.escape(i)}"', f"JavaScript uses #{i} but the page has no such id")

    def test_filter_controls_exist(self):
        for i in ["type-filter", "activity-filter", "school-filter", "sort-select", "radius-select", "keyword-input", "clear-filters", "facility-grid", "show-more"]:
            self.assertIn(f'id="{i}"', self.html)

    def test_sort_options_are_the_ones_the_script_handles(self):
        select = re.search(r'<select id="sort-select">(.*?)</select>', self.html, re.S).group(1)
        values = set(re.findall(r'value="([^"]*)"', select))
        self.assertTrue({"name", "cost"} <= values, values)

    def test_no_missing_local_files(self):
        refs = re.findall(r'(?:src|href)="([^"#:]+\.[a-z]{2,4})"', self.html)
        for r in refs:
            if r.startswith(("http", "mailto", "//")):
                continue
            self.assertTrue((ROOT / r).exists(), f"index.html refers to missing file {r}")

    def test_hardcoded_place_count_matches_the_data(self):
        n = len(embedded_facilities())
        self.assertRegex(self.html, rf"<strong>{n}</strong>\s*<span>places to explore</span>", "hero place count is out of date")
        self.assertIn(f"Explore {n} places", self.html, "'Explore N places' count is out of date")

    def test_external_links_open_safely(self):
        for tag in re.findall(r'<a [^>]*target="_blank"[^>]*>', self.html):
            self.assertIn("noreferrer", tag, f"link without rel=noreferrer: {tag[:80]}")


if __name__ == "__main__":
    unittest.main()
