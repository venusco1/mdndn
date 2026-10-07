# MDNDN Life OS

A private, browser-based personal dashboard for daily priorities, tasks, goals, habits, progress, journaling, and milestones. Your data is stored in this browser; it is not sent to a server.

## Run locally

Open `index.html` in a modern browser. For deployment, build the static site and publish the contents of `dist/`:

```sh
npm run build
```

The build copies the app and its assets into `dist/` and generates the sitemap. Node.js 18 or later is required.

## Backups

Use **Export** to download a JSON backup and **Import** to restore one in another browser. Keep exported files somewhere safe; clearing browser data removes the local copy.