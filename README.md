# Vision 30 — MDNDN Life OS

Vision 30 is a private, single-user Django application for planning, executing,
reviewing, and preserving a personal development journey. It uses Django's
authentication, SQLite persistence, accessible server-rendered forms, and the
existing Life OS visual design. The static HTML site is retained as a read-only
legacy reference; the Django application is the primary dashboard.

## Local setup

Python 3.10 or later is required. From the project directory:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_vision30
python manage.py createsuperuser
python manage.py runserver
```

Open <http://127.0.0.1:8000/> and sign in with the account created above. The
first setup creates the editable eight-pillar, ten-block, 80-stage framework;
it does **not** create example tasks, goals, habits, check-ins, or progress.
Use `/admin/` to manage detailed records and accounts.
The app defaults to a dark theme across the sign-in and Life OS pages; change
the theme from **Settings** if you prefer the light palette.

SQLite stores app records in `db.sqlite3` by default. Set `DJANGO_DB_PATH` to
choose another database file. `DJANGO_TIME_ZONE` sets the initial timezone;
the signed-in app's editable timezone preference takes effect on requests.

## Dates and blocks

The master journey runs inclusively from **6 October 2026** through **18 July
2029** (1,017 calendar days). Block 01 starts **15 October 2026**; with its
first day counted as Day 01, its 100th day is **22 January 2027**. Ten
consecutive 100-day blocks end **10 July 2029**. The application keeps the
9-day pre-block period and 8-day post-block transition visible; changing master
dates does not silently rewrite saved block dates.

Run `python manage.py seed_vision30` again to restore any missing framework
records. The command is idempotent and does not overwrite edited framework
content or create personal activity.

## Daily use and measurements

Today brings priorities, due tasks, eight pillar check-ins, habit completion,
an optional mood/energy check, and an evening reflection together. Tasks and
habits measure execution; target values, evidence, and reviews describe
outcomes. Those measures remain separate. Each pillar has its own selectable
measurement approach rather than contributing to a universal life score.
Saving an evening reflection records that day's execution snapshot when
planned items exist. Progress shows saved scores and compares available
recorded days in the current and preceding seven-day periods; empty days remain
unscored rather than appearing as zero or being inferred later.

Weekly, monthly, block, and stage reviews preserve wins, problems, missed
commitments, evidence, lessons, and next actions. A target is not marked
achieved merely because its numeric progress reaches the target; completion
criteria and status are reviewed explicitly.

## Existing browser data and backups

The former static dashboard used browser `localStorage`; Django cannot read
that browser storage automatically. In the old dashboard, choose **Export** to
download its JSON file. In the Django app, open **Settings** and import that
file. Import validates the content, leaves the source unchanged, preserves
existing personal records, and recognizes an exact file already imported to
prevent duplicate imports. A complete Vision 30 backup updates matching
framework plans and settings. The older dashboard shipped with example goals,
activity, and scores when no local backup existed; review a legacy JSON file
and remove any placeholders before importing. Legacy scores become historical
practice check-ins only; no missing pillar history or outcome progress is
inferred.

**Export backup** downloads the complete framework and personal records as
JSON. Keep backups in a private location. Django records persist in SQLite
across browser reloads and sessions.

## Security and deployment

The app requires a Django login. Create and manage users with `createsuperuser`
or `/admin/`. For a private deployment, set a unique `DJANGO_SECRET_KEY`,
`DJANGO_DEBUG=0`, and an explicit `DJANGO_ALLOWED_HOSTS`; serve over HTTPS and
protect database and backup files. Do not expose Django's development server
directly to the public internet.

## Production deployment (Render + Neon)

This project is ready for a free Render web service backed by a Neon free
PostgreSQL database. In production, set the following environment variables in
Render's dashboard or `render.yaml`:

- `SECRET_KEY` — a unique secret value for Django.
- `DEBUG` — set to `False`.
- `DATABASE_URL` — the Neon PostgreSQL connection string, including
  `?sslmode=require`.
- `DJANGO_ALLOWED_HOSTS` — optional if Render auto-provides
  `RENDER_EXTERNAL_HOSTNAME`; the app also reads that automatically.

Render build command:

```bash
./build.sh
```

Render start command:

```bash
python -m gunicorn vision30.wsgi:application --bind 0.0.0.0:$PORT
```

The app uses WhiteNoise for static files and runs `collectstatic` during build.
The project keeps the local SQLite database for development and expects a fresh
Neon PostgreSQL database for production. Run `python manage.py migrate --noinput`
after the deployment environment is connected and then create a superuser with
`python manage.py createsuperuser`.

## Tests

```powershell
python manage.py test lifeos
python manage.py check
```

The test suite exercises the inclusive timeline, seed idempotency, login
protection, daily workflow, reviews, and backup import/export.
