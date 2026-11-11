# Fleet Intelligence System

Streamlit and MySQL fleet operations app for the existing `omnilogistics` database.
The Command Center brings fleet status, dispatch work, route activity and operational
alerts into one view. Fleet, driver and operations records can also be maintained from
the app, with system checks and filtered data exports available in Reports & System.

## What the app includes

- A Command Center with fleet counts, dispatch attention items, driver performance and
  recent operating activity.
- An interactive route map with truck and driver photo previews. Map positions are
  illustrative: they are placed along planned routes, change when the page is refreshed,
  and update automatically every ten minutes. They are not GPS locations.
- Fleet and operations workspaces for trucks, brands, garages, jobs, cargo, routes and
  customers, plus driver record management.
- Rule-based checks for jobs that need dispatch review, database/schema status panels,
  searchable reports and CSV downloads.
- Local image uploads for drivers, brands and trucks, with a shared dark interface using
  warm amber, muted green and steel tones.

The app reads and writes the existing MySQL `omnilogistics` database; it does not need an
AI service or API key.

## Project team

- [Mir Said Sahin](https://github.com/mirsaidsahin) — Project owner
- Teammate: [amk1005799Heli](https://github.com/amk1005799Heli)
- Teammate : ” https://github.com/MdAfsarhossain123 “

## Setup

1. Create and activate a virtual environment.
   - Windows: `python -m venv .venv` then `.venv\Scripts\activate`
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.
4. For a new empty database, select the database and run `docs/schema.sql` as a MySQL administrator.
   For the existing database from the course, keep its tables and data; do not run `BACKUP.sql`.
5. Run `docs/create_app_user.sql` as a MySQL administrator after replacing its placeholder password.
   The account needs `SELECT`, `INSERT`, `UPDATE` and `DELETE` grants for CRUD.
6. Check the connection and schema (read-only): `python scripts/verify_schema.py`
7. Start the app: `streamlit run app.py`

## Tests

`python -m pytest` from the project root. Tests use fakes and never read `.env` or connect to MySQL.

## Structure

```
app.py          entry point, navigation, status bar
pages/          one script per navigation section
components/     theme, status bar, panels, bootstrap (Streamlit code)
services/       health, schema verification, status rules, visual convention
repositories/   allow-listed SQL access and dashboard reports
models/         plain data classes and the expected schema
utils/          config, db engine, logging, SQL guard, error messages
docs/           schema.sql, DEFINITIONS.md, create_app_user.sql
assets/         local images, ignored by git
```

## Safety

- The app never issues DDL and never recreates tables. The supplied dump contains `DROP TABLE` and must not be run against the live database.
- Credentials come from environment variables or `.env`. `.env` is git-ignored and passwords are redacted from logs.
- Raw database errors go to `logs/app.log`; the UI shows short messages.
- CRUD is limited to the eight known application tables and uses bound values. MySQL foreign-key constraints remain authoritative.
- Records and reports show up to 500 rows per table; CSV export respects the selected report filters.

## Troubleshooting

| Message | Fix |
|---|---|
| Authentication failed | Check `DB_USER` and `DB_PASSWORD` |
| Cannot reach the MySQL server | Start the MySQL service; check `DB_HOST` and `DB_PORT` |
| `cryptography` package is missing | `pip install cryptography` (MySQL 8 sign-in needs it) |

Definitions for the available schema and status/image conventions: `docs/DEFINITIONS.md`.
