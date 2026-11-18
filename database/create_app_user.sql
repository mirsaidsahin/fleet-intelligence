-- OPTIONAL. Run once as a MySQL administrator to give the app a restricted account.
-- It cannot create, alter or drop tables, so the existing database stays intact.
-- Replace the placeholder password and never commit the real one.

CREATE USER IF NOT EXISTS 'fleet_app'@'localhost' IDENTIFIED BY '<choose-a-strong-password>';

-- The app reads and edits existing rows, but never changes the schema.
GRANT SELECT, INSERT, UPDATE, DELETE ON omnilogistics.* TO 'fleet_app'@'localhost';
