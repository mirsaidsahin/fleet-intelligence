# Fleet Intelligence System

Streamlit and MySQL fleet operations app for the existing `omnilogistics` database.
The Command Center brings fleet status, dispatch work and route activity into one view. Fleet, driver and operations records can also be maintained from
the app, with a database connection check on the System page.

## What the app includes

- A Command Center with fleet counts, a fleet map, status charts and
  recent operating activity.
- A sidebar note that map positions are illustrative rather than live GPS data and that brand
  logos are for demonstration only.
- A route map with truck tooltips. Illustrative truck points
  are randomized along their assigned routes on page refresh and every ten minutes; they
  are not GPS locations.
- Fleet and operations workspaces for trucks, brands, garages, jobs, cargo, routes and
  customers, plus driver record management.
- A searchable dispatch board with CSV export and a database connection panel on the System page.
- Job status transition rules, overlapping truck/driver assignment checks, and linked-record
  impact warnings before deletion.
- Local image previews for drivers, brands and trucks (images are placed by hand in the
  `assets/` folder), with a shared dark interface using warm amber, muted green and steel tones.
- Form validation for required fields, non-negative numeric values, and consistent job dates,
  with database errors translated into short, actionable messages.

The app reads and writes the existing MySQL `omnilogistics` database; it does not need an
AI service or API key.

## Project team

- [Mir Said Sahin](https://github.com/mirsaidsahin) — Project owner
- Teammate: [amk1005799Heli](https://github.com/amk1005799Heli)
- [Md Afsar Hossain](https://github.com/MdAfsarhossain123) — Teammate

## Setup

1. Create and activate a virtual environment.
   - Windows: `python -m venv .venv` then `.venv\Scripts\activate`
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.
4. For a new empty database, select the database and run `database/schema.sql` as a MySQL administrator.
   For the existing database from the course, keep its tables and data; do not run `BACKUP.sql`.
5. Run `database/create_app_user.sql` as a MySQL administrator after replacing its placeholder password.
   The account needs `SELECT`, `INSERT`, `UPDATE` and `DELETE` grants for CRUD.
6. Start the app: `streamlit run app.py`

## Validation and error handling

- Record forms check required text fields, non-negative numeric values, whole-number fields,
  and ensure a job's end date is not earlier than its start date.
- Database exceptions are logged for diagnosis while the interface displays safe messages
  that do not expose raw SQL, host details, or credentials.

More detail is in [docs/VALIDATION_AND_ERRORS.md](docs/VALIDATION_AND_ERRORS.md).

## Tests

`python -m pytest` from the project root. The suite covers configuration, validation, database
error mapping, SQL safety, fleet status rules, image handling, CRUD behavior for all eight
entities, SQLite repository integration, and Streamlit AppTest checks for delete safeguards.
Tests use fakes or temporary in-memory databases and never read `.env` or contact production MySQL.

**MySQL integration test (opt-in).** `tests/test_mysql_integration.py` inserts a brand through
`FleetRepository`, reads it back and deletes it, on the separate `omnilogistics_test` database only.
Create that database once with `database/create_test_database.sql` (structure only, no data), then run:
`$env:RUN_MYSQL_TESTS = "1"; python -m pytest tests/test_mysql_integration.py -v`

**Code quality.** Run `ruff check .` (linter) together with `python -m pytest`.

## Structure

```
app.py          entry point, navigation, status bar
pages/          one script per navigation section
components/     theme, status bar, panels, fleet map, shared UI helpers, bootstrap (Streamlit code)
services/       job status rules, workflow safeguards, image assets
repositories/   allow-listed SQL access and dashboard reports
utils/          config, db engine and connection status, logging, SQL guard, error messages
database/       schema.sql, create_app_user.sql, update_garages_to_route_network.sql
docs/           DEFINITIONS.md, DESIGN.md, VALIDATION_AND_ERRORS.md
assets/         local images, ignored by git
```

## Database usage

The app uses eight tables in the MySQL `omnilogistics` database (full definition in
`database/schema.sql`):

| Table | Holds | Linked to | Managed on |
|---|---|---|---|
| `brands` | Truck manufacturers | — | Fleet |
| `garages` | Regional garages | — | Fleet |
| `trucks` | Vehicles, plate, mileage, required licence | brand, garage, assigned driver | Fleet |
| `drivers` | Drivers and licence class | mentor (another driver) | Fleet |
| `customers` | Customer companies | — | Operations |
| `routes` | City-to-city routes, distance, hours | specialist driver | Operations |
| `cargos` | Cargo types and default route | route | Operations |
| `jobs` | Deliveries with dates and status | customer, truck, driver, cargo, route | Operations |

- `repositories/fleet.py` holds all SQL. `FleetRepository` performs CRUD on the eight tables
  with bound parameters; `DashboardRepository` runs the read-only queries (JOIN, GROUP BY)
  behind the Command Center.
- Writes run inside a transaction (`Database.transaction`), so a saved form is committed to MySQL.
- Before a delete, the app counts linked rows (for example jobs that use a truck) and blocks the
  delete while they exist; MySQL foreign keys enforce the same rule.

## Safety

- The app never issues DDL and never recreates tables. The supplied dump contains `DROP TABLE` and must not be run against the live database.
- Credentials come from environment variables or `.env`. `.env` is git-ignored and passwords are redacted from logs.
- Raw database errors go to `logs/app.log`; the UI shows short messages.
- CRUD is limited to the eight known application tables and uses bound values. MySQL foreign-key constraints remain authoritative.
- Records show up to 500 rows per table.

## Troubleshooting

| Message | Fix |
|---|---|
| Authentication failed | Check `DB_USER` and `DB_PASSWORD` |
| Cannot reach the MySQL server | Start the MySQL service; check `DB_HOST` and `DB_PORT` |
| `cryptography` package is missing | `pip install cryptography` (MySQL 8 sign-in needs it) |

Definitions for the available schema and status/image conventions: `docs/DEFINITIONS.md`.
Validation and error behavior: `docs/VALIDATION_AND_ERRORS.md`.
Interface colors, type, spacing and accessibility rules: `docs/DESIGN.md`.
