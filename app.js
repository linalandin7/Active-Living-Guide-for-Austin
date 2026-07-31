const PARKS_DIRECTORY = "https://www.austintexas.gov/parks";

const typeImages = {
  Park: "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=900&q=78",
  Trail: "https://images.unsplash.com/photo-1551632811-561732d1e306?auto=format&fit=crop&w=900&q=78",
  "Pool/Splash Pad": "https://images.unsplash.com/photo-1530053969600-caed2596d242?auto=format&fit=crop&w=900&q=78",
  "Dog Park": "https://images.unsplash.com/photo-1558788353-f76d92427f16?auto=format&fit=crop&w=900&q=78",
  "Nature Center/Preserve": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=900&q=78",
  "Recreation Center": "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?auto=format&fit=crop&w=900&q=78",
  "Sports Facility": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?auto=format&fit=crop&w=900&q=78",
};

const fallbackImage =
  "https://images.unsplash.com/photo-1533777324565-a040eb52facd?auto=format&fit=crop&w=900&q=78";

const state = {
  facilities: [],
  filtered: [],
  visible: 12,
  location: null,
  featuredIndex: 0,
};

const elements = {
  searchForm: document.querySelector("#search-form"),
  keyword: document.querySelector("#keyword-input"),
  location: document.querySelector("#location-input"),
  radius: document.querySelector("#radius-select"),
  locationStatus: document.querySelector("#location-status"),
  useLocation: document.querySelector("#use-location"),
  type: document.querySelector("#type-filter"),
  activity: document.querySelector("#activity-filter"),
  school: document.querySelector("#school-filter"),
  sort: document.querySelector("#sort-select"),
  clear: document.querySelector("#clear-filters"),
  emptyClear: document.querySelector("#empty-clear"),
  grid: document.querySelector("#facility-grid"),
  empty: document.querySelector("#empty-state"),
  count: document.querySelector("#results-count"),
  showMore: document.querySelector("#show-more"),
  filters: document.querySelector("#active-filters"),
  facilityMenu: document.querySelector("#facility-menu"),
  map: document.querySelector("#map-canvas"),
  today: document.querySelector("#today-card"),
  surprise: document.querySelector("#surprise-me"),
  dialog: document.querySelector("#facts-dialog"),
  dialogContent: document.querySelector("#dialog-content"),
  dialogClose: document.querySelector("#dialog-close"),
  toast: document.querySelector("#toast"),
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function unique(values) {
  return [...new Set(values.filter(Boolean))].sort((a, b) => a.localeCompare(b));
}

function imageFor(type) {
  return typeImages[type] ?? fallbackImage;
}

function addressFor(facility) {
  return [facility.address, facility.city, facility.zip].filter(Boolean).join(", ");
}

function shortHours(hours) {
  if (!hours) return "Hours not listed";
  return hours.replace(/\s*\(general City of Austin park hours.*$/i, "").trim();
}

function shortCost(cost) {
  if (!cost) return "Cost not listed";
  if (/18-hole/i.test(cost)) return "Golf course fees";
  if (/court fees/i.test(cost)) return "Court fees";
  if (/fee charged/i.test(cost)) return "Entry fee";
  return cost.length > 36 ? "Fee information available" : cost;
}

function minimumCost(cost) {
  if (!cost) return Number.POSITIVE_INFINITY;
  const values = [...cost.matchAll(/\$(\d+(?:\.\d+)?)/g)].map((match) => Number(match[1]));
  return values.length ? Math.min(...values) : Number.POSITIVE_INFINITY;
}

function haversineMiles(lat1, lon1, lat2, lon2) {
  const toRadians = (degrees) => (degrees * Math.PI) / 180;
  const radius = 3958.8;
  const dLat = toRadians(lat2 - lat1);
  const dLon = toRadians(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRadians(lat1)) *
      Math.cos(toRadians(lat2)) *
      Math.sin(dLon / 2) ** 2;
  return radius * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function optionMarkup(value) {
  return `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`;
}

function populateControls() {
  const types = unique(state.facilities.map((facility) => facility.type));
  const activities = unique(state.facilities.map((facility) => facility.activity));
  const schools = unique(state.facilities.map((facility) => facility.school));

  elements.type.insertAdjacentHTML("beforeend", types.map(optionMarkup).join(""));
  elements.activity.insertAdjacentHTML("beforeend", activities.map(optionMarkup).join(""));
  elements.school.insertAdjacentHTML("beforeend", schools.map(optionMarkup).join(""));
  elements.facilityMenu.innerHTML = [
    '<button type="button" data-menu-type="">View all facilities</button>',
    ...types.map(
      (type) =>
        `<button type="button" data-menu-type="${escapeHtml(type)}">${escapeHtml(type)}</button>`,
    ),
  ].join("");
}

function searchableText(facility) {
  return [
    facility.name,
    facility.type,
    facility.activity,
    facility.address,
    facility.city,
    facility.zip,
    facility.school,
    facility.parentName,
  ]
    .join(" ")
    .toLowerCase();
}

function applyFilters({ resetVisible = true } = {}) {
  const keyword = elements.keyword.value.trim().toLowerCase();
  const type = elements.type.value;
  const activity = elements.activity.value;
  const school = elements.school.value;
  const radius = Number(elements.radius.value);

  let results = state.facilities.map((facility) => {
    const distance =
      state.location && facility.latitude !== null && facility.longitude !== null
        ? haversineMiles(
            state.location.latitude,
            state.location.longitude,
            facility.latitude,
            facility.longitude,
          )
        : null;
    return { ...facility, distance };
  });

  results = results.filter((facility) => {
    if (keyword && !searchableText(facility).includes(keyword)) return false;
    if (type && facility.type !== type) return false;
    if (activity && facility.activity !== activity) return false;
    if (school && facility.school !== school) return false;
    if (state.location && (facility.distance === null || facility.distance > radius)) return false;
    return true;
  });

  if (elements.sort.value === "name") {
    results.sort((a, b) => a.name.localeCompare(b.name));
  } else if (elements.sort.value === "distance" && state.location) {
    results.sort((a, b) => (a.distance ?? Infinity) - (b.distance ?? Infinity));
  } else if (elements.sort.value === "cost") {
    results.sort((a, b) => minimumCost(a.cost) - minimumCost(b.cost) || a.name.localeCompare(b.name));
  } else if (state.location) {
    results.sort((a, b) => (a.distance ?? Infinity) - (b.distance ?? Infinity));
  }

  state.filtered = results;
  if (resetVisible) state.visible = 12;
  renderResults();
  renderActiveFilters();
  renderMap();
}

function renderResults() {
  const visible = state.filtered.slice(0, state.visible);
  elements.count.textContent = `${state.filtered.length} ${state.filtered.length === 1 ? "place" : "places"}`;
  elements.grid.innerHTML = visible.map(cardMarkup).join("");
  elements.grid.hidden = state.filtered.length === 0;
  elements.empty.hidden = state.filtered.length !== 0;
  elements.showMore.hidden = state.visible >= state.filtered.length || state.filtered.length === 0;
}

function cardMarkup(facility) {
  const distance =
    facility.distance === null
      ? ""
      : `<span class="card-distance">${facility.distance.toFixed(1)} mi</span>`;
  const notice = facility.notice
    ? `<p class="card-notice">${escapeHtml(facility.notice)}</p>`
    : "";
  return `
    <article class="facility-card">
      <div class="card-image" style="background-image:url('${imageFor(facility.type)}')">
        <span class="card-type">${escapeHtml(facility.type)}</span>
        ${distance}
      </div>
      <div class="card-body">
        <h3>${escapeHtml(facility.name)}</h3>
        <p class="card-address">${escapeHtml(addressFor(facility) || "Address not listed")}</p>
        <div class="card-meta">
          <span class="meta-pill">${escapeHtml(facility.activity || "Activity not listed")}</span>
          <span class="meta-pill">${escapeHtml(shortCost(facility.cost))}</span>
        </div>
        ${notice}
        <button class="facts-button" type="button" data-facility-index="${facility.index}">Quick facts</button>
      </div>
    </article>`;
}

function renderActiveFilters() {
  const chips = [];
  if (elements.keyword.value.trim()) chips.push(`Keyword: ${elements.keyword.value.trim()}`);
  if (elements.type.value) chips.push(elements.type.value);
  if (elements.activity.value) chips.push(`Activity: ${elements.activity.value}`);
  if (elements.school.value) chips.push(`School: ${elements.school.value}`);
  if (state.location) chips.push(`Within ${elements.radius.value} miles of ${state.location.label}`);
  elements.filters.innerHTML = chips
    .map((chip) => `<span class="filter-chip">${escapeHtml(chip)}</span>`)
    .join("");
}

function renderMap() {
  const points = state.filtered.filter(
    (facility) => facility.latitude !== null && facility.longitude !== null,
  );
  if (!points.length) {
    elements.map.innerHTML = "";
    return;
  }
  const latitudes = points.map((point) => point.latitude);
  const longitudes = points.map((point) => point.longitude);
  const minLat = Math.min(...latitudes);
  const maxLat = Math.max(...latitudes);
  const minLon = Math.min(...longitudes);
  const maxLon = Math.max(...longitudes);
  const latSpan = maxLat - minLat || 1;
  const lonSpan = maxLon - minLon || 1;

  elements.map.innerHTML = "";
  points.slice(0, 100).forEach((facility) => {
    const dot = document.createElement("button");
    dot.className = "map-dot";
    dot.type = "button";
    dot.title = facility.name;
    dot.setAttribute("aria-label", `Open quick facts for ${facility.name}`);
    dot.style.left = `${6 + ((facility.longitude - minLon) / lonSpan) * 88}%`;
    dot.style.top = `${94 - ((facility.latitude - minLat) / latSpan) * 88}%`;
    dot.addEventListener("click", () => openFacts(facility.index));
    elements.map.append(dot);
  });
}

function renderToday() {
  const candidates = state.facilities.filter(
    (facility) => !facility.notice && ["Park", "Trail", "Nature Center/Preserve"].includes(facility.type),
  );
  if (!candidates.length) return;
  const dayIndex = Math.floor(Date.now() / 86400000);
  const facility = candidates[(dayIndex + state.featuredIndex) % candidates.length];
  elements.today.innerHTML = `
    <div class="today-image" style="background-image:url('${imageFor(facility.type)}')"></div>
    <div class="today-copy">
      <span class="type-badge">${escapeHtml(facility.type)}</span>
      <h3>${escapeHtml(facility.name)}</h3>
      <p>${escapeHtml(addressFor(facility) || "Address not listed")} · ${escapeHtml(facility.activity || "Explore")}</p>
      <div class="today-actions">
        <button class="light-button" type="button" data-featured-index="${facility.index}">See quick facts</button>
        <a class="text-link" href="#explore">Browse all places →</a>
      </div>
    </div>`;
}

function factItem(label, value) {
  if (!value) return "";
  return `<div class="fact-item"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`;
}

function openFacts(index) {
  const facility = state.facilities.find((item) => item.index === Number(index));
  if (!facility) return;
  const officialLink = facility.website || PARKS_DIRECTORY;
  const mapQuery = encodeURIComponent(addressFor(facility) || facility.name);
  elements.dialogContent.innerHTML = `
    <div class="dialog-image" style="background-image:url('${imageFor(facility.type)}')"></div>
    <div class="dialog-body">
      <span class="type-badge">${escapeHtml(facility.type)}</span>
      <h2>${escapeHtml(facility.name)}</h2>
      <p class="dialog-address">${escapeHtml(addressFor(facility) || "Address not listed")}</p>
      <div class="fact-list">
        ${factItem("Activity", facility.activity || "Not listed")}
        ${factItem("Cost", facility.cost || "Cost not listed")}
        ${factItem("Days", facility.days || "Not listed")}
        ${factItem("Hours", shortHours(facility.hours))}
        ${factItem("School area", facility.school || "Not listed")}
        ${factItem("Located within", facility.parentName)}
      </div>
      ${facility.notice ? `<p class="dialog-notice">${escapeHtml(facility.notice)}</p>` : ""}
      <div class="dialog-actions">
        <a href="${escapeHtml(officialLink)}" target="_blank" rel="noreferrer">Official information ↗</a>
        <a href="https://www.google.com/maps/search/?api=1&query=${mapQuery}" target="_blank" rel="noreferrer">Get directions ↗</a>
      </div>
    </div>`;
  elements.dialog.showModal();
}

function showToast(message) {
  elements.toast.textContent = message;
  elements.toast.classList.add("visible");
  window.setTimeout(() => elements.toast.classList.remove("visible"), 2600);
}

function setLocationStatus(message, isError = false) {
  elements.locationStatus.textContent = message;
  elements.locationStatus.style.color = isError ? "#9f3514" : "";
}

function normalizeAddress(value) {
  return value.toLowerCase().replace(/[^a-z0-9]/g, "");
}

async function resolveTypedLocation() {
  const query = elements.location.value.trim();
  if (!query) {
    state.location = null;
    setLocationStatus("");
    applyFilters();
    return true;
  }

  setLocationStatus("Finding that location…");
  const zipMatch = query.match(/\b\d{5}\b/);
  if (zipMatch) {
    const matches = state.facilities.filter(
      (facility) =>
        facility.zip === zipMatch[0] && facility.latitude !== null && facility.longitude !== null,
    );
    if (matches.length) {
      state.location = {
        latitude: matches.reduce((sum, item) => sum + item.latitude, 0) / matches.length,
        longitude: matches.reduce((sum, item) => sum + item.longitude, 0) / matches.length,
        label: zipMatch[0],
      };
      setLocationStatus(`Showing places near ${zipMatch[0]}.`);
      applyFilters();
      return true;
    }
  }

  const normalizedQuery = normalizeAddress(query);
  const addressMatch = state.facilities.find((facility) => {
    if (facility.latitude === null || facility.longitude === null) return false;
    const candidate = normalizeAddress(`${facility.address}${facility.city}${facility.zip}`);
    const facilityAddress = normalizeAddress(facility.address);
    return candidate.includes(normalizedQuery) ||
      (facilityAddress && normalizedQuery.includes(facilityAddress));
  });
  if (addressMatch) {
    state.location = {
      latitude: addressMatch.latitude,
      longitude: addressMatch.longitude,
      label: addressMatch.address,
    };
    setLocationStatus(`Showing places near ${addressMatch.address}.`);
    applyFilters();
    return true;
  }

  try {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&countrycodes=us&q=${encodeURIComponent(`${query}, Austin area, Texas`)}`,
      { headers: { Accept: "application/json" } },
    );
    if (!response.ok) throw new Error("Location lookup failed");
    const [result] = await response.json();
    if (!result) throw new Error("No location found");
    state.location = {
      latitude: Number(result.lat),
      longitude: Number(result.lon),
      label: query,
    };
    setLocationStatus(`Showing places near ${query}.`);
    applyFilters();
    return true;
  } catch {
    state.location = null;
    setLocationStatus("We couldn’t find that address. Try a five-digit ZIP code.", true);
    applyFilters();
    return false;
  }
}

function useBrowserLocation() {
  if (!navigator.geolocation) {
    setLocationStatus("Location services are not available in this browser.", true);
    return;
  }
  setLocationStatus("Requesting your location…");
  navigator.geolocation.getCurrentPosition(
    ({ coords }) => {
      state.location = {
        latitude: coords.latitude,
        longitude: coords.longitude,
        label: "your current location",
      };
      elements.location.value = "My location";
      setLocationStatus("Showing nearby places.");
      applyFilters();
    },
    () => setLocationStatus("Location access was not available. Try entering a ZIP code.", true),
    { enableHighAccuracy: false, timeout: 10000 },
  );
}

function clearFilters() {
  elements.keyword.value = "";
  elements.location.value = "";
  elements.radius.value = "10";
  elements.type.value = "";
  elements.activity.value = "";
  elements.school.value = "";
  elements.sort.value = "recommended";
  state.location = null;
  setLocationStatus("");
  applyFilters();
}

function selectType(type) {
  elements.type.value = type;
  applyFilters();
  document.querySelector("#explore").scrollIntoView({ behavior: "smooth", block: "start" });
}

function bindEvents() {
  elements.keyword.addEventListener("input", () => applyFilters());
  [elements.type, elements.activity, elements.school, elements.radius].forEach((control) =>
    control.addEventListener("change", () => applyFilters()),
  );
  elements.sort.addEventListener("change", () => {
    if (elements.sort.value === "distance" && !state.location) {
      elements.sort.value = "recommended";
      showToast("Enter a ZIP code or address before sorting by distance.");
      elements.location.focus();
      return;
    }
    applyFilters();
  });
  elements.searchForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    await resolveTypedLocation();
    document.querySelector("#explore").scrollIntoView({ behavior: "smooth", block: "start" });
  });
  elements.useLocation.addEventListener("click", useBrowserLocation);
  elements.clear.addEventListener("click", clearFilters);
  elements.emptyClear.addEventListener("click", clearFilters);
  elements.showMore.addEventListener("click", () => {
    state.visible += 12;
    renderResults();
  });
  elements.surprise.addEventListener("click", () => {
    state.featuredIndex += 1;
    renderToday();
  });
  elements.dialogClose.addEventListener("click", () => elements.dialog.close());
  elements.dialog.addEventListener("click", (event) => {
    if (event.target === elements.dialog) elements.dialog.close();
  });

  document.addEventListener("click", (event) => {
    const factsButton = event.target.closest("[data-facility-index]");
    if (factsButton) openFacts(factsButton.dataset.facilityIndex);
    const featuredButton = event.target.closest("[data-featured-index]");
    if (featuredButton) openFacts(featuredButton.dataset.featuredIndex);
    const menuButton = event.target.closest("[data-menu-type]");
    if (menuButton) {
      selectType(menuButton.dataset.menuType);
      menuButton.closest("details")?.removeAttribute("open");
    }
    const challenge = event.target.closest("[data-challenge-type]");
    if (challenge) selectType(challenge.dataset.challengeType);
    const scrollButton = event.target.closest("[data-scroll-to]");
    if (scrollButton) document.querySelector(`#${scrollButton.dataset.scrollTo}`)?.scrollIntoView({ behavior: "smooth" });
    const comingSoon = event.target.closest("[data-coming-soon]");
    if (comingSoon) showToast(`${comingSoon.dataset.comingSoon} will be added in a future version.`);
  });
}

async function initialize() {
  try {
    let facilities = window.AMSC_FACILITIES;
    if (!Array.isArray(facilities)) {
      const response = await fetch("data/facilities.json");
      if (!response.ok) throw new Error("Facility data could not be loaded");
      facilities = await response.json();
    }
    state.facilities = facilities.map((facility, index) => ({ ...facility, index }));
    populateControls();
    renderToday();
    bindEvents();
    applyFilters();
  } catch (error) {
    elements.count.textContent = "Facility data unavailable";
    elements.grid.innerHTML = `<div class="empty-state"><h3>We couldn’t load the directory.</h3><p>${escapeHtml(error.message)}</p></div>`;
    elements.showMore.hidden = true;
  }
}

initialize();
