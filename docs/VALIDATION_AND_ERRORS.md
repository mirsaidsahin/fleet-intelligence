# Validation and error handling

This document describes the checks performed by Fleet Intelligence before a write and how
failures are presented. MySQL remains the final authority for schema constraints and
relationships.

## Record forms

The shared create/edit forms in `components/entity_manager.py` use the rules in
`services/input_validation.py`:

- Required text fields cannot be blank or whitespace-only.
- Numeric fields cannot be negative; integer fields must be whole numbers.
- A job's `EndDate` must be the same as or later than `StartDate` when both are supplied.
- Optional relationships and dates may be left empty where the schema permits them.
- Select controls limit license and job status values to the supported choices; relationship
  controls use IDs loaded from the corresponding table.

The numeric widgets also enforce a zero minimum. Validation is repeated at form submission
so invalid values are reported next to the save action and can be covered without a database.

Job status edits follow a one-way workflow: Pending jobs may remain Pending, enter In Transit,
or be Cancelled; In Transit jobs may remain In Transit, become Completed, or be Cancelled;
Completed and Cancelled jobs are terminal. Before saving an open job, the app checks whether its
truck or driver has another open job with an overlapping estimated time window. The database
remains authoritative if concurrent changes occur after the check.

Before deletion, the interface counts records that reference the selected truck, driver, job,
brand, garage, route, cargo, or customer. It shows the affected table counts and disables delete
while references exist. This preview can become stale if another user changes the database;
foreign-key constraints remain the final safeguard. Successful edits show the record ID and
changed fields; creates and deletes show the affected record type and ID where available.

## Database failures

`utils/db_errors.py` maps common MySQL failures to concise guidance. Connection failures are
shown as database-unavailable messages; other query failures are shown as query errors.
Detailed exceptions are written to `logs/app.log` for local diagnosis. The UI does not show
raw driver text, which can include SQL, hostnames, or account names. Passwords are excluded
from settings representations and masked in connection strings.

Unique-key and foreign-key errors have specific guidance. The database enforces remaining
schema rules and relationships; users should refresh records and check linked entries when a
write is rejected.

## Image uploads

Uploads are limited to 10 MB and supported formats. The image service validates the entity,
ID, visual option, file signature, and that the file can be verified as a real PNG or JPEG before saving into the local asset folders. Invalid
files and filesystem failures are caught at the UI boundary and shown as actionable errors.

## Automated checks

Run `python -m pytest` from the project root. The unit tests exercise validation rules,
configuration safety, error translation, repository SQL parameterization, status rules, image
lookup/upload/replacement/rejection, and schema comparison. Create, update, and delete SQL is
checked for every supported entity table. Tests use fakes and temporary directories; they do
not require the production database or local environment file. Repository behavior is also
exercised against a temporary SQLite database, while Streamlit AppTest checks the delete warning,
confirmation requirement, and disabled action when linked records exist.
