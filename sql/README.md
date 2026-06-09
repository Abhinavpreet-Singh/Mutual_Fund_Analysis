# 🗄️ SQL Scripts Directory

This directory contains the SQL scripts defining the schema and the analytical database queries.

## 📄 File Details

- **`schema.sql`**: SQL DDL script defining the schema for the Star Schema relational data model (create table statements, data types, and primary/foreign key constraints).
- **`queries.sql`**: Compilation of the 10 analytical queries designed to run against the schema (e.g. fund rankings, category trends, geographical distributions).

## ⚙️ Execution
The schemas and queries are run automatically as part of the ETL database construction step:
```bash
python scripts/etl_pipeline.py
```
This script parses `queries.sql`, translates SQL Server dialects to SQLite compatibility, and writes a detailed markdown report of query results to `reports/day2_query_results.md`.
