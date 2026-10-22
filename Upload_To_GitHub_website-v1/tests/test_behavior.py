"""What the site does: filters, search, sort, cost text, distance, safe rendering.
These run the site's real JavaScript against a small fixed set of test facilities."""
import json
import unittest

from harness import fac, js, make_site, embedded_facilities

SAMPLE = [
    fac("Alpha Pool", type="Pool/Splash Pad", activity="swimming", cost="Fee charged (Spring Break-AISD through end of Oct): Resident $2 child", school="Marshall", zip="78723", latitude=30.30, longitude=-97.69),
    fac("Beta Park", type="Park", activity="Multi", school="Covington", zip="78745", latitude=30.20, longitude=-97.83),
    fac("Gamma Rec Center", type="Recreation Center", activity="fitness", cost="$10 per month", school="Marshall", zip="78723", latitude=30.31, longitude=-97.70),
    fac("Delta Trail", type="Trail", activity="walking", school="Dessau", zip="78754", latitude=30.37, longitude=-97.62),
    fac("Epsilon Dog Park", type="Dog Park", activity="Multi", school="Covington", zip="78745", latitude=30.21, longitude=-97.82),
] + [fac(f"Filler Park {i:02d}", school="Marshall", zip="78723") for i in range(20)]


def site():
    return make_site(SAMPLE)


def results(ctx):
    return js(ctx, "state.filtered.map(f => f.name)")


class BehaviorTests(unittest.TestCase):
    def test_starts_with_everything_shown(self):
        ctx = site()
        self.assertEqual(len(results(ctx)), len(SAMPLE))

    def test_dropdowns_are_built_from_the_data(self):
        ctx = site()
        self.assertEqual(sorted(js(ctx, "unique(state.facilities.map(f => f.school))")), ["Covington", "Dessau", "Marshall"])
        self.assertEqual(len(js(ctx, "unique(state.facilities.map(f => f.type))")), 5)

    def test_keyword_search_matches_name_type_zip_and_school(self):
        ctx = site()
        for kw, expect in [("alpha", {"Alpha Pool"}), ("trail", {"Delta Trail"}), ("78745", {"Beta Park", "Epsilon Dog Park"}), ("dessau", {"Delta Trail"})]:
            ctx.eval(f'elements.keyword.value = "{kw}"; applyFilters();')
            self.assertEqual(set(results(ctx)), expect, kw)

    def test_type_filter(self):
        ctx = site(); ctx.eval('elements.type.value = "Trail"; applyFilters();')
        self.assertEqual(results(ctx), ["Delta Trail"])

    def test_activity_filter(self):
        ctx = site(); ctx.eval('elements.activity.value = "swimming"; applyFilters();')
        self.assertEqual(results(ctx), ["Alpha Pool"])

    def test_school_filter(self):
        ctx = site(); ctx.eval('elements.school.value = "Covington"; applyFilters();')
        self.assertEqual(set(results(ctx)), {"Beta Park", "Epsilon Dog Park"})

    def test_filters_combine(self):
        ctx = site(); ctx.eval('elements.school.value = "Marshall"; elements.type.value = "Recreation Center"; applyFilters();')
        self.assertEqual(results(ctx), ["Gamma Rec Center"])

    def test_clear_filters_resets_everything(self):
        ctx = site()
        ctx.eval('elements.school.value = "Marshall"; elements.keyword.value = "pool"; applyFilters(); clearFilters();')
        self.assertEqual(len(results(ctx)), len(SAMPLE))
        self.assertEqual(js(ctx, "elements.school.value"), "")

    def test_no_match_shows_empty_state(self):
        ctx = site(); ctx.eval('elements.keyword.value = "zzzz"; applyFilters();')
        self.assertEqual(results(ctx), [])
        self.assertEqual(js(ctx, "elements.empty.hidden"), False)
        self.assertEqual(js(ctx, "elements.grid.hidden"), True)

    def test_result_count_wording(self):
        ctx = site(); ctx.eval('elements.keyword.value = "alpha"; applyFilters();')
        self.assertEqual(js(ctx, "elements.count.textContent"), "1 place")
        ctx.eval('elements.keyword.value = ""; applyFilters();')
        self.assertEqual(js(ctx, "elements.count.textContent"), f"{len(SAMPLE)} places")

    def test_sort_by_name(self):
        ctx = site(); ctx.eval('elements.sort.value = "name"; applyFilters();')
        names = results(ctx); self.assertEqual(names, sorted(names))

    def test_sort_by_cost_puts_cheapest_first_and_unlisted_last(self):
        ctx = site(); ctx.eval('elements.sort.value = "cost"; applyFilters();')
        names = results(ctx)
        self.assertEqual(names[:2], ["Alpha Pool", "Gamma Rec Center"])  # $2 then $10
        self.assertEqual(js(ctx, "state.filtered[2].cost"), "")        # missing cost is last, not free

    def test_pagination_shows_12_then_more(self):
        ctx = site()
        self.assertEqual(js(ctx, "state.visible"), 12)
        self.assertEqual(js(ctx, "elements.grid.innerHTML.split('facility-card').length - 1"), 12)
        self.assertEqual(js(ctx, "elements.showMore.hidden"), False)
        ctx.eval("state.visible += 12; renderResults();")  # 24 of 25 shown: button still needed
        self.assertEqual(js(ctx, "elements.showMore.hidden"), False)
        ctx.eval("state.visible += 12; renderResults();")  # all shown
        self.assertEqual(js(ctx, "elements.showMore.hidden"), True)

    def test_distance_radius_filter(self):
        ctx = site()
        ctx.eval('state.location = {latitude: 30.30, longitude: -97.69, label: "test"}; elements.radius.value = "2"; applyFilters();')
        names = set(results(ctx))
        self.assertIn("Alpha Pool", names); self.assertIn("Gamma Rec Center", names)
        self.assertNotIn("Beta Park", names); self.assertNotIn("Delta Trail", names)

    def test_haversine_distance_is_about_right(self):
        ctx = site()
        miles = js(ctx, "haversineMiles(30.2672, -97.7431, 30.2672, -97.6431)")  # 0.1 deg of longitude at Austin
        self.assertAlmostEqual(miles, 5.98, delta=0.1)

    def test_cost_text_helpers(self):
        ctx = site()
        self.assertEqual(js(ctx, 'shortCost("")'), "Cost not listed")
        self.assertEqual(js(ctx, 'shortCost("Court fees: Juniors $2")'), "Court fees")
        self.assertEqual(js(ctx, 'shortCost("Fee charged (Spring Break)")'), "Entry fee")
        self.assertEqual(js(ctx, 'shortCost("$5")'), "$5")
        self.assertEqual(js(ctx, 'minimumCost("Resident $2 child / $5 adult")'), 2)
        self.assertIsNone(js(ctx, 'minimumCost("")'))  # Infinity serialises to null

    def test_hours_text_helper(self):
        ctx = site()
        self.assertEqual(js(ctx, 'shortHours("")'), "Hours not listed")
        self.assertEqual(js(ctx, 'shortHours("5:00 AM–10:00 PM daily (general City of Austin park hours, Code 8)")'), "5:00 AM–10:00 PM daily")

    def test_card_text_is_escaped(self):
        ctx = make_site([fac('<script>alert(1)</script> Park')])
        html = js(ctx, "elements.grid.innerHTML")
        self.assertNotIn("<script>alert", html)
        self.assertIn("&lt;script&gt;", html)

    def test_card_shows_cost_unlisted_when_blank_and_never_free(self):
        ctx = make_site([fac("Plain Park")])
        html = js(ctx, "elements.grid.innerHTML")
        self.assertIn("Cost not listed", html)
        self.assertNotIn(">Free<", html)

    def test_card_notice_is_displayed(self):
        ctx = make_site([fac("Closed Pool", notice="Closed for the season")])
        self.assertIn("Closed for the season", js(ctx, "elements.grid.innerHTML"))

    def test_quick_facts_has_official_link_and_directions(self):
        ctx = make_site([fac("Linked Park", website="https://example.org/park")])
        ctx.eval("openFacts(0)")
        html = js(ctx, "elements.dialogContent.innerHTML")
        self.assertIn("https://example.org/park", html)
        self.assertIn("google.com/maps/search", html)
        self.assertIn("School area", html)

    def test_facility_without_website_falls_back_to_parks_directory(self):
        ctx = make_site([fac("No Link Park")])
        ctx.eval("openFacts(0)")
        self.assertIn("austintexas.gov/parks", js(ctx, "elements.dialogContent.innerHTML"))

    def test_todays_pick_skips_places_with_notices(self):
        ctx = make_site([fac("Noticed Park", notice="Closed"), fac("Fine Trail", type="Trail")])
        self.assertIn("Fine Trail", js(ctx, "elements.today.innerHTML"))
        self.assertNotIn("Noticed Park", js(ctx, "elements.today.innerHTML"))

    def test_map_points_skip_places_without_coordinates(self):
        ctx = make_site([fac("Mapped"), fac("Unmapped", latitude=None, longitude=None)])
        self.assertEqual(js(ctx, "elements.map.children.length"), 1)

    def test_site_loads_with_the_real_shipped_data(self):
        ctx = make_site()
        self.assertEqual(len(results(ctx)), len(embedded_facilities()))
        self.assertEqual(js(ctx, "elements.count.textContent").split()[0], str(len(embedded_facilities())))

    def test_bad_data_shows_friendly_error(self):
        ctx = make_site(facilities=None)
        ctx2 = __import__("quickjs").Context()
        from harness import FAKE_DOM, scripts
        ctx2.eval(FAKE_DOM); ctx2.eval("window.AMSC_FACILITIES = 'oops';"); ctx2.eval(scripts()[1])
        ctx2.eval("1")  # let the async initialize() settle
        ctx2.execute_pending_job() if hasattr(ctx2, "execute_pending_job") else None
        self.assertIn("unavailable", js(ctx2, "elements.count.textContent"))


if __name__ == "__main__":
    unittest.main()
