"""Test helpers: read index.html and run the site's own JavaScript in a fake browser.

The site is a single static page. Its facility data lives in the first <script> block
(window.AMSC_FACILITIES) and its behavior in the second. We run both in QuickJS with a tiny
fake DOM so the real filter/sort/search functions are tested without a browser.
"""
import json
import pathlib
import re

import quickjs

ROOT = pathlib.Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"

FAKE_DOM = r"""
var __els = {};
function __makeEl(id) {
  var el = {
    _id: id, value: "", hidden: false, textContent: "", innerHTML: "", dataset: {}, style: {},
    className: "", children: [], disabled: false,
    classList: { add: function(){}, remove: function(){}, toggle: function(){}, contains: function(){ return false; } },
    addEventListener: function(){}, removeEventListener: function(){}, setAttribute: function(){},
    getAttribute: function(){ return null; }, removeAttribute: function(){}, append: function(c){ el.children.push(c); },
    appendChild: function(c){ el.children.push(c); },
    insertAdjacentHTML: function(pos, html){ el.innerHTML += html; },
    querySelector: function(){ return __makeEl("child"); }, querySelectorAll: function(){ return []; },
    closest: function(){ return null; }, focus: function(){}, scrollIntoView: function(){},
    showModal: function(){ el.open = true; }, close: function(){ el.open = false; }, remove: function(){}
  };
  return el;
}
var document = {
  querySelector: function(sel){ if (!__els[sel]) __els[sel] = __makeEl(sel); return __els[sel]; },
  querySelectorAll: function(){ return []; },
  createElement: function(t){ return __makeEl(t); },
  addEventListener: function(){},
  getElementById: function(id){ return document.querySelector("#" + id); },
  body: __makeEl("body"), documentElement: __makeEl("html")
};
var window = { addEventListener: function(){}, setTimeout: function(){ return 0; }, location: { hash: "" },
  matchMedia: function(){ return { matches: false, addEventListener: function(){} }; }, scrollTo: function(){} };
var navigator = { geolocation: { getCurrentPosition: function(){} } };
var console = { log: function(){}, warn: function(){}, error: function(){} };
var fetch = function(){ return Promise.reject(new Error("no network in tests")); };
var IntersectionObserver = function(){ this.observe = function(){}; };
"""


def read_html():
    return INDEX.read_text(encoding="utf-8")


def scripts():
    """Return the inline <script> blocks of index.html (data script first, logic script second)."""
    return re.findall(r"<script>(.*?)</script>", read_html(), re.S)


def embedded_facilities():
    """The facility list embedded in index.html, parsed as JSON."""
    m = re.search(r"window\.AMSC_FACILITIES = (\[.*?\n\]);", read_html(), re.S)
    if not m:
        raise AssertionError("index.html has no window.AMSC_FACILITIES array")
    return json.loads(m.group(1))


def make_site(facilities=None):
    """Load the site's JavaScript into a fresh QuickJS context. Pass `facilities` to use test data."""
    ctx = quickjs.Context()
    ctx.eval(FAKE_DOM)
    data_js, logic_js = scripts()[0], scripts()[1]
    if facilities is not None:
        data_js = "window.AMSC_FACILITIES = " + json.dumps(facilities) + ";"
    ctx.eval(data_js)
    ctx.eval(logic_js)
    return ctx


def js(ctx, expression):
    """Evaluate JS and return a plain Python value (objects come back as JSON-decoded)."""
    out = ctx.eval("JSON.stringify(" + expression + ")")
    return json.loads(out) if out is not None else None


def fac(name, **kw):
    base = {"name": name, "type": "Park", "activity": "Multi", "cost": "", "address": "1 Test St.", "city": "Austin",
            "zip": "78701", "longitude": -97.74, "latitude": 30.27, "days": "Daily", "hours": "", "website": "",
            "school": "Marshall", "parentName": "", "notice": ""}
    base.update(kw)
    return base
