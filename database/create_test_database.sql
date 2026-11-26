-- Separate test database for the MySQL integration test (tests/test_mysql_integration.py).
-- Run once as a MySQL administrator. It copies only the table STRUCTURE of the real
-- omnilogistics tables; no records are copied and the real database is not changed.

CREATE DATABASE IF NOT EXISTS omnilogistics_test;

CREATE TABLE IF NOT EXISTS omnilogistics_test.brands    LIKE omnilogistics.brands;
CREATE TABLE IF NOT EXISTS omnilogistics_test.customers LIKE omnilogistics.customers;
CREATE TABLE IF NOT EXISTS omnilogistics_test.garages   LIKE omnilogistics.garages;
CREATE TABLE IF NOT EXISTS omnilogistics_test.drivers   LIKE omnilogistics.drivers;
CREATE TABLE IF NOT EXISTS omnilogistics_test.routes    LIKE omnilogistics.routes;
CREATE TABLE IF NOT EXISTS omnilogistics_test.cargos    LIKE omnilogistics.cargos;
CREATE TABLE IF NOT EXISTS omnilogistics_test.trucks    LIKE omnilogistics.trucks;
CREATE TABLE IF NOT EXISTS omnilogistics_test.jobs      LIKE omnilogistics.jobs;
