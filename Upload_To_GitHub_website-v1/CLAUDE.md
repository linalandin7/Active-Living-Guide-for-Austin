# Active Living Guide for Austin (AMSC Activity Guide)

A static website (one `index.html` page, deployed through GitHub and Vercel) that helps students, families and
community members find places and programs for physical activity near Covington, Marshall and Dessau Middle Schools.

- Page and behavior: `index.html` (its data lives in `window.AMSC_FACILITIES`). `facilities.json` and `facilities.js` are
  copies of that same data and must stay identical to it.
- Data comes from the working Excel database (`Cards` tab of the latest pilot workbook). See `DATA_SOURCE.md`.
- Do not change the page design or the filters unless Lina asks. Do not push to `main` or publish without her go-ahead.

## Run the tests
    pip install -r requirements-dev.txt
    python3 tests/run_all.py

## Testing rules
- Write tests for every new feature.
- Run all tests before finishing any change. Don't push if any fail.
- Never change or delete a test to make it pass without asking me.
