(() => {
  const STORAGE_KEY = 'mdndn-life-os-v1';
  const DOB = new Date(1999, 6, 18);
  const AGE30 = new Date(2029, 6, 18);
  const AGE60 = new Date(2059, 6, 18);
  const VIEWS = ['today', 'goals', 'tasks', 'habits', 'progress', 'life', 'journal', 'archive'];
  const PILLARS = [
    { id: 'mental', name: 'Mental & Intelligence', tag: 'learning' },
    { id: 'physical', name: 'Physical', tag: 'health' },
    { id: 'spiritual', name: 'Islamic & Spiritual', tag: 'faith' },
    { id: 'financial', name: 'Financial', tag: 'money' },
    { id: 'personal', name: 'Personal Development', tag: 'growth' },
    { id: 'character', name: 'Character & Discipline', tag: 'discipline' },
    { id: 'business', name: 'Business & Professional', tag: 'career' },
  ];

  const defaultState = {
    currentView: 'today',
    theme: 'system',
    big3: ['Complete client website', 'Follow up with 50 leads', 'Exercise for 30 minutes'],
    scores: {
      mental: 2,
      physical: 1,
      spiritual: 2,
      financial: 1,
      personal: 2,
      character: 1,
      business: 2,
    },
    tasks: [
      { id: 'task-1', title: 'Book the next client call', description: 'Prepare offer and follow-up notes', status: 'todo', priority: 'high', dueDate: '', pillar: 'business', createdAt: nowISO() },
      { id: 'task-2', title: 'Review monthly finances', description: 'Check revenue, expenses, and savings', status: 'in_progress', priority: 'medium', dueDate: '', pillar: 'financial', createdAt: nowISO() },
      { id: 'task-3', title: 'Read 20 pages', description: 'Focused learning and reflection', status: 'completed', priority: 'low', dueDate: '', pillar: 'mental', createdAt: nowISO() },
    ],
    goals: [
      { id: 'goal-1', title: 'Reach ₹50,000 monthly personal income', description: 'Create stable personal income through business systems.', category: 'age-30', pillar: 'financial', target: 50000, current: 22000, unit: '₹', status: 'on-track', deadline: '2029-07-18' },
      { id: 'goal-2', title: 'Build a strong wellness base', description: 'Strengthen sleep, exercise, and daily discipline.', category: 'yearly', pillar: 'physical', target: 100, current: 74, unit: '%', status: 'on-track', deadline: '2027-12-31' },
      { id: 'goal-3', title: 'Complete core Islamic rhythm', description: 'Daily Salah and Qur’an routine with consistency.', category: 'short-term', pillar: 'spiritual', target: 100, current: 82, unit: '%', status: 'needs-focus', deadline: '2026-12-31' },
    ],
    habits: [
      { id: 'habit-1', title: 'Exercise', bestStreak: 8, history: [3, 2, 1, 0].map((days) => isoDate(subDays(new Date(), days))) },
      { id: 'habit-2', title: 'Qur’an', bestStreak: 12, history: [5, 4, 3, 2, 1, 0].map((days) => isoDate(subDays(new Date(), days))) },
      { id: 'habit-3', title: 'Reading', bestStreak: 7, history: [2, 1, 0].map((days) => isoDate(subDays(new Date(), days))) },
      { id: 'habit-4', title: 'Plan the day', bestStreak: 5, history: [1, 0].map((days) => isoDate(subDays(new Date(), days))) },
      { id: 'habit-5', title: 'Sleep on time', bestStreak: 9, history: [4, 3, 2, 1, 0].map((days) => isoDate(subDays(new Date(), days))) },
    ],
    journal: [
      { id: 'jour-1', date: isoDate(subDays(new Date(), 1)), mood: 'focused', text: 'Focused work on client work and reduced the clutter in my task list. The day felt calm and productive.' },
      { id: 'jour-2', date: isoDate(subDays(new Date(), 3)), mood: 'strong', text: 'I kept my rhythm better today. My biggest win was consistent follow-up and a stronger pattern of daily execution.' },
    ],
    history: [
      { date: isoDate(subDays(new Date(), 6)), scores: { mental: 2, physical: 1, spiritual: 2, financial: 1, personal: 2, character: 2, business: 2 } },
      { date: isoDate(subDays(new Date(), 5)), scores: { mental: 1, physical: 1, spiritual: 2, financial: 0, personal: 1, character: 2, business: 2 } },
      { date: isoDate(subDays(new Date(), 4)), scores: { mental: 2, physical: 0, spiritual: 2, financial: 1, personal: 2, character: 1, business: 2 } },
      { date: isoDate(subDays(new Date(), 3)), scores: { mental: 2, physical: 1, spiritual: 2, financial: 2, personal: 1, character: 2, business: 1 } },
      { date: isoDate(subDays(new Date(), 2)), scores: { mental: 2, physical: 2, spiritual: 2, financial: 1, personal: 2, character: 2, business: 2 } },
      { date: isoDate(subDays(new Date(), 1)), scores: { mental: 2, physical: 1, spiritual: 2, financial: 1, personal: 2, character: 2, business: 2 } },
      { date: isoDate(new Date()), scores: { mental: 2, physical: 1, spiritual: 2, financial: 1, personal: 2, character: 1, business: 2 } },
    ],
    archive: [
      { id: 'arch-1', type: 'achievement', title: 'Reached first client milestone', date: '2026-09-20', text: 'Delivered a premium website and closed the project on time.' },
      { id: 'arch-2', type: 'review', title: 'Weekly review', date: '2026-09-18', text: 'Focused on improving follow-through and reducing task switching.' },
    ],
  };

  function nowISO() { return isoDate(new Date()); }
  function startOfDay(date) { return new Date(date.getFullYear(), date.getMonth(), date.getDate()); }
  function subDays(date, days) { const next = new Date(date); next.setDate(next.getDate() - days); return next; }
  function pad(value) { return String(value).padStart(2, '0'); }
  function isoDate(date) { return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`; }
  function isISODate(value) { if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false; const date = new Date(`${value}T00:00:00`); return !Number.isNaN(date.getTime()) && isoDate(date) === value; }
  function daysBetween(start, end) { return Math.round((startOfDay(end) - startOfDay(start)) / 86400000); }
  function ymdBetween(start, end) { let years = end.getFullYear() - start.getFullYear(); let months = end.getMonth() - start.getMonth(); let days = end.getDate() - start.getDate(); if (days < 0) { months -= 1; days += new Date(end.getFullYear(), end.getMonth(), 0).getDate(); } if (months < 0) { years -= 1; months += 12; } return { years, months, days }; }
  function formatAge(value) { return `${value.years} years, ${value.months} months, ${value.days} days`; }
  function getAgeNow() { return ymdBetween(DOB, new Date()); }
  function getLifeStats() { const now = new Date(); const age = ymdBetween(DOB, now); const yearsLived = daysBetween(DOB, now); const to30 = Math.max(0, daysBetween(now, AGE30)); const to60 = Math.max(0, daysBetween(now, AGE60)); const age30Progress = Math.min(100, Math.max(0, (yearsLived / daysBetween(DOB, AGE30)) * 100)); const age60Progress = Math.min(100, Math.max(0, (yearsLived / daysBetween(DOB, AGE60)) * 100)); return { age, yearsLived, to30, to60, age30Progress, age60Progress }; }
  function dailyScore(scores) { const total = PILLARS.reduce((sum, pillar) => sum + (Number(scores[pillar.id]) || 0), 0); return { total, pct: (total / 14) * 100 }; }
  function isRecord(value) { return value !== null && typeof value === 'object' && !Array.isArray(value); }
  function normalizeState(value) {
    if (!isRecord(value)) throw new Error('The saved data must be a JSON object.');
    const state = { ...structuredClone(defaultState), ...value };
    for (const key of ['tasks', 'goals', 'habits', 'journal', 'history', 'archive', 'big3']) {
      if (value[key] !== undefined && !Array.isArray(value[key])) throw new Error(`The "${key}" field must be a list.`);
    }
    if (value.scores !== undefined && !isRecord(value.scores)) throw new Error('The "scores" field must be an object.');
    state.currentView = VIEWS.includes(value.currentView) ? value.currentView : 'today';
    state.theme = ['system', 'light', 'dark'].includes(value.theme) ? value.theme : 'system';
    state.big3 = (value.big3 || defaultState.big3).slice(0, 3).map((item) => String(item).slice(0, 200));
    while (state.big3.length < 3) state.big3.push('');
    state.scores = Object.fromEntries(PILLARS.map(({ id }) => [id, Math.max(0, Math.min(2, Math.round(Number(value.scores?.[id] ?? defaultState.scores[id]) || 0)))]));
    state.tasks = (value.tasks || defaultState.tasks).map((item, index) => {
      if (!isRecord(item)) throw new Error('Each task in the saved data must be an object.');
      return { ...item, id: String(item.id || `task-${index}`), title: String(item.title || ''), description: String(item.description || ''), status: ['todo', 'in_progress', 'completed'].includes(item.status) ? item.status : 'todo', priority: ['low', 'medium', 'high'].includes(item.priority) ? item.priority : 'medium', dueDate: String(item.dueDate || ''), pillar: String(item.pillar || 'business') };
    });
    state.goals = (value.goals || defaultState.goals).map((item, index) => {
      if (!isRecord(item)) throw new Error('Each goal in the saved data must be an object.');
      return { ...item, id: String(item.id || `goal-${index}`), title: String(item.title || ''), description: String(item.description || ''), category: String(item.category || 'short-term'), pillar: String(item.pillar || 'personal'), target: Math.max(0, Number(item.target) || 0), current: Math.max(0, Number(item.current) || 0), unit: String(item.unit || ''), status: String(item.status || 'on-track'), deadline: String(item.deadline || '') };
    });
    state.habits = (value.habits || defaultState.habits).map((item, index) => {
      if (!isRecord(item)) throw new Error('Each habit in the saved data must be an object.');
      return { ...item, id: String(item.id || `habit-${index}`), title: String(item.title || ''), history: Array.isArray(item.history) ? [...new Set(item.history.filter(isISODate))].sort() : [] };
    });
    state.journal = (value.journal || defaultState.journal).map((item, index) => {
      if (!isRecord(item)) throw new Error('Each journal entry in the saved data must be an object.');
      return { ...item, id: String(item.id || `journal-${index}`), date: String(item.date || nowISO()), mood: String(item.mood || 'focused'), text: String(item.text || '') };
    });
    state.history = (value.history || defaultState.history).map((item) => {
      if (!isRecord(item) || !isRecord(item.scores)) throw new Error('Each progress record must contain a score object.');
      if (!isISODate(item.date)) throw new Error('Each progress record must have a valid date.');
      return { date: String(item.date || nowISO()), scores: Object.fromEntries(PILLARS.map(({ id }) => [id, Math.max(0, Math.min(2, Math.round(Number(item.scores[id]) || 0)))])) };
    });
    state.archive = (value.archive || defaultState.archive).map((item, index) => {
      if (!isRecord(item)) throw new Error('Each archive entry in the saved data must be an object.');
      return { ...item, id: String(item.id || `archive-${index}`), type: String(item.type || 'achievement'), title: String(item.title || ''), date: String(item.date || nowISO()), text: String(item.text || '') };
    });
    return state;
  }
  function loadState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? normalizeState(JSON.parse(raw)) : normalizeState(defaultState);
    } catch (error) {
      console.error('Unable to load local state.', error);
      announce('Saved data could not be loaded. The app is showing the default data instead.');
      return structuredClone(defaultState);
    }
  }
  function saveState(state) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
      return true;
    } catch (error) {
      console.error('Unable to save local state.', error);
      announce('Your browser could not save this change. Check available storage and try again.');
      return false;
    }
  }
  function announce(message) {
    document.querySelector('.toast')?.remove();
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.setAttribute('role', 'status');
    toast.textContent = message;
    document.body.appendChild(toast);
    window.setTimeout(() => toast.remove(), 5000);
  }
  function recordTodayScore(state) {
    const today = nowISO();
    const record = state.history.find((item) => item.date === today);
    if (record) record.scores = { ...state.scores };
    else state.history.push({ date: today, scores: { ...state.scores } });
  }
  function getHabitStreaks(history) {
    const dates = [...new Set(history)].sort();
    const completed = new Set(dates);
    let cursor = startOfDay(new Date());
    if (!completed.has(isoDate(cursor))) cursor = subDays(cursor, 1);
    let currentStreak = 0;
    while (completed.has(isoDate(cursor))) {
      currentStreak += 1;
      cursor = subDays(cursor, 1);
    }
    let bestStreak = 0;
    let streak = 0;
    let previous;
    dates.forEach((date) => {
      const current = new Date(`${date}T00:00:00`);
      streak = previous && daysBetween(previous, current) === 1 ? streak + 1 : 1;
      bestStreak = Math.max(bestStreak, streak);
      previous = current;
    });
    return { currentStreak, bestStreak };
  }
  function greeting() { const hour = new Date().getHours(); if (hour < 12) return 'Good morning'; if (hour < 17) return 'Good afternoon'; return 'Good evening'; }
  function formatCurrency(value) { const amount = Number(value) || 0; return `₹${amount.toLocaleString('en-IN')}`; }
  function formatGoalValue(goal, value) { return goal.unit === '₹' ? formatCurrency(value) : `${Number(value).toLocaleString()}${goal.unit ? ` ${goal.unit}` : ''}`; }
  function escapeHtml(value) { return String(value).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;'); }

  function renderToday(state, life, daily, age) {
    return `
      <div class="section-header">
        <h2>Today</h2>
        <div class="pills">
          <span class="badge">Age ${age.years}</span>
          <span class="badge">${life.to30.toLocaleString()} days to 30</span>
        </div>
      </div>
      <div class="grid grid-4">
        <div class="card metric"><span class="label">Daily score</span><strong>${daily.total}/14</strong><span class="small muted">${daily.pct.toFixed(1)}%</span></div>
        <div class="card metric"><span class="label">Age</span><strong>${age.years}</strong><span class="small muted">${formatAge(age)}</span></div>
        <div class="card metric"><span class="label">Days lived</span><strong>${life.yearsLived.toLocaleString()}</strong><span class="small muted">${Math.max(0, Math.min(100, life.age30Progress)).toFixed(1)}% to age 30</span></div>
        <div class="card metric"><span class="label">Age 60</span><strong>${life.to60.toLocaleString()}</strong><span class="small muted">${life.age60Progress.toFixed(1)}% of life horizon</span></div>
      </div>
      <div class="grid grid-2" style="margin-top: 18px;">
        <div class="card">
          <div class="section-header"><h3>Today's Big 3</h3></div>
          <form id="big3-form">
            ${state.big3.map((item, index) => `<label><span>Priority ${index + 1}</span><input type="text" name="big${index}" value="${escapeHtml(item)}" /></label>`).join('')}
            <button type="submit" class="primary-btn">Save priorities</button>
          </form>
        </div>
        <div class="card">
          <div class="section-header"><h3>Daily performance</h3><span class="badge">Max 14</span></div>
          <div class="pillars">
            ${PILLARS.map((pillar) => `
              <div class="score-row">
                <div>${pillar.name}</div>
                <div class="score-controls" data-pillar="${pillar.id}">
                  <button type="button" data-score="0" class="${Number(state.scores[pillar.id]) === 0 ? 'active' : ''}" aria-label="Not done for ${pillar.name}">❌</button>
                  <button type="button" data-score="1" class="${Number(state.scores[pillar.id]) === 1 ? 'active' : ''}" aria-label="Partial for ${pillar.name}">🟡</button>
                  <button type="button" data-score="2" class="${Number(state.scores[pillar.id]) === 2 ? 'active' : ''}" aria-label="Completed for ${pillar.name}">✅</button>
                </div>
                <strong>${Number(state.scores[pillar.id]) || 0}</strong>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
      <div class="grid grid-2" style="margin-top: 18px;">
        <div class="card">
          <div class="section-header"><h3>Top tasks</h3><button type="button" class="chip-btn" data-action="nav" data-view="tasks">View all</button></div>
          <div class="task-list">${state.tasks.filter((task) => task.status !== 'completed').slice(0, 4).map(taskItemCard).join('') || '<p class="muted">No active tasks right now.</p>'}</div>
        </div>
        <div class="card">
          <div class="section-header"><h3>Habit rhythm</h3><button type="button" class="chip-btn" data-action="nav" data-view="habits">Track</button></div>
          <div class="habit-list">${state.habits.slice(0, 4).map((habit) => {
            const streaks = getHabitStreaks(habit.history);
            const done = habit.history.includes(nowISO());
            return `<div class="habit-item"><div><strong>${escapeHtml(habit.title)}</strong><div class="small muted">Streak ${streaks.currentStreak} • Best ${Math.max(Number(habit.bestStreak) || 0, streaks.bestStreak)}</div></div><button type="button" class="${done ? 'done' : ''}" data-action="toggle-habit" data-id="${escapeHtml(habit.id)}">${done ? 'Done' : 'Mark done'}</button></div>`;
          }).join('') || '<p class="empty-state">No habits yet. Add one to start your daily rhythm.</p>'}</div>
        </div>
      </div>
    `;
  }

  function renderGoals(state) {
    return `
      <div class="section-header"><h2>Goals</h2></div>
      <div class="card">
        <h3>Create a goal</h3>
        <form id="goal-form" class="goal-form">
          <label>Goal name<input type="text" name="title" maxlength="160" placeholder="What are you working toward?" required /></label>
          <label>Category<select name="category"><option value="short-term">Short-term</option><option value="yearly">Yearly</option><option value="age-30">Age 30</option><option value="long-term">Long-term</option></select></label>
          <label>Pillar<select name="pillar">${PILLARS.map((pillar) => `<option value="${pillar.id}">${pillar.name}</option>`).join('')}</select></label>
          <label>Progress unit<input type="text" name="unit" maxlength="20" placeholder="%, ₹, books..." /></label>
          <label>Current progress<input type="number" name="current" min="0" step="any" value="0" /></label>
          <label>Target<input type="number" name="target" min="0.01" step="any" required /></label>
          <label>Deadline<input type="date" name="deadline" /></label>
          <label>Description<input type="text" name="description" maxlength="300" placeholder="Optional context" /></label>
          <button type="submit" class="primary-btn">Save goal</button>
        </form>
      </div>
      <div class="goal-list">
        ${state.goals.map((goal) => {
          const progress = Math.min(100, Math.max(0, ((Number(goal.current) || 0) / Math.max(1, Number(goal.target) || 1)) * 100));
          return `
            <div class="goal-card">
              <div class="section-header" style="margin-bottom: 6px;"><h3>${escapeHtml(goal.title)}</h3><span class="badge">${escapeHtml(goal.category)}</span></div>
              ${goal.description ? `<p class="muted">${escapeHtml(goal.description)}</p>` : ''}
              <div class="task-meta"><span class="tag">${escapeHtml(goal.pillar)}</span><span class="tag">Deadline ${escapeHtml(goal.deadline || 'TBD')}</span><span class="tag">${escapeHtml(goal.status)}</span></div>
              <div class="goal-progress"><span style="width:${progress}%"></span></div>
              <form class="goal-progress-form" data-id="${escapeHtml(goal.id)}" style="grid-template-columns: minmax(0, 1fr) auto; align-items: end; margin-top: 10px;">
                <label>Progress (${escapeHtml(goal.unit || 'units')})<input type="number" name="current" min="0" step="any" value="${escapeHtml(goal.current)}" /></label>
                <div class="pills"><span class="small muted">${escapeHtml(formatGoalValue(goal, goal.current))} / ${escapeHtml(formatGoalValue(goal, goal.target))} • ${progress.toFixed(0)}%</span><button type="submit" class="chip-btn">Update</button><button type="button" class="danger-btn" data-action="delete-goal" data-id="${escapeHtml(goal.id)}">Delete</button></div>
              </form>
            </div>
          `;
        }).join('') || '<p class="empty-state">No goals yet. Create your first goal above.</p>'}
      </div>
    `;
  }

  function renderTasks(state) {
    return `
      <div class="section-header"><h2>Tasks</h2><button type="button" class="primary-btn" data-action="quick-add" data-type="task">Add task</button></div>
      <div class="card"><form id="task-form" class="inline-form"><label><span>Task</span><input type="text" name="title" placeholder="Task name" required /></label><label><span>Priority</span><select name="priority"><option value="high">High</option><option value="medium" selected>Medium</option><option value="low">Low</option></select></label><label><span>Due</span><input type="date" name="dueDate" /></label><button type="submit" class="primary-btn">Save</button></form></div>
      <div class="task-list" style="margin-top: 18px;">${state.tasks.map(taskItemCard).join('') || '<p class="empty-state">No tasks yet. Add the first step you want to take.</p>'}</div>
    `;
  }

  function renderHabits(state) {
    return `
      <div class="section-header"><h2>Habits</h2><button type="button" class="primary-btn" data-action="quick-add" data-type="habit">Add habit</button></div>
      <div class="card"><form id="habit-form"><label><span>Habit name</span><input type="text" name="title" placeholder="Exercise, Qur'an, reading..." required /></label><button type="submit" class="primary-btn">Save habit</button></form></div>
      <div class="habit-list" style="margin-top: 18px;">${state.habits.map((habit) => {
        const streaks = getHabitStreaks(habit.history);
        const done = habit.history.includes(nowISO());
        return `<div class="habit-item"><div><strong>${escapeHtml(habit.title)}</strong><div class="small muted">Current streak: ${streaks.currentStreak} • Best streak: ${Math.max(Number(habit.bestStreak) || 0, streaks.bestStreak)}</div></div><div class="pills"><button type="button" class="${done ? 'done' : ''}" data-action="toggle-habit" data-id="${escapeHtml(habit.id)}">${done ? 'Completed' : 'Mark done'}</button><button type="button" class="danger-btn" data-action="delete-habit" data-id="${escapeHtml(habit.id)}" aria-label="Delete ${escapeHtml(habit.title)}">Delete</button></div></div>`;
      }).join('') || '<p class="empty-state">No habits yet. Add one to build a consistent routine.</p>'}</div>
    `;
  }

  function renderProgress(state) {
    const today = startOfDay(new Date());
    const weekStart = subDays(today, 6);
    const monthStart = subDays(today, 29);
    const weekRecords = state.history.filter((entry) => daysBetween(weekStart, new Date(`${entry.date}T00:00:00`)) >= 0 && daysBetween(new Date(`${entry.date}T00:00:00`), today) >= 0);
    const monthRecords = state.history.filter((entry) => daysBetween(monthStart, new Date(`${entry.date}T00:00:00`)) >= 0 && daysBetween(new Date(`${entry.date}T00:00:00`), today) >= 0);
    const average = (records) => records.length ? records.reduce((sum, entry) => sum + dailyScore(entry.scores).total, 0) / records.length : 0;
    const weeklyAvg = average(weekRecords);
    const monthlyAvg = average(monthRecords);
    const strongest = state.history.length ? PILLARS.map((pillar) => ({ pillar, value: state.history.reduce((sum, entry) => sum + (Number(entry.scores[pillar.id]) || 0), 0) })).sort((a, b) => b.value - a.value)[0] : null;
    return `
      <div class="section-header"><h2>Progress</h2><span class="badge">This week ${weeklyAvg.toFixed(1)}/14 avg</span></div>
      <div class="grid grid-4">
        <div class="card metric"><span class="label">Today</span><strong>${dailyScore(state.scores).total}/14</strong><span class="small muted">${dailyScore(state.scores).pct.toFixed(1)}%</span></div>
        <div class="card metric"><span class="label">This week</span><strong>${weeklyAvg.toFixed(1)}</strong><span class="small muted">Average</span></div>
        <div class="card metric"><span class="label">This month</span><strong>${monthlyAvg.toFixed(1)}</strong><span class="small muted">Average per logged day</span></div>
        <div class="card metric"><span class="label">Age 30</span><strong>${getLifeStats().age30Progress.toFixed(0)}%</strong><span class="small muted">${strongest ? strongest.pillar.name : 'N/A'}</span></div>
      </div>
      <div class="card" style="margin-top: 18px;">
        <h3>Pillar performance</h3>
        <div class="pillars">
          ${PILLARS.map((pillar) => {
            const score = state.history.reduce((sum, entry) => sum + (Number(entry.scores[pillar.id]) || 0), 0);
            const possible = state.history.length * 2;
            const pct = possible ? (score / possible) * 100 : 0;
            return `<div class="score-row"><div>${pillar.name}</div><div class="small muted">${score} / ${possible}</div><div class="goal-progress"><span style="width:${pct}%"></span></div></div>`;
          }).join('')}
        </div>
      </div>
    `;
  }

  function renderLife(life, age) {
    return `
      <div class="section-header"><h2>Life</h2></div>
      <div class="life-grid">
        <div class="card"><h3>About me</h3><p class="muted">Muhammed Nezamudheen is a founder, software developer, and digital entrepreneur building a long-term life with clarity, discipline, and purpose.</p></div>
        <div class="card"><h3>Life clock</h3><p class="muted">Age ${age.years} • ${life.to30.toLocaleString()} days to 30 • ${life.to60.toLocaleString()} days to 60</p></div>
        <div class="card"><h3>Vision</h3><p class="muted">Build the man first. Build a stable, useful, credible life that can sustain peace, prosperity, and legacy.</p></div>
      </div>
      <div class="card" style="margin-top: 18px;"><h3>Mission stages</h3><div class="life-grid">${[['Reset & Foundation', 'Create stability in sleep, faith, health, money, and discipline.'], ['Build', 'Develop capability, business systems, and personal traction.'], ['Scale', 'Turn repeatable systems into predictable growth and leverage.'], ['Age-30 Preparation', 'Review all pillars and become the man intended by the vision.']].map(([title, text]) => `<div class="card"><h4>${title}</h4><p class="muted">${text}</p></div>`).join('')}</div></div>
      <div class="card" style="margin-top: 18px;"><h3>Age-30 scorecard</h3><div class="pillars">${PILLARS.map((pillar) => `<div class="score-row"><div>${pillar.name}</div><div class="small muted">Vision → target → evidence</div><div class="tag">${getLifeStats().age30Progress.toFixed(0)}%</div></div>`).join('')}</div></div>
    `;
  }

  function renderJournal(state) {
    return `
      <div class="section-header"><h2>Journal</h2></div>
      <div class="card"><form id="journal-form"><label><span>Mood</span><select name="mood"><option value="focused">Focused</option><option value="strong">Strong</option><option value="tired">Tired</option><option value="grateful">Grateful</option></select></label><label><span>Entry</span><textarea name="text" placeholder="What went well? What went wrong? What should change tomorrow?" required></textarea></label><button type="submit" class="primary-btn">Save journal</button></form></div>
      <div class="journal-list" style="margin-top: 18px;">${state.journal.map((entry) => `<div class="journal-item"><div class="section-header" style="margin-bottom: 8px;"><strong>${escapeHtml(entry.date)}</strong><span class="badge">${escapeHtml(entry.mood)}</span></div><p class="muted">${escapeHtml(entry.text)}</p><button type="button" class="danger-btn" data-action="delete-journal" data-id="${escapeHtml(entry.id)}">Delete entry</button></div>`).join('') || '<p class="empty-state">Your journal is empty. Add an entry whenever you want to reflect.</p>'}</div>
    `;
  }

  function renderArchive(state) {
    return `
      <div class="section-header"><h2>Archive</h2></div>
      <div class="card">
        <h3>Add to your archive</h3>
        <form id="archive-form" class="archive-form">
          <label>Title<input type="text" name="title" maxlength="160" required /></label>
          <label>Type<select name="type"><option value="achievement">Achievement</option><option value="review">Review</option><option value="milestone">Milestone</option><option value="memory">Memory</option></select></label>
          <label>Date<input type="date" name="date" value="${nowISO()}" required /></label>
          <label class="wide">Notes<textarea name="text" maxlength="2000" placeholder="Add a little context (optional)"></textarea></label>
          <button type="submit" class="primary-btn">Save to archive</button>
        </form>
      </div>
      <div class="archive-list" style="margin-top: 18px;">${state.archive.map((item) => `<div class="archive-item"><div class="section-header" style="margin-bottom: 8px;"><h3>${escapeHtml(item.title)}</h3><span class="badge">${escapeHtml(item.type)}</span></div><div class="small muted">${escapeHtml(item.date)}</div>${item.text ? `<p class="muted">${escapeHtml(item.text)}</p>` : ''}<button type="button" class="danger-btn" data-action="delete-archive" data-id="${escapeHtml(item.id)}">Delete</button></div>`).join('') || '<p class="empty-state">Nothing archived yet. Save milestones and reflections here.</p>'}</div>
    `;
  }

  function renderApp() {
    const state = loadState();
    const root = document.getElementById('app-root');
    if (!root) return;
    const life = getLifeStats();
    const age = getAgeNow();
    const daily = dailyScore(state.scores);
    const theme = state.theme === 'system' ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light') : state.theme;
    document.body.setAttribute('data-theme', theme);
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', theme === 'dark' ? '#10131a' : '#f4f5f8');

    root.innerHTML = `
      <div class="app-shell">
        <aside class="sidebar">
          <div class="brand"><div class="brand-kicker">Life OS</div><h1>MDNDN</h1><p>Build the man first. Build the life second. Build the legacy third.</p></div>
          <nav class="nav" aria-label="Primary navigation">
            ${[['today', 'Today'], ['goals', 'Goals'], ['tasks', 'Tasks'], ['habits', 'Habits'], ['progress', 'Progress'], ['life', 'Life'], ['journal', 'Journal'], ['archive', 'Archive']].map(([view, label], index) => `<button type="button" class="${state.currentView === view ? 'active' : ''}" data-view="${view}"${state.currentView === view ? ' aria-current="page"' : ''}><span class="nav-label">${label}</span><span class="nav-index">${String(index + 1).padStart(2, '0')}</span></button>`).join('')}
          </nav>
          <div class="sidebar-metric"><div class="label">Days to age 30</div><strong>${life.to30.toLocaleString()}</strong><div class="progress-bar"><span style="width:${Math.max(0, Math.min(100, (life.yearsLived / daysBetween(DOB, AGE30)) * 100))}%"></span></div></div>
        </aside>
        <main class="main-pane">
          <header class="topbar"><div class="meta"><div class="eyebrow">${greeting()}</div><h2>${new Date().toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}</h2></div><div class="actions"><button type="button" class="chip-btn" data-action="theme-toggle" aria-label="Switch to ${theme === 'dark' ? 'light' : 'dark'} mode">Use ${theme === 'dark' ? 'light' : 'dark'} mode</button><button type="button" class="chip-btn" data-action="backup-import">Import</button><button type="button" class="action-btn" data-action="backup-export">Export</button><button type="button" class="danger-btn" data-action="backup-clear">Clear</button></div></header>
          <section class="view ${state.currentView === 'today' ? 'active' : ''}" data-view-section="today">${renderToday(state, life, daily, age)}</section>
          <section class="view ${state.currentView === 'goals' ? 'active' : ''}" data-view-section="goals">${renderGoals(state)}</section>
          <section class="view ${state.currentView === 'tasks' ? 'active' : ''}" data-view-section="tasks">${renderTasks(state)}</section>
          <section class="view ${state.currentView === 'habits' ? 'active' : ''}" data-view-section="habits">${renderHabits(state)}</section>
          <section class="view ${state.currentView === 'progress' ? 'active' : ''}" data-view-section="progress">${renderProgress(state)}</section>
          <section class="view ${state.currentView === 'life' ? 'active' : ''}" data-view-section="life">${renderLife(life, age)}</section>
          <section class="view ${state.currentView === 'journal' ? 'active' : ''}" data-view-section="journal">${renderJournal(state)}</section>
          <section class="view ${state.currentView === 'archive' ? 'active' : ''}" data-view-section="archive">${renderArchive(state)}</section>
        </main>
      </div>
      <button class="fab" type="button" aria-label="Quick actions" aria-expanded="false" data-action="quick-add-toggle">+</button>
      <div class="quick-menu" id="quick-menu" aria-label="Quick actions"><button type="button" data-action="quick-add" data-type="task">Add task</button><button type="button" data-action="quick-add" data-type="goal">Add goal</button><button type="button" data-action="quick-add" data-type="habit">Add habit</button><button type="button" data-action="quick-add" data-type="journal">Write journal</button></div>
    `;
    bindGlobalEvents();
  }

  function taskItemCard(task) {
    return `
      <div class="task-item">
        <div class="task-main">
          <input type="checkbox" ${task.status === 'completed' ? 'checked' : ''} data-status="${escapeHtml(task.status)}" data-action="toggle-task" data-id="${escapeHtml(task.id)}" aria-label="Toggle task ${escapeHtml(task.title)}" />
          <div>
            <strong>${escapeHtml(task.title)}</strong>
            ${task.description ? `<div class="small muted">${escapeHtml(task.description)}</div>` : ''}
            <div class="task-meta">
              <span class="tag ${escapeHtml(task.priority)}">${escapeHtml(task.priority)}</span>
              ${task.dueDate ? `<span class="tag">Due ${escapeHtml(task.dueDate)}</span>` : ''}
              <span class="tag">${escapeHtml(task.status.replace('_', ' '))}</span>
            </div>
          </div>
        </div>
        <button type="button" class="danger-btn" data-action="delete-task" data-id="${escapeHtml(task.id)}">Delete</button>
      </div>
    `;
  }

  function bindGlobalEvents() {
    document.querySelectorAll('[data-view]').forEach((button) => {
      button.addEventListener('click', () => {
        const view = button.dataset.view;
        if (view) { const next = loadState(); next.currentView = view; saveState(next); renderApp(); }
      });
    });

    document.getElementById('archive-form')?.addEventListener('submit', (event) => {
      event.preventDefault();
      const form = new FormData(event.currentTarget);
      const title = String(form.get('title') || '').trim();
      if (!title) return;
      const next = loadState();
      next.archive.unshift({ id: `archive-${Date.now()}`, title, type: String(form.get('type') || 'achievement'), date: String(form.get('date') || nowISO()), text: String(form.get('text') || '').trim() });
      saveState(next);
      renderApp();
    });

    document.querySelectorAll('[data-action="theme-toggle"]').forEach((button) => {
      button.addEventListener('click', () => {
        const next = loadState(); next.theme = document.body.dataset.theme === 'dark' ? 'light' : 'dark'; saveState(next); renderApp();
      });
    });

    document.querySelectorAll('[data-action="backup-export"]').forEach((button) => {
      button.addEventListener('click', () => {
        const blob = new Blob([JSON.stringify(loadState(), null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = `mdndn-backup-${isoDate(new Date())}.json`; document.body.appendChild(link); link.click(); link.remove(); window.setTimeout(() => URL.revokeObjectURL(url), 1000);
      });
    });

    document.querySelectorAll('[data-action="backup-import"]').forEach((button) => {
      button.addEventListener('click', () => {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'application/json,.json';
        input.addEventListener('change', (event) => {
          const file = event.target.files?.[0];
          if (!file) return;
          const reader = new FileReader();
          reader.onload = () => {
            try {
              const parsed = JSON.parse(String(reader.result));
              if (!window.confirm('Importing a backup will replace the data saved in this browser. Continue?')) return;
              const next = normalizeState(parsed);
              if (saveState(next)) {
                announce('Backup imported successfully.');
                renderApp();
              }
            } catch (error) {
              console.error('Unable to import backup.', error);
              announce(`Backup could not be imported: ${error.message}`);
            }
          };
          reader.onerror = () => announce('The selected backup file could not be read.');
          reader.readAsText(file);
        });
        input.click();
      });
    });

    document.querySelectorAll('[data-action="backup-clear"]').forEach((button) => {
      button.addEventListener('click', () => {
        if (window.confirm('Clear all MDNDN data from this browser? This cannot be undone.')) {
          try {
            localStorage.removeItem(STORAGE_KEY);
            renderApp();
            announce('Saved data cleared.');
          } catch (error) {
            console.error('Unable to clear local state.', error);
            announce('Saved data could not be cleared. Check your browser storage settings.');
          }
        }
      });
    });

    document.querySelectorAll('[data-action="quick-add-toggle"]').forEach((button) => {
      button.addEventListener('click', () => {
        const menu = document.getElementById('quick-menu');
        const open = menu.classList.toggle('open');
        button.setAttribute('aria-expanded', String(open));
      });
    });

    document.querySelectorAll('[data-action="quick-add"]').forEach((button) => {
      button.addEventListener('click', () => {
        const type = button.dataset.type || 'task';
        const next = loadState();
        next.currentView = type === 'goal' ? 'goals' : type === 'habit' ? 'habits' : type === 'journal' ? 'journal' : 'tasks';
        saveState(next); renderApp();
      });
    });

    document.querySelectorAll('[data-action="toggle-habit"]').forEach((button) => {
      button.addEventListener('click', () => {
        const next = loadState();
        const habit = next.habits.find((item) => item.id === button.dataset.id);
        if (!habit) return;
        const todayKey = nowISO();
        if (habit.history.includes(todayKey)) habit.history = habit.history.filter((date) => date !== todayKey);
        else habit.history.push(todayKey);
        const streaks = getHabitStreaks(habit.history);
        habit.currentStreak = streaks.currentStreak;
        habit.bestStreak = Math.max(Number(habit.bestStreak) || 0, streaks.bestStreak);
        saveState(next);
        renderApp();
      });
    });

    document.getElementById('task-form')?.addEventListener('submit', (event) => {
      event.preventDefault();
      const form = new FormData(event.currentTarget);
      const next = loadState();
      const title = String(form.get('title') || '').trim();
      if (!title) return; next.tasks.unshift({ id: `task-${Date.now()}`, title, description: '', priority: String(form.get('priority') || 'medium'), dueDate: String(form.get('dueDate') || ''), status: 'todo', pillar: 'business', createdAt: nowISO() }); saveState(next); renderApp();
    });

    document.getElementById('goal-form')?.addEventListener('submit', (event) => {
      event.preventDefault();
      const form = new FormData(event.currentTarget);
      const title = String(form.get('title') || '').trim();
      const target = Number(form.get('target'));
      const current = Number(form.get('current'));
      if (!title || !Number.isFinite(target) || target <= 0 || !Number.isFinite(current) || current < 0) {
        announce('Enter a goal name, a positive target, and a valid current value.');
        return;
      }
      const next = loadState();
      next.goals.unshift({
        id: `goal-${Date.now()}`,
        title,
        description: String(form.get('description') || '').trim(),
        category: String(form.get('category') || 'short-term'),
        pillar: String(form.get('pillar') || 'personal'),
        current,
        target,
        unit: String(form.get('unit') || '').trim(),
        status: current >= target ? 'completed' : 'on-track',
        deadline: String(form.get('deadline') || ''),
      });
      saveState(next);
      renderApp();
    });

    document.querySelectorAll('.goal-progress-form').forEach((goalForm) => {
      goalForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const form = new FormData(goalForm);
        const current = Number(form.get('current'));
        if (!Number.isFinite(current) || current < 0) {
          announce('Goal progress must be zero or a positive number.');
          return;
        }
        const next = loadState();
        const goal = next.goals.find((item) => item.id === goalForm.dataset.id);
        if (!goal) return;
        goal.current = current;
        goal.status = current >= goal.target ? 'completed' : 'on-track';
        saveState(next);
        renderApp();
      });
    });

    document.getElementById('habit-form')?.addEventListener('submit', (event) => {
      event.preventDefault();
      const form = new FormData(event.currentTarget); const title = String(form.get('title') || '').trim(); if (!title) return; const next = loadState(); next.habits.push({ id: `habit-${Date.now()}`, title, currentStreak: 0, bestStreak: 0, history: [] }); saveState(next); renderApp();
    });

    document.getElementById('journal-form')?.addEventListener('submit', (event) => {
      event.preventDefault();
      const form = new FormData(event.currentTarget); const text = String(form.get('text') || '').trim(); if (!text) return; const next = loadState(); next.journal.unshift({ id: `jour-${Date.now()}`, date: nowISO(), mood: String(form.get('mood') || 'focused'), text }); saveState(next); renderApp();
    });

    document.getElementById('big3-form')?.addEventListener('submit', (event) => {
      event.preventDefault(); const form = new FormData(event.currentTarget); const next = loadState(); next.big3 = [0,1,2].map((index) => String(form.get(`big${index}`) || '').trim()).filter(Boolean); while (next.big3.length < 3) next.big3.push(''); saveState(next); renderApp();
    });

    document.querySelectorAll('[data-pillar]').forEach((group) => {
      group.addEventListener('click', (event) => {
        const btn = event.target.closest('button[data-score]'); if (!btn) return; const next = loadState(); next.scores[group.dataset.pillar] = Number(btn.dataset.score); recordTodayScore(next); saveState(next); renderApp();
      });
    });

    document.querySelectorAll('[data-action="toggle-task"]').forEach((input) => {
      input.addEventListener('change', () => {
        const next = loadState(); const task = next.tasks.find((item) => item.id === input.dataset.id); if (!task) return; task.status = input.checked ? 'completed' : (input.dataset.status === 'completed' ? 'todo' : input.dataset.status); saveState(next); renderApp();
      });
    });

  }

  document.addEventListener('click', (event) => {
    const quickMenu = document.getElementById('quick-menu'); if (quickMenu && !event.target.closest('.fab') && !event.target.closest('#quick-menu')) quickMenu.classList.remove('open');
    const deleteBtn = event.target.closest('[data-action^="delete-"]');
    if (deleteBtn) {
      const next = loadState();
      const collectionByAction = {
        'delete-task': 'tasks',
        'delete-goal': 'goals',
        'delete-habit': 'habits',
        'delete-journal': 'journal',
        'delete-archive': 'archive',
      };
      const collection = collectionByAction[deleteBtn.dataset.action];
      if (collection) {
        next[collection] = next[collection].filter((item) => item.id !== deleteBtn.dataset.id);
        saveState(next);
        renderApp();
      }
    }
  });

  document.addEventListener('DOMContentLoaded', renderApp);
})();
