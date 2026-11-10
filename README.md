# Fleet Intelligence System

Streamlit and MySQL fleet operations app for the existing `omnilogistics` database.
Current state: **1.1.0**. Includes the Command Center, offline route network, rule-based
operational alerts, live dispatch board with filtered CSV export, driver performance
scorecards, searchable CRUD for all eight database tables, live system/schema health,
filterable reports and local image uploads for drivers, brands and trucks.

## Project team

- [Mir Said Sahin](https://github.com/mirsaidsahin) — Project owner
- Teammate: [amk1005799Heli](https://github.com/amk1005799Heli)

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
