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
ID, visual option, and file signature before saving into the local asset folders. Invalid
files and filesystem failures are caught at the UI boundary and shown as actionable errors.

## Automated checks

Run `python -m pytest` from the project root. The unit tests exercise validation rules,
configuration safety, error translation, repository SQL parameterization, status rules, image
uploads, and schema comparison. Tests use fakes and temporary directories; they do not require
the production database or local environment file.
