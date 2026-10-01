const navLinks = document.querySelectorAll(".nav-link");
const panels = document.querySelectorAll(".panel");
const chips = document.querySelectorAll(".chip");
const tickerList = document.getElementById("ticker-list");
const modules = document.querySelectorAll(".module");
const revealNodes = document.querySelectorAll(".reveal");
const exploreButton = document.getElementById("explore-button");
const modulesButton = document.getElementById("modules-button");
const modulesSection = document.getElementById("modules-section");
const dashboardSection = document.getElementById("dashboard-section");

const marketStates = [
  [
    { item: "Black Dieci", state: "Stable" },
    { item: "Dueling Dragons", state: "Rising" },
    { item: "TW Octane", state: "Hot" },
  ],
  [
    { item: "Cristiano", state: "Watching" },
    { item: "Standard Boost", state: "Moving" },
    { item: "Interstellar", state: "Strong" },
  ],
  [
    { item: "Fennec", state: "Popular" },
    { item: "Shattered", state: "Upward" },
    { item: "Zomba", state: "Stable" },
  ],
];

function setActivePanel(target) {
  navLinks.forEach((link) => {
    link.classList.toggle("active", link.dataset.target === target);
  });

  panels.forEach((panel) => {
    panel.classList.toggle("active", panel.dataset.panel === target);
  });

  modules.forEach((module) => {
    const matches = module.dataset.view === target;
    const isDashboard = target === "dashboard";

    module.classList.toggle("is-active", matches || (isDashboard && matches));
    module.classList.toggle("is-muted", !isDashboard && !matches);
  });
}

navLinks.forEach((link) => {
  link.addEventListener("click", () => setActivePanel(link.dataset.target));
});

chips.forEach((chip) => {
  chip.addEventListener("click", () => {
    chips.forEach((node) => node.classList.remove("active"));
    chip.classList.add("active");
  });
});

let tickerIndex = 0;

function renderTicker(items) {
  tickerList.innerHTML = "";

  items.forEach(({ item, state }) => {
    const row = document.createElement("div");
    row.className = "ticker-item";
    row.innerHTML = `<span>${item}</span><strong>${state}</strong>`;
    tickerList.appendChild(row);
  });
}

setInterval(() => {
  tickerIndex = (tickerIndex + 1) % marketStates.length;
  renderTicker(marketStates[tickerIndex]);
}, 3200);

const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.2 }
);

revealNodes.forEach((node) => observer.observe(node));

exploreButton.addEventListener("click", () => {
  dashboardSection.scrollIntoView({ behavior: "smooth", block: "start" });
});

modulesButton.addEventListener("click", () => {
  modulesSection.scrollIntoView({ behavior: "smooth", block: "start" });
});

document.body.classList.add("loaded");
setActivePanel("dashboard");
