# Where the site data comes from

- Source: the `Cards` tab of `Active_Living_Database_v13.xlsx` (Active_Living_Website_Database/Working), built 2026-10-22.
- Scope: places and programs inside, near (within 1 mile) or nearby (1-2 miles) the attendance boundaries of Covington MS,
  General Marshall MS and Dessau MS. Marshall's boundary is an Austin ISD proposal (provisional); other boundary versions
  are still being confirmed.
- Status: every card is `release: "Hold"` with a `holdReason` (geographic eligibility not yet cleared). No card is approved for
  publication, and only a few records have had an independent source review. The page does not display this status.
  Extra fields (`cardId`, `recordId`, `provider`, `role`, `areas`, `sourceCheck`, `independentReview`, `release`,
  `holdReason`, `launchPriority`) are carried for later use and are not shown on the page.
- Site format is unchanged. Programs are filed under the closest existing facility type because the page has no Program type yet.
- Regenerate with `Active_Living_Website_Database/Tools/export_site_data.py WORKBOOK.xlsx REPO_DIR` (one folder over from this one), then run the tests.
- Nothing on this site comes from the old `PA Resource Guide Project` folder.
