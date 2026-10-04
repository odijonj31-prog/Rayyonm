const tg = window.Telegram?.WebApp;

let CONFIG = { manager_username: "" };
let PORTFOLIO_ITEMS = [];
let ACTIVE_CATEGORY = "Barchasi";

function initTelegram() {
  if (!tg) return;
  tg.ready();
  tg.expand();
  try { tg.setHeaderColor("#0f0e0d"); } catch (e) {}
  try { tg.setBackgroundColor("#0f0e0d"); } catch (e) {}
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

async function apiGet(path) {
  const res = await fetch(path);
  return res.json();
}

async function apiPost(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  return res.json();
}

async function validateUser() {
  if (!tg || !tg.initData) return null;
  const data = await apiPost("/api/validate", { initData: tg.initData });
  return data.ok ? data.user : null;
}

async function loadConfig() {
  const data = await apiGet("/api/config");
  if (data.ok) CONFIG = data;
}

function setupManagerButton() {
  document.getElementById("manager-btn").addEventListener("click", () => {
    if (!CONFIG.manager_username) {
      tg?.showAlert?.("Menejer bilan bog'lanish hozircha sozlanmagan.");
      return;
    }
    tg?.openTelegramLink?.(`https://t.me/${CONFIG.manager_username}`);
  });
}

/* ============ PORTFOLIO: KATEGORIYA + GRID ============ */

async function loadPortfolio() {
  const data = await apiGet("/api/portfolio");
  if (!data.ok) return;
  PORTFOLIO_ITEMS = data.items || [];
  renderCategoryChips();
  renderPortfolioGrid();
}

function renderCategoryChips() {
  const container = document.getElementById("category-chips");
  const categories = ["Barchasi", ...new Set(PORTFOLIO_ITEMS.map(i => i.category || "Boshqa"))];
  if (PORTFOLIO_ITEMS.length === 0) { container.innerHTML = ""; return; }

  container.innerHTML = categories.map(cat => `
    <button class="category-chip ${cat === ACTIVE_CATEGORY ? 'active' : ''}" data-cat="${escapeHtml(cat)}">
      ${escapeHtml(cat)}
    </button>
  `).join("");

  container.querySelectorAll(".category-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      ACTIVE_CATEGORY = chip.dataset.cat;
      renderCategoryChips();
      renderPortfolioGrid();
    });
  });
}

function renderPortfolioGrid() {
  const grid = document.getElementById("portfolio-grid");
  const items = ACTIVE_CATEGORY === "Barchasi"
    ? PORTFOLIO_ITEMS
    : PORTFOLIO_ITEMS.filter(i => (i.category || "Boshqa") === ACTIVE_CATEGORY);

  if (!items.length) {
    grid.innerHTML = `<div class="empty-state"><div class="empty-icon">🖼</div><p>Bu bo'limda hali rasm yo'q</p></div>`;
    return;
  }

  grid.className = "portfolio-grid large";
  grid.innerHTML = items.map(item => `
    <div class="portfolio-card" data-id="${item.id}">
      <img src="${item.photo_url}" alt="${escapeHtml(item.title)}" loading="lazy" />
      <div class="portfolio-card-info">
        <p class="portfolio-card-title">${escapeHtml(item.title)}</p>
        ${item.style_tags ? `<p class="portfolio-card-tags">${escapeHtml(item.style_tags)}</p>` : ""}
      </div>
    </div>
  `).join("");

  grid.querySelectorAll(".portfolio-card").forEach(card => {
    card.addEventListener("click", () => openDetail(parseInt(card.dataset.id)));
  });
}

/* ============ DETAIL MODAL ============ */

function openDetail(itemId) {
  const item = PORTFOLIO_ITEMS.find(i => i.id === itemId);
  if (!item) return;

  document.getElementById("detail-image").src = item.photo_url;
  document.getElementById("detail-title").textContent = item.title;
  document.getElementById("detail-tags").textContent = item.style_tags || "";
  document.getElementById("detail-description").textContent = item.description || "";
  document.getElementById("detail-overlay").classList.remove("hidden");

  const selectBtn = document.getElementById("detail-select-btn");
  selectBtn.onclick = () => {
    if (tg?.sendData) {
      tg.sendData(JSON.stringify({ type: "portfolio_select", item_id: item.id }));
    } else {
      tg?.showAlert?.("Bu funksiya faqat Telegram ilovasida ishlaydi.");
    }
  };
  selectBtn.onclick = async () => {
    if (!tg?.initData) {
      tg?.showAlert?.("Bu funksiya faqat Telegram ilovasida ishlaydi.");
      return;
    }
    selectBtn.disabled = true;
    try {
      const data = await apiPost("/api/portfolio/select", { initData: tg.initData, item_id: item.id });
      if (data.ok) {
        tg.close();
        return;
      }
      tg.showAlert?.("Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.");
    } catch (e) {
      tg.showAlert?.("Aloqa xatosi. Iltimos, qayta urinib ko'ring.");
    }
    selectBtn.disabled = false;
  };

  if (tg?.HapticFeedback) { try { tg.HapticFeedback.impactOccurred("light"); } catch (e) {} }
}

function setupDetailClose() {
  document.getElementById("detail-close").addEventListener("click", () => {
    document.getElementById("detail-overlay").classList.add("hidden");
  });
  document.getElementById("detail-overlay").addEventListener("click", (e) => {
    if (e.target.id === "detail-overlay") {
      document.getElementById("detail-overlay").classList.add("hidden");
    }
  });
}

/* ============ TABS ============ */

function setupTabs() {
  document.querySelectorAll(".nav-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const tabId = btn.dataset.tab;
      document.querySelectorAll(".nav-btn").forEach(b => b.classList.toggle("active", b === btn));
      document.querySelectorAll(".tab-panel").forEach(p => p.classList.toggle("active", p.id === tabId));
      if (tg?.HapticFeedback) { try { tg.HapticFeedback.impactOccurred("light"); } catch (e) {} }
    });
  });
}

/* ============ MAIN ============ */

async function main() {
  initTelegram();
  setupTabs();
  setupManagerButton();
  setupDetailClose();

  await Promise.all([loadConfig(), validateUser(), loadPortfolio()]);

  document.getElementById("splash").classList.add("hidden");
  document.getElementById("app").classList.remove("hidden");
}

main();
