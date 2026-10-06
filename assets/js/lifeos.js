(() => {
  const DOB = new Date(1999, 6, 18);
  const AGE30 = new Date(2029, 6, 18);
  const AGE60 = new Date(2059, 6, 18);
  const HORIZON_DAYS = daysBetween(new Date(1999, 6, 18), new Date(2059, 6, 18));
  const PILLARS = [
    { id: "mental", name: "Mental & Intelligence", action: "30 min learning" },
    { id: "physical", name: "Physical", action: "Exercise" },
    { id: "spiritual", name: "Islamic & Spiritual", action: "Salah / Qur'an" },
    { id: "financial", name: "Financial", action: "Record expenses" },
    { id: "personal", name: "Personal Development", action: "Reading / skill" },
    { id: "character", name: "Character & Discipline", action: "Discipline / emotional control" },
    { id: "business", name: "Business & Professional", action: "Revenue-producing work" }
  ];

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

  function startOfDay(d) {
    return new Date(d.getFullYear(), d.getMonth(), d.getDate());
  }

  function daysBetween(a, b) {
    const ms = startOfDay(b) - startOfDay(a);
    return Math.round(ms / 86400000);
  }

  function ymdBetween(from, to) {
    let years = to.getFullYear() - from.getFullYear();
    let months = to.getMonth() - from.getMonth();
    let days = to.getDate() - from.getDate();
    if (days < 0) {
      months -= 1;
      days += new Date(to.getFullYear(), to.getMonth(), 0).getDate();
    }
    if (months < 0) {
      years -= 1;
      months += 12;
    }
    return { years, months, days };
  }

  function fmtYMD({ years, months, days }) {
    return `${years} years, ${months} months, ${days} days`;
  }

  function pad(n) {
    return String(n).padStart(2, "0");
  }

  function isoDate(d) {
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  }

  function isoWeekKey(d) {
    const date = startOfDay(d);
    date.setDate(date.getDate() + 4 - (date.getDay() || 7));
    const yearStart = new Date(date.getFullYear(), 0, 1);
    const week = Math.ceil(((date - yearStart) / 86400000 + 1) / 7);
    return `${date.getFullYear()}-W${pad(week)}`;
  }

  function monthKey(d) {
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}`;
  }

  function setStatus(message, isError = false, target = "app-status") {
    const el = document.getElementById(target);
    if (!el) return;
    el.textContent = message;
    el.classList.toggle("is-error", isError);
  }

  function load(key, fallback) {
    try {
      const raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : fallback;
    } catch (error) {
      console.error(`Unable to read saved diary data for "${key}".`, error);
      setStatus("Saved data could not be read. Export or repair your diary backup, then reload.", true);
      return fallback;
    }
  }

  function save(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (error) {
      console.error(`Unable to save diary data for "${key}".`, error);
      setStatus("Changes could not be saved in this browser. Export your data or free browser storage.", true);
      return false;
    }
  }

  function currentStage(now) {
    const t = startOfDay(now).getTime();
    if (t <= new Date(2026, 11, 31).getTime()) return 1;
    if (t <= new Date(2027, 11, 31).getTime()) return 2;
    if (t <= new Date(2028, 11, 31).getTime()) return 3;
    return 4;
  }

  function renderClock() {
    const now = new Date();
    const lived = Math.max(0, daysBetween(DOB, now));
    const to30 = Math.max(0, daysBetween(now, AGE30));
    const to60 = Math.max(0, daysBetween(now, AGE60));
    const age = now < DOB ? { years: 0, months: 0, days: 0 } : ymdBetween(DOB, now);
    const remain60 = to60 ? ymdBetween(now, AGE60) : { years: 0, months: 0, days: 0 };
    const remain30 = to30 ? ymdBetween(now, AGE30) : { years: 0, months: 0, days: 0 };
    const pct60 = Math.max(0, Math.min(100, (lived / HORIZON_DAYS) * 100));
    const weeksLived = Math.floor(lived / 7);
    const weekRemLived = lived % 7;
    const monthsLivedApprox = age.years * 12 + age.months;
    const weeks30 = Math.floor(to30 / 7);
    const weekRem30 = to30 % 7;
    const months30 = remain30.years * 12 + remain30.months;
    const weeks60 = Math.floor(to60 / 7);
    const weekRem60 = to60 % 7;
    const months60 = remain60.years * 12 + remain60.months;

    const setText = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val;
    };

    setText("live-now", now.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" }));
    setText("live-age", fmtYMD(age));
    setText("live-to30", to30 ? `${to30.toLocaleString()} days` : "Milestone reached");
    setText("current-age", String(age.years));
    setText("clock-today", now.toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" }));
    setText("clock-age", fmtYMD(age));
    setText("clock-days-lived", lived.toLocaleString());
    setText("clock-weeks-lived", `${weeksLived.toLocaleString()} weeks + ${weekRemLived} days`);
    setText("clock-months-lived", `${monthsLivedApprox} months + ${age.days} days`);
    setText("clock-years-lived", String(age.years));
    setText("clock-pct", `${pct60.toFixed(1)}%`);
    setText("clock-remain-ymd", fmtYMD(remain60));
    setText("clock-remain-days", to60.toLocaleString());
    setText("clock-remain-weeks", `${weeks60.toLocaleString()} weeks + ${weekRem60} days`);
    setText("clock-remain-months", `${months60} months + ${remain60.days} days`);
    setText("deadline-ymd", fmtYMD(remain30));
    setText("deadline-years", String(remain30.years));
    setText("deadline-days", to30.toLocaleString());
    setText("deadline-total-days", to30.toLocaleString());
    setText("deadline-weeks", `${weeks30} weeks + ${weekRem30} days`);
    setText("deadline-months", `${months30} months + ${remain30.days} days`);
    setText("daily-date", isoDate(now));
    setText("daily-age", fmtYMD(age));
    setText("daily-lived", lived.toLocaleString());
    setText("daily-to30", to30.toLocaleString());
    setText("daily-to60", to60.toLocaleString());
    setText("sidebar-days", to30.toLocaleString());
    setText("clock-days-to-30", to30.toLocaleString());
    setText("mission-days", to30 ? to30.toLocaleString() : "Milestone reached");
    setText("deadline-window", `${isoDate(new Date(2026, 9, 6))} – ${isoDate(AGE30)}`);

    const ring = document.getElementById("life-ring");
    if (ring) ring.style.setProperty("--p", pct60.toFixed(1));
    const windowStart = new Date(2026, 9, 6);
    const windowTotal = Math.max(1, daysBetween(windowStart, AGE30));
    const windowElapsed = Math.max(0, daysBetween(windowStart, now));
    const missionPct = Math.max(0, Math.min(100, (windowElapsed / windowTotal) * 100));
    const bar = document.getElementById("sidebar-bar");
    if (bar) bar.style.width = `${missionPct}%`;
    if (bar) bar.parentElement.setAttribute("aria-valuenow", String(Math.round(missionPct)));
    if (ring) ring.setAttribute("aria-label", `${pct60.toFixed(1)} percent of the 60-year life horizon completed`);

    $$(".stage").forEach((el) => {
      el.classList.toggle("active", Number(el.dataset.stage) === currentStage(now));
    });
  }

  function dailyKey(dateStr) {
    return `mdndn.daily.${dateStr}`;
  }

  function defaultDaily(dateStr) {
    return {
      date: dateStr,
      big3: ["", "", ""],
      actions: Object.fromEntries(PILLARS.map((p) => [p.id, { note: p.action, done: false }])),
      scores: Object.fromEntries(PILLARS.map((p) => [p.id, null]))
    };
  }

  function normalizeDaily(dateStr, stored) {
    const daily = defaultDaily(dateStr);
    if (!stored || typeof stored !== "object" || Array.isArray(stored)) return daily;
    if (Array.isArray(stored.big3)) {
      daily.big3 = daily.big3.map((value, index) =>
        typeof stored.big3[index] === "string" ? stored.big3[index] : value
      );
    }
    PILLARS.forEach((pillar) => {
      const action = stored.actions?.[pillar.id];
      if (action && typeof action === "object") {
        daily.actions[pillar.id] = {
          note: typeof action.note === "string" ? action.note : pillar.action,
          done: action.done === true
        };
      }
      const score = stored.scores?.[pillar.id];
      daily.scores[pillar.id] = [0, 1, 2].includes(score) ? score : null;
    });
    return daily;
  }

  function renderDaily() {
    const dateStr = isoDate(new Date());
    const data = normalizeDaily(dateStr, load(dailyKey(dateStr), defaultDaily(dateStr)));

    ["big1", "big2", "big3"].forEach((id, i) => {
      const el = document.getElementById(id);
      if (el) el.value = data.big3[i] || "";
    });

    const track = document.getElementById("pillar-track");
    if (track) {
      track.replaceChildren();
      PILLARS.forEach((pillar) => {
        const row = document.createElement("div");
        row.className = "check-row";
        const name = document.createElement("div");
        name.textContent = pillar.name;
        const note = document.createElement("input");
        note.className = "act";
        note.type = "text";
        note.dataset.pillar = pillar.id;
        note.value = data.actions[pillar.id].note;
        note.setAttribute("aria-label", `Daily action for ${pillar.name}`);
        const done = document.createElement("input");
        done.type = "checkbox";
        done.dataset.done = pillar.id;
        done.checked = data.actions[pillar.id].done;
        done.setAttribute("aria-label", `Mark ${pillar.name} complete`);
        row.append(name, note, done);
        track.append(row);
      });
    }

    const scoreBox = document.getElementById("night-scores");
    if (scoreBox) {
      scoreBox.replaceChildren();
      PILLARS.forEach((pillar) => {
        const row = document.createElement("div");
        row.className = "check-row";
        const name = document.createElement("div");
        name.textContent = pillar.name;
        const buttons = document.createElement("div");
        buttons.className = "score-btns";
        buttons.dataset.score = pillar.id;
        [0, 1, 2].forEach((value) => {
          const button = document.createElement("button");
          button.type = "button";
          button.dataset.v = String(value);
          button.textContent = String(value);
          button.setAttribute("aria-label", `${pillar.name}: score ${value}`);
          button.setAttribute("aria-pressed", String(data.scores[pillar.id] === value));
          if (data.scores[pillar.id] === value) button.classList.add(`on-${value}`);
          buttons.append(button);
        });
        row.append(name, buttons);
        scoreBox.append(row);
      });
    }
    updateScoreDisplay(data);
    renderHistory();
  }

  function readDailyFromDom(data) {
    data = normalizeDaily(isoDate(new Date()), data);
    data.big3 = ["big1", "big2", "big3"].map((id) => document.getElementById(id)?.value || "");
    PILLARS.forEach((p) => {
      const note = document.querySelector(`[data-pillar="${p.id}"]`);
      const done = document.querySelector(`[data-done="${p.id}"]`);
      data.actions[p.id] = { note: note ? note.value : p.action, done: !!(done && done.checked) };
    });
    return data;
  }

  function persistDaily() {
    const dateStr = isoDate(new Date());
    const data = readDailyFromDom(load(dailyKey(dateStr), defaultDaily(dateStr)));
    save(dailyKey(dateStr), data);
    updateScoreDisplay(data);
  }

  function updateScoreDisplay(data) {
    const vals = PILLARS.map((p) => data.scores[p.id]).filter((v) => v !== null && v !== undefined);
    const total = PILLARS.reduce((sum, p) => sum + (Number(data.scores[p.id]) || 0), 0);
    const pct = (total / 14) * 100;
    const el = document.getElementById("night-total");
    if (el) el.textContent = vals.length ? `${total}/14 = ${pct.toFixed(1)}%` : "— / 14";
  }

  function renderHistory() {
    const box = document.getElementById("score-history");
    if (!box) return;
    const rows = [];
    try {
      for (let i = 0; i < localStorage.length; i += 1) {
        const key = localStorage.key(i);
        if (key && key.startsWith("mdndn.daily.")) {
          const d = load(key, null);
          if (!d || typeof d !== "object") continue;
          const normalized = normalizeDaily(key.slice(12), d);
          const total = PILLARS.reduce((sum, p) => sum + (normalized.scores[p.id] ?? 0), 0);
          const scored = PILLARS.some((p) => normalized.scores[p.id] !== null);
          if (scored) rows.push({ date: normalized.date, total, pct: (total / 14) * 100 });
        }
      }
    } catch (error) {
      console.error("Unable to read diary score history.", error);
      setStatus("Diary history could not be read from this browser.", true);
      return;
    }
    rows.sort((a, b) => (a.date < b.date ? 1 : -1));
    box.replaceChildren();
    if (!rows.length) {
      box.textContent = "No scored days yet.";
      return;
    }
    rows.slice(0, 21).forEach((row) => {
      const line = document.createElement("div");
      line.textContent = `${row.date} — ${row.total}/14 (${row.pct.toFixed(1)}%)`;
      box.append(line);
    });
  }

  function bindDaily() {
    document.getElementById("daily-panel")?.addEventListener("input", persistDaily);
    document.getElementById("daily-panel")?.addEventListener("change", persistDaily);
    document.getElementById("night-scores")?.addEventListener("click", (e) => {
      const btn = e.target.closest("button[data-v]");
      if (!btn) return;
      const group = btn.parentElement;
      const id = group.dataset.score;
      const dateStr = isoDate(new Date());
      const data = readDailyFromDom(load(dailyKey(dateStr), defaultDaily(dateStr)));
      data.scores[id] = Number(btn.dataset.v);
      save(dailyKey(dateStr), data);
      group.querySelectorAll("button").forEach((button) => {
        button.className = "";
        button.setAttribute("aria-pressed", "false");
      });
      btn.className = `on-${btn.dataset.v}`;
      btn.setAttribute("aria-pressed", "true");
      updateScoreDisplay(data);
      renderHistory();
    });
  }

  function bindWeekly() {
    const key = `mdndn.weekly.${isoWeekKey(new Date())}`;
    const stored = load(key, {
      q1: "", q2: "", q3: "", q4: "", q5: "", q6: "", q7: "",
      income: "", expenses: "", savings: "", debt: "",
      revenue: "", profit: "", leads: "", sales: "",
      exercise: "", learning: "", spiritual: "", sleep: ""
    });
    const data = stored && typeof stored === "object" && !Array.isArray(stored) ? stored : {};
    Object.entries(data).forEach(([k, v]) => {
      const el = document.getElementById(`w-${k}`);
      if (el) el.value = v;
    });
    const weekLabel = document.getElementById("week-key");
    if (weekLabel) weekLabel.textContent = isoWeekKey(new Date());
    document.getElementById("weekly-panel")?.addEventListener("input", () => {
      const next = {};
      $$("#weekly-panel [id^='w-']").forEach((el) => {
        next[el.id.slice(2)] = el.value;
      });
      save(key, next);
    });
  }

  function bindMonthly() {
    const key = `mdndn.monthly.${monthKey(new Date())}`;
    const fields = ["mental", "physical", "spiritual", "financial", "personal", "character", "business", "family"];
    const stored = load(key, Object.fromEntries(fields.map((f) => [f, ""])));
    const data = stored && typeof stored === "object" && !Array.isArray(stored) ? stored : {};
    fields.forEach((f) => {
      const el = document.getElementById(`m-${f}`);
      if (el) el.value = data[f] ?? "";
    });
    const note = document.getElementById("m-note");
    if (note) note.value = data.note || "";
    const label = document.getElementById("month-key");
    if (label) label.textContent = monthKey(new Date());
    const overall = document.getElementById("m-overall");
    const updateOverall = () => {
      const controls = fields.map((f) => document.getElementById(`m-${f}`)).filter(Boolean);
      const invalidScore = controls.some((control) => !control.checkValidity());
      const nums = controls
        .filter((control) => control.value !== "" && control.checkValidity())
        .map((control) => Number(control.value));
      const avg = nums.length ? (nums.reduce((a, b) => a + b, 0) / nums.length).toFixed(1) : "—";
      if (overall) overall.textContent = invalidScore ? "Use scores from 0 to 100" : avg;
      const next = {};
      fields.forEach((f) => { next[f] = document.getElementById(`m-${f}`)?.value || ""; });
      next.note = document.getElementById("m-note")?.value || "";
      save(key, next);
    };
    updateOverall();
    document.getElementById("monthly-panel")?.addEventListener("input", updateOverall);
  }

  function bindTargets() {
    const key = "mdndn.targets";
    const stored = load(key, {});
    const data = stored && typeof stored === "object" && !Array.isArray(stored) ? stored : {};
    $$("[data-target]").forEach((el) => {
      el.value = data[el.dataset.target] || "";
      el.addEventListener("input", () => {
        const next = load(key, {});
        next[el.dataset.target] = el.value;
        save(key, next);
      });
    });
  }

  function bindAnswers() {
    const key = "mdndn.answers";
    const stored = load(key, {});
    const data = stored && typeof stored === "object" && !Array.isArray(stored) ? stored : {};
    $$("[data-answer]").forEach((el) => {
      el.value = data[el.dataset.answer] || "";
      el.addEventListener("input", () => {
        const next = load(key, {});
        next[el.dataset.answer] = el.value;
        save(key, next);
      });
    });
  }

  function bindNav() {
    const toggle = document.getElementById("menu-toggle");
    const sidebar = document.getElementById("sidebar");
    const backdrop = document.getElementById("nav-backdrop");
    const setOpen = (open) => {
      document.body.classList.toggle("nav-open", open);
      if (toggle) {
        toggle.setAttribute("aria-expanded", String(open));
        toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
      }
      if (sidebar) {
        sidebar.inert = window.matchMedia("(max-width: 980px)").matches && !open;
      }
      if (open) sidebar?.querySelector("a")?.focus();
    };
    setOpen(false);
    toggle?.addEventListener("click", () => setOpen(!document.body.classList.contains("nav-open")));
    backdrop?.addEventListener("click", () => {
      setOpen(false);
      toggle?.focus();
    });
    $$(".nav-list a").forEach((a) => {
      a.addEventListener("click", () => setOpen(false));
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && document.body.classList.contains("nav-open")) {
        setOpen(false);
        toggle?.focus();
      }
    });
    window.addEventListener("resize", () => setOpen(document.body.classList.contains("nav-open")));
    const links = $$(".nav-list a");
    const sections = links
      .map((a) => document.getElementById(a.hash.slice(1)))
      .filter(Boolean);
    const onScroll = () => {
      const y = window.scrollY + 90;
      let current = sections[0];
      sections.forEach((s) => {
        if (s.getBoundingClientRect().top + window.scrollY <= y) current = s;
      });
      links.forEach((a) => {
        const active = a.hash === `#${current.id}`;
        a.classList.toggle("active", active);
        if (active) a.setAttribute("aria-current", "location");
        else a.removeAttribute("aria-current");
      });
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  function bindExport() {
    document.getElementById("export-diary")?.addEventListener("click", () => {
      try {
        const dump = {};
        for (let i = 0; i < localStorage.length; i += 1) {
          const key = localStorage.key(i);
          if (key && key.startsWith("mdndn.")) dump[key] = load(key, null);
        }
        const blob = new Blob([JSON.stringify(dump, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `mdndn-diary-${isoDate(new Date())}.json`;
        link.click();
        window.setTimeout(() => URL.revokeObjectURL(url), 1000);
        setStatus("Diary backup downloaded.", false, "transfer-status");
      } catch (error) {
        console.error("Unable to export the diary backup.", error);
        setStatus("The diary backup could not be created. Check browser storage and try again.", true, "transfer-status");
      }
    });
    document.getElementById("import-diary")?.addEventListener("change", (e) => {
      const file = e.target.files?.[0];
      if (!file) return;
      const importInput = e.target;
      if (file.size > 5 * 1024 * 1024) {
        setStatus("That backup is larger than 5 MB and was not imported.", true, "transfer-status");
        importInput.value = "";
        return;
      }
      const reader = new FileReader();
      reader.onload = () => {
        try {
          const dump = JSON.parse(String(reader.result));
          if (!dump || typeof dump !== "object" || Array.isArray(dump)) {
            throw new Error("The backup must contain a JSON object.");
          }
          const entries = Object.entries(dump);
          const allowedKey = /^mdndn\.(?:daily\.\d{4}-\d{2}-\d{2}|weekly\.\d{4}-W\d{2}|monthly\.\d{4}-\d{2}|targets|answers)$/;
          if (!entries.length || entries.some(([key, value]) =>
            !allowedKey.test(key) || !value || typeof value !== "object" || Array.isArray(value)
          )) {
            throw new Error("The file does not contain a valid Life OS diary backup.");
          }
          if (!window.confirm("Merge this backup into the diary saved in this browser? Existing matching dates will be replaced.")) {
            importInput.value = "";
            return;
          }
          for (const [key, value] of entries) {
            if (!save(key, value)) throw new Error("Browser storage could not save the imported backup.");
          }
          setStatus("Diary imported. Reloading your saved entries…", false, "transfer-status");
          window.setTimeout(() => location.reload(), 250);
        } catch (error) {
          console.error("Unable to import the diary backup.", error);
          setStatus(error.message || "The selected file could not be imported.", true, "transfer-status");
          importInput.value = "";
        }
      };
      reader.onerror = () => {
        console.error("Unable to read the selected diary backup.", reader.error);
        setStatus("The selected backup file could not be read.", true, "transfer-status");
        importInput.value = "";
      };
      reader.readAsText(file);
    });
  }

  renderClock();
  setInterval(renderClock, 60000);
  renderDaily();
  bindDaily();
  bindWeekly();
  bindMonthly();
  bindTargets();
  bindAnswers();
  bindNav();
  bindExport();
})();
