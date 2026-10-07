# MDNDN Life OS

A private, browser-based personal planning system. The read-only home page explains the vision, the dashboard is the action workspace for priorities, goals, tasks, habits, progress, journaling, and milestones, and the [User Guide](user-guide.html) explains the purpose and use of each feature.

## Run locally

Open `index.html` in a modern browser. Follow its Dashboard or User Guide links to move between pages. For deployment, build the static site and publish the contents of `dist/`:

```sh
npm run build
```

The build copies all HTML pages and assets into `dist/` and generates the sitemap. Node.js 18 or later is required.

## Data and backups

Dashboard data is stored locally in the current browser and is not sent to a server or automatically synchronized to other devices. Use **Export** to download a JSON backup and **Import** to replace the local data with a backup. Keep exported files somewhere safe; clearing browser data removes the local copy. See the User Guide's [privacy and backups section](user-guide.html#data) before moving or clearing data.

## Features

- Overview with daily priorities, seven-pillar scorecard, life metrics, open tasks, and habit check-ins
- Goals with categories, deadlines, target values, and progress updates
- Tasks with priorities, due dates, completion, and deletion
- Habits with daily check-ins and consecutive-day streaks
- Progress summaries, journal entries, and a dated archive
- Light/dark theme, quick-add menu, and JSON export/import