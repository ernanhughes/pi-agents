# Postgres extension (pg_query) documentation

This is a project-local development aid in the [PI Agents book development
repository](../../README.md). The pinned chapter examples and evidence live in
`examples/`; this guide describes a local implementation pattern.

Overview
- This extension provides a read-only Postgres query tool named pg_query for the Pi agent. It connects to a PostgreSQL database using the DATABASE_URL environment variable (or a sensible default) and executes read-only SQL statements.

Prerequisites
- Node.js dependencies include the pg package (see package.json).
- Ensure a PostgreSQL instance is accessible and the connection URL is provided via DATABASE_URL. Default URL used by the tool is postgresql://pi:pi@localhost:5432/pi.
- The database must allow read queries (SELECT, WITH, SHOW, EXPLAIN).
- Pi must be reloaded after configuring the environment or the database connection.

Setup
- Start or expose your PostgreSQL instance. Example docker:
  docker run --name pi-pg -e POSTGRES_USER=pi -e POSTGRES_PASSWORD=pi -e POSTGRES_DB=pi -p 5432:5432 -d postgres:16
- Set DATABASE_URL to your connection string, e.g. export DATABASE_URL="postgresql://pi:pi@localhost:5432/pi".
- In Pi, run /reload to load the new tool.

Usage
- Tool name: pg_query
- Primary purpose: Run a read-only SQL query against the configured PostgreSQL database.
- Parameters:
  - sql: SQL statement to run (string).
  - params: Optional array of string parameters for prepared statements.
  - maxRows: Optional max rows to return (default 50, max 200).
- Safety: Only SELECT, WITH, SHOW, EXPLAIN are permitted. Non-read-only statements are blocked with a helpful message.

Examples
- List user tables
  - SQL: SELECT table_schema, table_name
           FROM information_schema.tables
           WHERE table_type = 'BASE TABLE'
             AND table_schema NOT IN ('pg_catalog', 'information_schema')
           LIMIT 5;
  - Output (example):
    2 row(s)
    [
      {
        "table_schema": "public",
        "table_name": "users"
      },
      {
        "table_schema": "public",
        "table_name": "orders"
      }
    ]
- Show database version
  - SQL: SELECT version();
  - Output (example):
    1 row(s)
    [
      "PostgreSQL 15.3 on x86_64-..."
    ]
- Quick row count for tables
  - SQL: SELECT table_schema, COUNT(*) AS n FROM information_schema.tables WHERE table_type='BASE TABLE' GROUP BY table_schema;
  - Output (example):
    1 row(s)
    [
      {
        "table_schema": "public",
        "n": 42
      }
    ]
- Using parameters (prepared statements)
  - SQL: SELECT table_name FROM information_schema.tables WHERE table_schema = $1 LIMIT $2;
  - Params: ["public", "5"]
  - Output (example):
    1 row(s)
    [
      {"table_name": "users"}
    ]

Output
- The tool returns up to maxRows rows in JSON format, with a small textual summary. If the result set is larger than maxRows, the output will indicate truncation.

Notes
- If you need write access or DDL, consider implementing a separate write tool with appropriate authorization.
- Ensure your environment variable DATABASE_URL is kept secret in your deployment environment.
