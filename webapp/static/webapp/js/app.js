(function () {
  "use strict";

  const tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;
  const API_BASE = "/app/api";

  const state = {
    bootstrap: null,
    activeTab: "searches",
    wizard: { step: 1, keyword: "", providers: new Set(), city: null, jobTypes: new Set() },
  };

  function el(id) {
    return document.getElementById(id);
  }

  function getInitData() {
    return tg ? tg.initData : "";
  }

  async function apiGet(path) {
    const res = await fetch(API_BASE + path, {
      headers: { "X-Telegram-Init-Data": getInitData() },
    });
    return res.json();
  }

  async function apiPost(path, body) {
    const res = await fetch(API_BASE + path, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Telegram-Init-Data": getInitData(),
      },
      body: JSON.stringify(body || {}),
    });
    return res.json();
  }

  function applyTheme() {
    if (!tg) return;
    document.documentElement.setAttribute("data-theme", tg.colorScheme || "light");
    const params = tg.themeParams || {};
    const root = document.documentElement.style;
    const map = {
      bg_color: "--bg",
      secondary_bg_color: "--secondary-bg",
      text_color: "--text",
      hint_color: "--hint",
      link_color: "--link",
      button_color: "--button",
      button_text_color: "--button-text",
      section_bg_color: "--section-bg",
      destructive_text_color: "--destructive",
    };
    Object.keys(map).forEach((key) => {
      if (params[key]) root.setProperty(map[key], params[key]);
    });
  }

  function showJoin(data) {
    el("view-loading").classList.add("hidden");
    el("view-join").classList.remove("hidden");
    el("view-main").classList.add("hidden");
    el("join-channel-name").textContent = "@" + data.channel_username;
    el("join-channel-link").href = "https://t.me/" + data.channel_username;
  }

  function showMain() {
    el("view-loading").classList.add("hidden");
    el("view-join").classList.add("hidden");
    el("view-main").classList.remove("hidden");
  }

  function goTo(tab) {
    state.activeTab = tab;
    document.querySelectorAll("#content > .view").forEach((v) => v.classList.add("hidden"));
    el("view-" + tab).classList.remove("hidden");
    document.querySelectorAll(".nav-btn").forEach((b) => {
      b.classList.toggle("active", b.dataset.go === tab);
    });
    if (tab === "add") resetWizard();
    updateWizardControls();
  }

  document.querySelectorAll("[data-go]").forEach((btn) => {
    btn.addEventListener("click", () => goTo(btn.dataset.go));
  });

  // ---------- Wizard ----------

  function choiceItem(label, single) {
    const div = document.createElement("div");
    div.className = "choice-item" + (single ? " single" : "");
    const check = document.createElement("span");
    check.className = "check";
    check.textContent = "✓";
    const text = document.createElement("span");
    text.textContent = label;
    div.appendChild(check);
    div.appendChild(text);
    return div;
  }

  function renderWizardOptions(providers, cities, jobTypes) {
    const providersEl = el("wizard-providers");
    providersEl.innerHTML = "";
    providers.forEach((p) => {
      const item = choiceItem(p.label, false);
      item.addEventListener("click", () => toggleSetChoice(state.wizard.providers, p.key, item));
      providersEl.appendChild(item);
    });

    const citiesEl = el("wizard-cities");
    citiesEl.innerHTML = "";
    const allItem = choiceItem("🌍 همه‌ی ایران (بدون فیلتر شهر)", true);
    allItem.addEventListener("click", () => selectCity(null, allItem));
    citiesEl.appendChild(allItem);
    cities.forEach((city) => {
      const item = choiceItem(city, true);
      item.addEventListener("click", () => selectCity(city, item));
      citiesEl.appendChild(item);
    });
    selectCity(null, allItem);

    const jobTypesEl = el("wizard-job-types");
    jobTypesEl.innerHTML = "";
    jobTypes.forEach((jt) => {
      const item = choiceItem(jt.label, false);
      item.addEventListener("click", () => toggleSetChoice(state.wizard.jobTypes, jt.key, item));
      jobTypesEl.appendChild(item);
    });
  }

  function toggleSetChoice(set, key, itemEl) {
    if (set.has(key)) {
      set.delete(key);
      itemEl.classList.remove("selected");
    } else {
      set.add(key);
      itemEl.classList.add("selected");
    }
    updateWizardControls();
  }

  function selectCity(city, itemEl) {
    state.wizard.city = city;
    document.querySelectorAll("#wizard-cities .choice-item").forEach((i) => i.classList.remove("selected"));
    itemEl.classList.add("selected");
    updateWizardControls();
  }

  function resetWizard() {
    state.wizard = { step: 1, keyword: "", providers: new Set(), city: null, jobTypes: new Set() };
    el("wizard-keyword").value = "";
    document.querySelectorAll("#wizard-providers .choice-item, #wizard-job-types .choice-item").forEach((i) => {
      i.classList.remove("selected");
    });
    const firstCity = document.querySelector("#wizard-cities .choice-item");
    if (firstCity) {
      document.querySelectorAll("#wizard-cities .choice-item").forEach((i) => i.classList.remove("selected"));
      firstCity.classList.add("selected");
    }
    showWizardStep(1);
  }

  function showWizardStep(step) {
    state.wizard.step = step;
    [1, 2, 3, 4].forEach((n) => el("wizard-step-" + n).classList.toggle("hidden", n !== step));
    el("wizard-success").classList.add("hidden");
    document.querySelectorAll(".step-dot").forEach((dot) => {
      const n = parseInt(dot.dataset.step, 10);
      dot.classList.toggle("active", n === step);
      dot.classList.toggle("done", n < step);
    });
    updateWizardControls();
  }

  function wizardCanProceed() {
    const w = state.wizard;
    if (w.step === 1) return el("wizard-keyword").value.trim().length > 0;
    if (w.step === 2) return w.providers.size > 0;
    return true;
  }

  function updateWizardControls() {
    const onSuccess = !el("wizard-success").classList.contains("hidden");
    const fallbackBtn = el("wizard-fallback-btn");

    if (state.activeTab !== "add" || onSuccess) {
      if (tg) {
        tg.MainButton.hide();
        tg.BackButton.hide();
      }
      fallbackBtn.classList.add("hidden");
      return;
    }

    const step = state.wizard.step;
    const canProceed = wizardCanProceed();
    const label = step < 4 ? "➡️ بعدی" : "✅ ساخت سرچ";

    if (tg) {
      fallbackBtn.classList.add("hidden");
      if (step > 1) tg.BackButton.show();
      else tg.BackButton.hide();
      tg.MainButton.setText(label);
      tg.MainButton.show();
      if (canProceed) tg.MainButton.enable();
      else tg.MainButton.disable();
    } else {
      fallbackBtn.classList.remove("hidden");
      fallbackBtn.textContent = label;
      fallbackBtn.disabled = !canProceed;
    }
  }

  async function onWizardAdvance() {
    const w = state.wizard;
    if (w.step === 1) {
      w.keyword = el("wizard-keyword").value.trim();
      if (!w.keyword) return;
      showWizardStep(2);
      return;
    }
    if (w.step === 2) {
      if (w.providers.size === 0) return;
      showWizardStep(3);
      return;
    }
    if (w.step === 3) {
      showWizardStep(4);
      return;
    }
    if (w.step === 4) {
      await submitWizard();
    }
  }

  function onWizardBack() {
    showWizardStep(Math.max(1, state.wizard.step - 1));
  }

  async function submitWizard() {
    const w = state.wizard;
    if (tg) tg.MainButton.showProgress();
    el("wizard-fallback-btn").disabled = true;

    const res = await apiPost("/searches/", {
      keyword: w.keyword,
      providers: Array.from(w.providers),
      city: w.city,
      job_types: Array.from(w.jobTypes),
    });

    if (tg) {
      tg.MainButton.hideProgress();
      tg.MainButton.hide();
      tg.BackButton.hide();
    }

    [1, 2, 3, 4].forEach((n) => el("wizard-step-" + n).classList.add("hidden"));
    el("wizard-success").classList.remove("hidden");
    el("wizard-fallback-btn").classList.add("hidden");

    const created = res.created || [];
    el("wizard-success-text").textContent = created.length
      ? created.map((s) => "✅ " + s.title).join("\n") + "\n\nهر ۱۵ دقیقه چک می‌شن و آگهی‌های جدید برات ارسال می‌شه."
      : "مشکلی پیش اومد، دوباره تلاش کن.";

    await refreshBootstrap();
  }

  el("wizard-keyword").addEventListener("input", updateWizardControls);
  el("wizard-fallback-btn").addEventListener("click", onWizardAdvance);

  if (tg) {
    tg.onEvent("mainButtonClicked", onWizardAdvance);
    tg.onEvent("backButtonClicked", onWizardBack);
  }

  // ---------- Searches list ----------

  function renderSearches(searches) {
    const listEl = el("searches-list");
    const emptyEl = el("searches-empty");
    listEl.innerHTML = "";

    if (!searches.length) {
      emptyEl.classList.remove("hidden");
      return;
    }
    emptyEl.classList.add("hidden");
    searches.forEach((s) => listEl.appendChild(buildSearchCard(s)));
  }

  function buildSearchCard(search) {
    const card = document.createElement("div");
    card.className = "search-card";

    const title = document.createElement("div");
    title.className = "search-card-title";
    title.textContent = search.title;
    card.appendChild(title);

    const actions = document.createElement("div");
    actions.className = "search-card-actions";

    const pauseBtn = document.createElement("button");
    pauseBtn.className = search.is_active ? "btn-pause" : "btn-resume";
    pauseBtn.textContent = search.is_active ? "🔵 توقف" : "🟢 ازسرگیری";
    pauseBtn.addEventListener("click", () => toggleSearch(search.id));

    const deleteBtn = document.createElement("button");
    deleteBtn.className = "btn-delete";
    deleteBtn.textContent = "🔴 حذف";
    deleteBtn.addEventListener("click", () => deleteSearch(search.id));

    actions.appendChild(pauseBtn);
    actions.appendChild(deleteBtn);
    card.appendChild(actions);
    return card;
  }

  async function toggleSearch(id) {
    await apiPost("/searches/" + id + "/toggle/", {});
    await refreshBootstrap();
  }

  function deleteSearch(id) {
    const run = async () => {
      await apiPost("/searches/" + id + "/delete/", {});
      await refreshBootstrap();
    };
    if (tg && tg.showConfirm) {
      tg.showConfirm("این سرچ حذف بشه؟", (ok) => {
        if (ok) run();
      });
    } else if (window.confirm("این سرچ حذف بشه؟")) {
      run();
    }
  }

  // ---------- Account ----------

  function renderAccount(user, activeCount) {
    el("acc-first-name").textContent = user.first_name || "—";
    el("acc-last-name").textContent = user.last_name || "—";
    el("acc-username").textContent = user.username ? "@" + user.username : "—";
    el("acc-chat-id").textContent = user.chat_id;
    el("acc-active-count").textContent = activeCount;
  }

  // ---------- Bootstrap ----------

  async function refreshBootstrap() {
    const data = await apiGet("/bootstrap/");
    state.bootstrap = data;
    renderAccount(data.user, data.active_search_count);
    renderSearches(data.searches);
  }

  async function loadBootstrap() {
    let data;
    try {
      data = await apiGet("/bootstrap/");
    } catch (e) {
      el("view-loading").classList.add("hidden");
      return;
    }

    state.bootstrap = data;

    if (data.error) {
      el("view-loading").classList.add("hidden");
      return;
    }

    if (!data.is_channel_member) {
      showJoin(data);
      return;
    }

    showMain();
    renderAccount(data.user, data.active_search_count);
    renderSearches(data.searches);
    renderWizardOptions(data.providers, data.cities, data.job_types);
    el("support-link").href = "https://t.me/" + data.support_username;
  }

  el("join-check-btn").addEventListener("click", loadBootstrap);

  // ---------- Init ----------

  if (tg) {
    tg.ready();
    tg.expand();
    applyTheme();
    tg.onEvent("themeChanged", applyTheme);
  }

  goTo("searches");
  loadBootstrap();
})();
