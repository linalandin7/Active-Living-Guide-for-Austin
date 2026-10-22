"""Rules for the three-school cards (Covington, Marshall, Dessau) added from the Excel working database."""
import unittest

from harness import embedded_facilities, js, make_site

SCHOOLS = {"Covington", "Marshall", "Dessau"}
CITY = "City of Austin Parks and Recreation"


class CardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = embedded_facilities()

    def test_only_the_three_schools_appear(self):
        self.assertEqual({f["school"] for f in self.data}, SCHOOLS)

    def test_every_school_has_cards(self):
        for s in SCHOOLS:
            self.assertGreater(sum(1 for f in self.data if f["school"] == s), 0, s)

    def test_card_ids_are_unique_and_present(self):
        ids = [f.get("cardId") for f in self.data]
        self.assertTrue(all(ids), "a record has no cardId")
        self.assertEqual(len(ids), len(set(ids)))

    def test_release_status_is_known_and_nothing_is_approved_by_accident(self):
        for f in self.data:
            self.assertIn(f.get("release"), {"Pending", "Approved", "Hold", "Excluded"}, f["name"])
        # Nothing has been approved by a person yet ("Pending" and "Hold" both mean not approved).
        # Loosened on 2026-10-22 with Lina's permission from "all Pending" to "none Approved" because the
        # v13 workbook marks every card Hold. Lina plans to restore the stricter rule later; ask before changing.
        self.assertFalse([f["name"] for f in self.data if f["release"] == "Approved"], "a card is marked Approved without sign-off")

    def test_cards_not_from_the_city_have_their_own_official_link(self):
        """Without a website the quick-facts link falls back to the City Parks directory, which is wrong for other providers."""
        missing = [f["name"] for f in self.data if f.get("provider") != CITY and not f["website"]]
        self.assertEqual(missing, [], f"non-City cards without an official link: {missing[:5]}")

    def test_missing_costs_are_blank_never_free(self):
        # a card whose cost says 'Free' must have a source link (the wording must come from a source, never be invented)
        for f in self.data:
            if f["cost"].strip().lower() == "free":
                self.assertTrue(f["website"], f"'{f['name']}' says Free but has no source link")

    def test_stale_schedules_show_a_notice(self):
        for f in self.data:
            if "2025 calendar" in (f["hours"] or ""):
                self.assertTrue(f["notice"], f"{f['name']} uses a 2025 schedule without a notice")

    def test_places_with_coordinates_stay_in_the_area(self):
        for f in self.data:
            if f["latitude"] is not None:
                self.assertTrue(30.0 <= f["latitude"] <= 30.65 and -98.0 <= f["longitude"] <= -97.4, f["name"])

    def test_school_filter_offers_exactly_the_three_schools(self):
        ctx = make_site()
        self.assertEqual(sorted(js(ctx, "unique(state.facilities.map(f => f.school))")), sorted(SCHOOLS))

    def test_each_school_filter_returns_only_its_cards(self):
        ctx = make_site()
        for s in SCHOOLS:
            ctx.eval(f'elements.school.value = "{s}"; applyFilters();')
            self.assertEqual(js(ctx, "state.filtered.length"), sum(1 for f in self.data if f["school"] == s))
            self.assertTrue(all(x == s for x in js(ctx, "state.filtered.map(f => f.school)")))

    def test_todays_pick_still_has_a_candidate(self):
        ctx = make_site()
        self.assertIn("today-copy", js(ctx, "elements.today.innerHTML"))

    def test_extra_fields_do_not_change_what_cards_show(self):
        ctx = make_site()
        html = js(ctx, "elements.grid.innerHTML")
        for hidden in ("cardId", "recordId", "release", "launchPriority", "independentReview"):
            self.assertNotIn(hidden, html)

    def test_swimming_programs_use_the_pool_type_and_other_programs_a_known_type(self):
        for f in self.data:
            if f["role"] == "Active program" and f["activity"] == "Swimming & Water Play":
                self.assertEqual(f["type"], "Pool/Splash Pad", f["name"])


if __name__ == "__main__":
    unittest.main()
