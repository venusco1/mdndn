(() => {
  'use strict';

  const DOB = new Date(1999, 6, 18);
  const AGE30 = new Date(2029, 6, 18);
  const AGE60 = new Date(2059, 6, 18);
  const MISSION_START = new Date(2026, 9, 6);
  const DAY_MS = 86400000;

  function startOfDay(date) {
    return new Date(date.getFullYear(), date.getMonth(), date.getDate());
  }

  function daysBetween(start, end) {
    return Math.round((startOfDay(end) - startOfDay(start)) / DAY_MS);
  }

  function ymdBetween(start, end) {
    let years = end.getFullYear() - start.getFullYear();
    let months = end.getMonth() - start.getMonth();
    let days = end.getDate() - start.getDate();

    if (days < 0) {
      months -= 1;
      days += new Date(end.getFullYear(), end.getMonth(), 0).getDate();
    }
    if (months < 0) {
      years -= 1;
      months += 12;
    }
    return { years, months, days };
  }

  function setText(id, text) {
    const element = document.getElementById(id);
    if (element) element.textContent = text;
  }

  function updateLifeClock() {
    const now = new Date();
    const today = startOfDay(now);
    const age = ymdBetween(DOB, today);
    const daysLived = daysBetween(DOB, today);
    const remainingTo30 = Math.max(0, daysBetween(today, AGE30));
    const remainingTo60 = Math.max(0, daysBetween(today, AGE60));
    const progressTo60 = Math.min(100, Math.max(0, (daysLived / daysBetween(DOB, AGE60)) * 100));
    const until30 = today < AGE30 ? ymdBetween(today, AGE30) : { years: 0, months: 0, days: 0 };
    const until60 = today < AGE60 ? ymdBetween(today, AGE60) : { years: 0, months: 0, days: 0 };
    const totalMissionDays = daysBetween(MISSION_START, AGE30);

    setText('live-now', now.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' }));
    setText('live-age', String(age.years));
    setText('live-to30', remainingTo30.toLocaleString());
    setText('current-age', String(age.years));
    setText('clock-today', now.toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }));
    setText('clock-age', `${age.years} years, ${age.months} months`);
    setText('clock-pct', `${progressTo60.toFixed(1)}%`);
    setText('clock-days-lived', daysLived.toLocaleString());
    setText('clock-weeks-lived', Math.floor(daysLived / 7).toLocaleString());
    setText('clock-months-lived', (age.years * 12 + age.months).toLocaleString());
    setText('clock-years-lived', age.years.toLocaleString());
    setText('clock-remain-ymd', `${until60.years} years, ${until60.months} months, ${until60.days} days`);
    setText('clock-remain-days', remainingTo60.toLocaleString());
    setText('clock-remain-weeks', Math.floor(remainingTo60 / 7).toLocaleString());
    setText('clock-remain-months', (until60.years * 12 + until60.months).toLocaleString());
    setText('clock-days-to-30', remainingTo30.toLocaleString());
    setText('deadline-years', until30.years.toLocaleString());
    setText('deadline-months', until30.months.toLocaleString());
    setText('deadline-days', until30.days.toLocaleString());
    setText('deadline-total-days', remainingTo30.toLocaleString());
    setText('deadline-window', `${totalMissionDays.toLocaleString()} days`);
    setText('sidebar-days', remainingTo30.toLocaleString());

    const ring = document.getElementById('life-ring');
    if (ring) {
      ring.style.setProperty('--p', progressTo60.toFixed(2));
      ring.setAttribute('aria-label', `Life horizon progress: ${progressTo60.toFixed(1)} percent`);
    }
    const sidebarBar = document.querySelector('.sidebar-meter .bar');
    if (sidebarBar) sidebarBar.setAttribute('aria-valuenow', String(Math.round(Math.min(100, Math.max(0, (daysLived / daysBetween(DOB, AGE30)) * 100)))));
    const sidebarFill = document.getElementById('sidebar-bar');
    if (sidebarFill) sidebarFill.style.width = `${Math.max(0, Math.min(100, (daysLived / daysBetween(DOB, AGE30)) * 100))}%`;
  }

  function setNavigationOpen(open) {
    document.body.classList.toggle('nav-open', open);
    const toggle = document.getElementById('menu-toggle');
    if (toggle) {
      toggle.setAttribute('aria-expanded', String(open));
      toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    }
  }

  function initializeNavigation() {
    const toggle = document.getElementById('menu-toggle');
    const backdrop = document.getElementById('nav-backdrop');
    toggle?.addEventListener('click', () => {
      setNavigationOpen(toggle.getAttribute('aria-expanded') !== 'true');
    });
    backdrop?.addEventListener('click', () => setNavigationOpen(false));
    document.querySelectorAll('#sidebar nav a').forEach((link) => {
      link.addEventListener('click', () => setNavigationOpen(false));
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') setNavigationOpen(false);
    });
    window.addEventListener('resize', () => {
      if (window.innerWidth > 980) setNavigationOpen(false);
    });
  }

  updateLifeClock();
  initializeNavigation();
  window.setInterval(updateLifeClock, 60000);
})();
