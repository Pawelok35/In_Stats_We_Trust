const navLinks = document.querySelectorAll(".nav-link");
const nav = document.querySelector(".primary-nav");
const navToggle = document.querySelector(".nav-toggle");
const signalsSection = document.querySelector("#signals");
const scrollButtons = document.querySelectorAll(".scroll-to-signals");
const faqItems = document.querySelectorAll(".faq-item");
const signalsCountEl = document.querySelector("[data-signals-count]");
const signalsLabelEl = document.querySelector("[data-signals-label]");
const signalsMetaEl = document.querySelector("[data-signals-meta]");
const bodyEl = document.querySelector("#signals-body");
const codenameFilter = document.querySelector("#filter-codename");
const seasonFilter = document.querySelector("#filter-season");
const resultFilter = document.querySelector("#filter-result");
const SIGNALS_ENDPOINT = "data/signals-week12.json";

let signalsData = [];

// Smooth scroll for nav links
if (nav) {
  navLinks.forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      const target = document.querySelector(link.getAttribute("href"));
      if (target) {
        target.scrollIntoView({ behavior: "smooth" });
        nav.classList.remove("open");
        navToggle?.setAttribute("aria-expanded", "false");
      }
    });
  });
}

// Mobile nav toggle
if (nav && navToggle) {
  navToggle.addEventListener("click", () => {
    const expanded = navToggle.getAttribute("aria-expanded") === "true";
    navToggle.setAttribute("aria-expanded", String(!expanded));
    nav.classList.toggle("open");
  });
}

// Buttons that jump to the signals section
scrollButtons.forEach((button) => {
  button.addEventListener("click", () => {
    if (signalsSection) {
      signalsSection.scrollIntoView({ behavior: "smooth" });
    }
  });
});

// Active nav highlight on scroll
const sections = document.querySelectorAll("main section");
if (sections.length) {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        const id = entry.target.getAttribute("id");
        if (entry.isIntersecting && id) {
          navLinks.forEach((link) => link.classList.remove("active"));
          const activeLink = document.querySelector(`.nav-link[href="#${id}"]`);
          if (activeLink) {
            activeLink.classList.add("active");
          }
        }
      });
    },
    { threshold: 0.4 },
  );
  sections.forEach((section) => observer.observe(section));
}

// FAQ accordion
faqItems.forEach((item) => {
  const button = item.querySelector("button");
  if (!button) {
    return;
  }
  button.addEventListener("click", () => {
    const isOpen = item.classList.contains("open");
    faqItems.forEach((faq) => {
      faq.classList.remove("open");
      const trigger = faq.querySelector("button");
      if (trigger) {
        trigger.setAttribute("aria-expanded", "false");
      }
    });
    if (!isOpen) {
      item.classList.add("open");
      button.setAttribute("aria-expanded", "true");
    }
  });
});

function getFilteredSignals() {
  const codenameValue = codenameFilter?.value ?? "all";
  const seasonValue = seasonFilter?.value ?? "all";
  const resultValue = resultFilter?.value ?? "all";

  return signalsData.filter((item) => {
    const codenameMatch = codenameValue === "all" || item.codename === codenameValue;
    const seasonMatch = seasonValue === "all" || String(item.season) === seasonValue;
    const resultMatch = resultValue === "all" || item.result === resultValue;
    return codenameMatch && seasonMatch && resultMatch;
  });
}

function renderTable() {
  if (!bodyEl) return;
  if (!signalsData.length) {
    bodyEl.innerHTML =
      '<tr><td colspan="8">No Weather Scale signals have been published yet.</td></tr>';
    return;
  }

  const filtered = getFilteredSignals();

  if (!filtered.length) {
    bodyEl.innerHTML =
      '<tr><td colspan="8">No signals match the current filters. Adjust the filters to continue.</td></tr>';
    return;
  }

  bodyEl.innerHTML = filtered
    .map(
      (item) => `
        <tr>
          <td>${item.date}</td>
          <td>${item.season}</td>
          <td>${item.week}</td>
          <td>${item.codename}</td>
          <td>${item.matchup}</td>
          <td>${item.direction}</td>
          <td>${item.result}</td>
          <td>${item.score}</td>
        </tr>
      `,
    )
    .join("");
}

function populateSeasonFilter() {
  if (!seasonFilter) return;
  const seasons = Array.from(new Set(signalsData.map((item) => item.season))).sort((a, b) => b - a);

  seasonFilter.innerHTML = "";
  const allOption = document.createElement("option");
  allOption.value = "all";
  allOption.textContent = "All seasons";
  seasonFilter.appendChild(allOption);

  seasons.forEach((season) => {
    const option = document.createElement("option");
    option.value = String(season);
    option.textContent = String(season);
    seasonFilter.appendChild(option);
  });
}

function updateSignalStats() {
  if (!signalsData.length) return;
  const actionable = signalsData.filter((item) => item.codename !== "Ultimate Supercell");
  if (signalsCountEl) {
    signalsCountEl.textContent = actionable.length.toString();
  }
  if (signalsLabelEl) {
    const latestWeek = actionable[0]?.week ?? signalsData[0].week;
    signalsLabelEl.textContent = `Signals logged for Week ${latestWeek}`;
  }
  if (signalsMetaEl) {
    const latest = actionable[0] ?? signalsData[0];
    const updatedAt = new Date(latest.date);
    const formattedDate = Number.isNaN(updatedAt.valueOf())
      ? latest.date
      : updatedAt.toLocaleDateString("en-US", {
          month: "short",
          day: "numeric",
          year: "numeric",
        });
    signalsMetaEl.textContent = `Latest batch: Week ${latest.week}, Season ${latest.season} · Updated ${formattedDate}`;
  }
}

async function loadSignalsData() {
  if (!bodyEl) return;
  bodyEl.innerHTML = '<tr><td colspan="8">Loading Weather Scale signals…</td></tr>';
  try {
    const response = await fetch(SIGNALS_ENDPOINT, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Failed to fetch signals (${response.status})`);
    }
    const payload = await response.json();
    signalsData = Array.isArray(payload) ? payload : [];
    updateSignalStats();
    populateSeasonFilter();
    renderTable();
  } catch (error) {
    console.error("Unable to load signals", error);
    bodyEl.innerHTML =
      '<tr><td colspan="8">Unable to load Weather Scale signals right now. Please refresh.</td></tr>';
  }
}

codenameFilter?.addEventListener("change", renderTable);
seasonFilter?.addEventListener("change", renderTable);
resultFilter?.addEventListener("change", renderTable);

document.addEventListener("DOMContentLoaded", () => {
  loadSignalsData();
});
